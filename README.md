# Ticket Booking Platform

A small but realistic event-driven microservices app used as the running example for the DevOps
mentorship. This repo currently holds **only the application code** — no Dockerfiles, no
Kubernetes manifests, no CI/CD. You add all of those yourself, starting in week 1.

The domain is concert/event ticketing: users browse events, pick seats, pay, and get their tickets
by email. It looks simple from the outside, but ticketing has a few genuinely hard problems baked
in that make for good DevOps material — two people clicking the same seat at the same moment,
payments that fail or never come back, and seats that have to be released if nobody pays for them.

## Architecture

Five components: three HTTP services, each with its own Postgres database, plus two background
workers. Synchronous calls happen only where the caller truly can't continue without an answer
(holding seats); everything else flows through RabbitMQ.

```
                              ┌───────────────┐
                              │    Client     │
                              └───────┬───────┘
          register/login              │ browse events          book seats (Bearer JWT)
        ┌─────────────────────────────┼──────────────────────────────┐
        ▼                             ▼                              ▼
┌────────────────┐          ┌──────────────────┐   REST: hold  ┌──────────────────┐
│  auth-service   │          │  event-service    │◀──── seats ───│ booking-service   │
│     :8001       │          │     :8002         │               │     :8003         │
│  (Postgres)     │          │ (Postgres+Redis)  │               │   (Postgres)      │
└────────────────┘          └─────────▲─────────┘               └───┬──────────▲────┘
   issues JWTs,                        │                              │          │
   booking-service                     │ booking.confirmed /          │ booking. │ payment.succeeded /
   verifies them with                  │ booking.cancelled            │ created  │ payment.failed
   the same shared secret              │                              ▼          │
                              ┌────────┴──────────────────────────────────────────┴───┐
                              │                  tickets_exchange                      │
                              │                 (RabbitMQ, topic)                      │
                              └────────┬───────────────────────────────▲──────────────┘
                     booking.confirmed │                               │
                     booking.cancelled ▼                               │ booking.created
                          ┌──────────────────────┐          ┌─────────┴──────────┐
                          │ notification-worker   │          │   payment-worker    │
                          │ (simulated emails)    │          │ (fake card charge)  │
                          └──────────────────────┘          └────────────────────┘

             ┌──────────────────────────────────────────────────────────────┐
             │ expire-bookings job (booking-service image, runs on a       │
             │ schedule): expires unpaid bookings → publishes              │
             │ booking.cancelled so their seats go back on sale             │
             └──────────────────────────────────────────────────────────────┘
```

### Components

| Component             | Tech                   | Port | Database / deps          | Responsibility |
|-----------------------|------------------------|------|--------------------------|----------------|
| `auth-service`        | FastAPI                | 8001 | `users_db`               | Register/login, issues JWTs (carrying user id + email) |
| `event-service`       | FastAPI + Redis        | 8002 | `events_db`, Redis       | Event catalog and seat maps; holds seats atomically; sells/releases seats on booking events |
| `booking-service`     | FastAPI                | 8003 | `bookings_db`            | Creates bookings, verifies JWTs locally, drives the booking lifecycle from payment events |
| `payment-worker`      | Plain Python (no HTTP) | —    | —                        | Consumes `booking.created`, simulates charging a card |
| `notification-worker` | Plain Python (no HTTP) | —    | —                        | Consumes `booking.confirmed` / `booking.cancelled`, simulates emailing the customer |
| `expire-bookings` job | booking-service image  | —    | `bookings_db`            | One-shot: `python -m app.jobs.expire_bookings`. Expires bookings stuck in `PENDING_PAYMENT` |

Each HTTP service owns its own Postgres database — no service reaches into another's tables.

### The interesting parts

**Two people, one seat.** Holding seats is the one synchronous call in the system:
`booking-service` asks `event-service` to hold them *before* the booking exists, and the client
gets a `409` straight away if someone beat them to it. `event-service` locks the seat rows
(`SELECT ... FOR UPDATE`, in a fixed order to avoid deadlocks) so that of N simultaneous requests
for the same seat, exactly one wins. See `event-service/app/crud.py → hold_seats`.

**No shared user database.** `booking-service` never calls `auth-service`. It verifies the JWT
itself using the same `JWT_SECRET`. That's fast and removes a runtime dependency, but it means the
secret has to be identical in both services — a nice reason to learn how Kubernetes Secrets are
shared between Deployments.

**Payments that never come back.** If `payment-worker` is down or slow, bookings would sit in
`PENDING_PAYMENT` forever and their seats would never go back on sale. The `expire-bookings` job is
the safety net: it expires bookings older than `HOLD_TIMEOUT_MINUTES` and publishes
`booking.cancelled`, which makes `event-service` release the seats. It's not a web server — it
runs once and exits — so something has to schedule it (a Kubernetes CronJob is the natural fit).

**Races between the job and payments.** The expiry job and the payment consumer can both try to
finalize the same booking. `booking-service` locks the booking row and only ever transitions out of
`PENDING_PAYMENT` once, so whichever arrives first wins. A payment that lands after expiry is logged
as "would refund" instead of resurrecting the booking. See `booking-service/app/crud.py → finalize`.

**A hot read path.** The seat map (`GET /events/{id}/seats`) is what everyone refreshes when an
event goes on sale, so it's cached in Redis with a short TTL and invalidated whenever seats change.

### Event catalog (`tickets_exchange`, topic exchange)

| Routing key          | Published by                         | Consumed by                        | Payload |
|----------------------|--------------------------------------|------------------------------------|---------|
| `booking.created`    | booking-service                      | payment-worker                     | `{booking_id, user_id, amount}` |
| `payment.succeeded`  | payment-worker                       | booking-service                    | `{booking_id, amount}` |
| `payment.failed`     | payment-worker                       | booking-service                    | `{booking_id, reason}` |
| `booking.confirmed`  | booking-service                      | event-service, notification-worker | `{booking_id, event_id, user_email, seat_labels, total_amount}` |
| `booking.cancelled`  | booking-service, expire-bookings job | event-service, notification-worker | `{booking_id, event_id, user_email, reason}` |

### Lifecycles

- **Seat:** `AVAILABLE` → `HELD` (booking created) → `SOLD` (booking confirmed), or back to
  `AVAILABLE` (booking cancelled or expired)
- **Booking:** `PENDING_PAYMENT` → `CONFIRMED` | `CANCELLED` (payment failed) | `EXPIRED` (not paid
  in time)

### Request flow: booking seats

1. Client registers and logs in on `auth-service`, getting a JWT.
2. Client browses events and the seat map on `event-service`.
3. Client calls `POST /bookings` on `booking-service` with the JWT, an `event_id`, and seat labels.
4. `booking-service` verifies the JWT, then calls `event-service`'s internal hold endpoint. Seats go
   `HELD`, or the client gets `409` (taken) / `422` (no such seat).
5. `booking-service` saves the booking as `PENDING_PAYMENT` and publishes `booking.created`.
6. `payment-worker` "charges the card" and publishes `payment.succeeded` or `payment.failed`.
7. `booking-service` moves the booking to `CONFIRMED` or `CANCELLED` and publishes
   `booking.confirmed` or `booking.cancelled`.
8. `event-service` marks the seats `SOLD` or releases them; `notification-worker` "emails" the
   customer either way.
9. Client polls `GET /bookings/{id}` to see the final status.

## Running locally (without containers)

Each component is configured entirely through environment variables — see each service's
`.env.example`. You need Postgres, Redis, and RabbitMQ reachable at those URLs. Quickest way to get
them without installing anything:

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
docker run -d --name redis -p 6379:6379 redis:7
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

docker exec -it pg psql -U postgres -c "CREATE DATABASE users_db;"
docker exec -it pg psql -U postgres -c "CREATE DATABASE events_db;"
docker exec -it pg psql -U postgres -c "CREATE DATABASE bookings_db;"
```

Then for each HTTP service (ports 8001–8003):

```bash
cd services/auth-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

The workers have no HTTP server — they just run:

```bash
cd services/payment-worker   # same for notification-worker
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

And the expiry job runs once and exits (from `services/booking-service`, with its venv active):

```bash
python -m app.jobs.expire_bookings
```

Tables are created automatically on startup (`Base.metadata.create_all`) — no migrations yet.

### Try it end to end

```bash
# register + log in
curl -X POST localhost:8001/auth/register -H 'content-type: application/json' \
  -d '{"email":"ammar@example.com","password":"secret","full_name":"Ammar"}'
TOKEN=$(curl -s -X POST localhost:8001/auth/login -H 'content-type: application/json' \
  -d '{"email":"ammar@example.com","password":"secret"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# create an event with 3 rows x 10 seats (A1..C10)
curl -X POST localhost:8002/events -H 'content-type: application/json' \
  -d '{"name":"Cairokee Live","venue":"Cairo Stadium","starts_at":"2026-12-01T20:00:00","seat_price":"350.00","rows":3,"seats_per_row":10}'

# look at the seat map
curl localhost:8002/events/<event-id>/seats

# book two seats
curl -X POST localhost:8003/bookings -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"event_id":"<event-id>","seat_labels":["A1","A2"]}'

# poll until CONFIRMED / CANCELLED (payment-worker fails ~20% of payments on purpose)
curl localhost:8003/bookings/<booking-id> -H "Authorization: Bearer $TOKEN"
```

Try booking the same seat twice to see the `409`, stop `payment-worker` and run the expiry job to
watch a booking expire, and watch messages flow in the RabbitMQ UI at `http://localhost:15672`
(`guest` / `guest`).

## Plan overview

| Week | Focus |
|------|-------|
| 1 | Containerize the app and deploy the whole stack live on a local Kind cluster, writing your own manifests |
| 2 | Build a GitHub Actions CI/CD pipeline for that same app |
| 3 | Write Terraform from scratch — AWS VPC/networking + compute target |
| 4 | Capstone: move the same stack to AWS via your own Terraform |
| 5 | Add an observability layer; polish and write up the project |
| 6 | LinkedIn, GitHub, and CV review; mock interviews |

See [`weekly_progress/`](weekly_progress/) for the week-by-week checklists — start with
[`weekly_progress/week-01/README.md`](weekly_progress/week-01/README.md).

## Working with the AI mentor (Claude Code)

The repo ships a Claude Code mentor agent that coaches you through the plan without doing the
graded work for you. Open Claude Code in the repo root and use:

| Command | What it does |
|---------|--------------|
| `/next-step` | Works out where you are in the current week's checklist and gives you the next small task, with a "done when…" check |
| `/review-my-work [path]` | Reviews your Dockerfiles/manifests/write-ups the way the PR reviewer will — findings and hints, not rewritten files |
| `/quiz [file or topic]` | One-question-at-a-time "explain this line" drill on your own files, to prepare for review |

Or just ask for the `devops-mentor` agent ("use devops-mentor to help me debug this
CrashLoopBackOff"). It climbs a hint ladder — concept → pointers → skeleton → worked example — and
only shows full answers when you explicitly ask. Definitions live in `.claude/agents/` and
`.claude/skills/`; repo rules for Claude are in `CLAUDE.md`.

## Repo layout

```
.
├── services/          # The application — one folder per component
├── k8s/               # Kubernetes manifests you write yourself (week 1 onwards)
├── weekly_progress/   # One checklist per week — check items off as you go
└── submissions/       # Per-week evidence: command output, screenshots, write-ups
```

Later weeks add folders like `.github/workflows/` (week 2) and `terraform/` (weeks 3–4). Create
those as you go.
