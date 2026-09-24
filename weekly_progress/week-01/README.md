# Week 1 — Docker to Kind

Goal: containerize the ticket booking platform, then run the **whole stack** — five components plus
Postgres, Redis, and RabbitMQ — live on a local Kubernetes cluster (Kind), using Dockerfiles and
manifests **you write yourself**. No `kubectl create deployment`, no Helm charts, no copy-pasting a
manifest you can't explain. By the end the app is reachable from your machine, a booking goes all
the way from `PENDING_PAYMENT` to `CONFIRMED`, and you can explain every field in every file you
wrote.

This is a big week. Sections 1–7 are the core; section 9 is a stretch goal.

## 1. Understand the app

- [ ] Read the root [`README.md`](../../README.md): architecture diagram, components table, "The
      interesting parts", event catalog, and the booking request flow
- [ ] Skim each service's code under `services/*/app/`, following the request flow:
  - [ ] `auth-service` — `routers/auth.py`, `security.py` (what's inside the JWT?)
  - [ ] `event-service` — `crud.py → hold_seats` (why `FOR UPDATE`, why sorted?), `cache.py`,
        `events.py`
  - [ ] `booking-service` — `routers/bookings.py`, `clients.py`, `crud.py → finalize`,
        `jobs/expire_bookings.py`
  - [ ] `payment-worker` and `notification-worker` — `main.py`, `messaging.py`
- [ ] For each component, write down: what it listens on (if anything), which env vars it needs,
      and what it connects to. You'll need this list for every manifest you write this week
- [ ] Be able to explain, without looking: why does `booking-service` need `JWT_SECRET`, and what
      happens if it doesn't match `auth-service`'s?

## 2. Write a Dockerfile for each service

- [ ] Write a `Dockerfile` in each of the five `services/*/` folders. Aim for:
  - a slim Python base image with a pinned version (not `python:latest`)
  - `requirements.txt` copied and installed **before** the app code, so code changes don't
    re-install dependencies (be able to explain layer caching)
  - the container runs as a **non-root** user
  - no `.env` file baked into the image — config comes from env vars at runtime
  - the right `CMD` for each: `uvicorn` for the three HTTP services, `python -m app.main` for the
    workers
- [ ] Add a `.dockerignore` per service (`.venv`, `__pycache__`, `.env`, …)
- [ ] Build all five with a real tag like `v1` — not `latest`. You'll see why in section 5:
  ```bash
  docker build -t auth-service:v1 ./services/auth-service
  # ...and the other four
  ```
- [ ] Smoke-test them with plain Docker before Kubernetes is involved: put Postgres, Redis,
      RabbitMQ, and your five containers on one user-defined Docker network
      (`docker network create tickets`) and run the "Try it end to end" flow from the root README
- [ ] Explain why containers on the same user-defined network can reach each other by name, and
      why `localhost` inside a container doesn't mean your laptop
- [ ] Notice: the `expire-bookings` job doesn't need its own image. Run it with the
      `booking-service` image and a different command:
  ```bash
  docker run --rm --network tickets -e DATABASE_URL=... -e RABBITMQ_URL=... booking-service:v1 \
    python -m app.jobs.expire_bookings
  ```

Don't write a `docker-compose.yml` this week — go straight from `docker run` to Kubernetes.

## 3. Kind setup & cluster basics

- [ ] Install `kind` and `kubectl`
- [ ] Read how Kind works: each Kubernetes "node" is actually a Docker container on your machine.
      Keep that in mind — it explains most of the surprises this week
- [ ] Write your own Kind cluster config at `k8s/kind-config.yaml`. Start with a single
      control-plane node. You'll come back to it in section 7 to add port mappings
- [ ] Create the cluster from your config:
  ```bash
  kind create cluster --name tickets --config k8s/kind-config.yaml
  ```
- [ ] Explore it and be able to explain what each command tells you:
  - [ ] `kubectl cluster-info`
  - [ ] `kubectl get nodes -o wide`
  - [ ] `kubectl get pods -A` — what are all these pods in `kube-system`, and what does each one do?
  - [ ] `docker ps` — find the container that *is* your Kind node
- [ ] Understand your kubeconfig: where it lives, what a "context" is, and how `kubectl` knows
      which cluster to talk to (`kubectl config get-contexts`)
- [ ] Create a `tickets` namespace and deploy everything into it, not `default`

Organize `k8s/` however makes sense to you (e.g. `k8s/infra/` and `k8s/apps/`), but be ready to
explain the choice.

## 4. Infrastructure: Postgres, Redis, RabbitMQ (with persistent storage)

The app needs three backing services inside the cluster. Write the manifests yourself — no Helm
charts, no operators.

- [ ] **Postgres** — a Deployment (or StatefulSet — be able to explain which you picked and why)
      plus a ClusterIP Service
  - [ ] The app needs three databases (`users_db`, `events_db`, `bookings_db`), but the Postgres
        image only creates one on first start. Solve it with an init SQL script stored in a
        **ConfigMap** and mounted into `/docker-entrypoint-initdb.d/`
  - [ ] The Postgres password comes from a **Secret**, not a plain value in the manifest
- [ ] **Persistent storage (PVC)** for Postgres:
  - [ ] Look at the StorageClass Kind gives you out of the box (`kubectl get storageclass`)
  - [ ] Write a PersistentVolumeClaim and mount it at Postgres's data directory
  - [ ] Prove it works: create a user and an event, delete the Postgres pod, let it come back, and
        show the data is still there
  - [ ] Explain the difference between a PersistentVolume, a PersistentVolumeClaim, and a
        StorageClass, and what `accessModes` means
  - [ ] Explain why the init script from the ConfigMap does **not** run again when the pod restarts
        with an existing volume (and what that means if you change the script later)
  - [ ] Note what happens to your data if you `kind delete cluster`, and why that's fine locally but
        not in production
- [ ] **Redis** — a Deployment + ClusterIP Service. Does it need a PVC? Explain your answer (hint:
      what is it used for in this app?)
- [ ] **RabbitMQ** — a Deployment + ClusterIP Service exposing the AMQP port (5672) and the
      management UI port (15672)

## 5. Config, Secrets, and the app Deployments

- [ ] Put non-secret config (service URLs, `CACHE_TTL_SECONDS`, `HOLD_TIMEOUT_MINUTES`,
      `PAYMENT_FAILURE_RATE`, …) in **ConfigMaps**
- [ ] Put `JWT_SECRET` and the database credentials in **Secrets**. `JWT_SECRET` must be the same
      in `auth-service` and `booking-service`, so both should read it from the same Secret
- [ ] Understand that a Secret is only base64-encoded, not encrypted — be able to decode one with
      `kubectl get secret ... -o jsonpath=... | base64 -d`. Don't commit real secrets
- [ ] Get your images into the cluster. Kind can't see images from your local Docker by default:
  ```bash
  kind load docker-image auth-service:v1 --name tickets
  # ...and the other four
  ```
  Explain **why** that step is needed, and why using the `latest` tag here tends to cause
  `ErrImagePull` (hint: the default `imagePullPolicy` for `latest`)
- [ ] Write a Deployment for each of the five components. Each should include:
  - labels + a `selector` that matches them
  - the container `image`, `ports` (HTTP services only), and an `imagePullPolicy` you chose on purpose
  - env vars wired from your ConfigMaps and Secrets (`envFrom` or `valueFrom` — know the difference)
  - resource `requests` and `limits`
  - for the three HTTP services: a `readinessProbe` and a `livenessProbe` on `/health`
  - for the two workers: no HTTP probes. Explain why you can't use one, and what you lose by not
    having a probe
- [ ] Run `event-service` with **2 replicas**. Explain why that's safe here (think: where does state
      live? what does Redis cache invalidation look like with 2 pods?)
- [ ] Watch everything come up: `kubectl get pods -n tickets -w`
- [ ] Delete one pod by hand and watch the Deployment replace it. Explain what brought it back
      (Deployment → ReplicaSet → Pod)
- [ ] **Startup order:** Kubernetes starts everything at once. The HTTP services create their tables
      at import time, so if Postgres isn't ready yet they crash. Watch this happen, then explain why
      the pod eventually recovers on its own (restartPolicy + backoff), and what an `initContainer`
      that waits for Postgres would change
- [ ] Make a small visible change to one service (e.g. the `/health` response), build `v2`, load it,
      and do a rolling update. Watch it with `kubectl rollout status`, then practice
      `kubectl rollout undo`

## 6. Services — wiring it together

- [ ] Write a **ClusterIP** Service for each HTTP service
  - [ ] Confirm each one has endpoints (`kubectl get endpointslices -n tickets`)
  - [ ] `booking-service` reaches `event-service` through its Service DNS name — make sure
        `EVENT_SERVICE_URL` in your ConfigMap uses it
  - [ ] From a throwaway pod, hit each service by its DNS name:
    ```bash
    kubectl run tmp -n tickets --rm -it --image=curlimages/curl -- sh
    # then: curl http://event-service.tickets.svc.cluster.local:<port>/health
    ```
  - [ ] Explain what the full DNS name means, and why the short name `event-service` also works
        from inside the same namespace
- [ ] Explain why the two workers don't need a Service at all
- [ ] Reach each HTTP service from your machine with `kubectl port-forward`

## 7. Reaching it from your browser — NodePort

- [ ] Expose `auth-service`, `event-service`, and `booking-service` as **NodePort** Services with
      fixed `nodePort`s
  - [ ] Try to hit them on `localhost:<nodePort>` — it won't work on Mac/Windows yet. Explain why
        (remember: the "node" is a Docker container)
  - [ ] Fix it by adding `extraPortMappings` to `k8s/kind-config.yaml` and recreating the cluster
  - [ ] Confirm the three APIs are reachable (e.g. each service's `/docs` page) with no
        `port-forward` running
- [ ] Be able to explain `port` vs `targetPort` vs `nodePort` vs `containerPort`, and draw the path a
      request takes from your browser to a pod
- [ ] Discussion point for review: exposing `event-service` also exposes `/internal/events/...`,
      which only `booking-service` is meant to call. Why is that a problem, and what are some ways
      you could fix it? (You don't have to fix it this week — just think it through)
- [ ] **The real test:** run the full "Try it end to end" flow from the root README against your
      Kind cluster — register, log in, create an event, book seats, and watch the booking reach
      `CONFIRMED` (or `CANCELLED`). Check `notification-worker`'s logs for the "email"

## 8. Debugging pods (describe, logs, exec)

Break things on purpose so you recognize the symptoms when they happen for real. For each one:
break it, find the cause **using only kubectl**, fix it, and write a few lines in
`submissions/week-01/debugging.md` about what you saw and which command gave it away.

Generic Kubernetes failures:

- [ ] **Bad image tag** — point a Deployment at a tag that doesn't exist → `ImagePullBackOff`
- [ ] **Wrong selector** — make a Service selector not match its pods' labels → Service with no
      endpoints
- [ ] **Wrong port** — set a Service's `targetPort` to a port the app doesn't listen on
- [ ] **Impossible resources** — request more CPU/memory than your node has → pod stuck `Pending`
- [ ] **Failing probe** — point a readiness probe at a path that returns 404 → pod `Running` but
      never `Ready`

Failures specific to this app:

- [ ] **Mismatched `JWT_SECRET`** — give `booking-service` a different secret from `auth-service`.
      Every pod is healthy, yet every booking fails. What status code do you get, and how would
      you track down the cause?
- [ ] **Broken service URL** — set `EVENT_SERVICE_URL` to a wrong hostname → bookings return `503`.
      Use `kubectl exec` into the `booking-service` pod to prove it can't resolve the name
- [ ] **Payments stop** — scale `payment-worker` to 0. Bookings stay `PENDING_PAYMENT` and their
      seats stay `HELD`. Run the expire-bookings job by hand to clear them (you'll need a one-off
      pod or Job using the `booking-service` image)
- [ ] **Scale the workers** — scale `payment-worker` to 3 and make several bookings. Use the logs
      (`kubectl logs -l <label> --prefix`) to show RabbitMQ spreading messages across the replicas

Commands you should be comfortable with by the end:

- [ ] `kubectl describe pod <pod>` — read the **Events** section at the bottom
- [ ] `kubectl logs <pod>`, `kubectl logs <pod> --previous`, `kubectl logs -f deploy/<name>`
- [ ] `kubectl exec -it <pod> -- sh` — look around inside the container (env vars, files, can it
      reach the other Services?)
- [ ] `kubectl get events -n tickets --sort-by=.lastTimestamp`
- [ ] `kubectl get pod <pod> -o yaml` — the full object, including what Kubernetes filled in for you

## 9. Stretch: expire bookings with a CronJob

- [ ] Write a **CronJob** that runs `python -m app.jobs.expire_bookings` with the `booking-service`
      image every 2 minutes
- [ ] Prove it works: scale `payment-worker` to 0, make a booking, wait, and watch the CronJob
      expire it and release the seat — no manual steps
- [ ] Explain `concurrencyPolicy`, `successfulJobsHistoryLimit`, and what happens if one run is
      still going when the next is due

## 10. Explain every field — the deliverable

This is what I'll actually test you on. Write `submissions/week-01/manifests-explained.md`
covering **every field** in every file under `k8s/` — `apiVersion`, `kind`, `metadata`, and
everything in `spec` down to the last line — plus every instruction in your Dockerfiles. For
each: what it does, and what would happen if you removed it or got it wrong.

To keep it manageable: explain each *kind* of object in full once (one Deployment, one Service,
the PVC, a ConfigMap, a Secret, …), then just note what's different about the others.

- [ ] Dockerfiles explained
- [ ] `kind-config.yaml` explained
- [ ] Postgres, Redis, RabbitMQ manifests explained (including the PVC and the init ConfigMap)
- [ ] App Deployments, Services, ConfigMaps, and Secrets explained
- [ ] CronJob explained (if you did the stretch)
- [ ] Be ready to answer "why this value and not another?" for anything you set — replicas,
      resource numbers, probe timings, Service types

Expect me to point at a random line during review and ask about it.

## 11. Submission — opening your PR

When you're done with this week, open a PR against this repo's `main` branch. I'll review it the
same way I'd review any real PR — treat it that way.

- [ ] Work on a branch named `week-01` (not directly on `main`)
- [ ] PR title: `Week 1 — Docker to Kind`
- [ ] PR description includes:
  - A short summary of what you did and what you learned
  - Which checklist items above you completed vs. skipped, and why if skipped
  - Anything that broke, confused you, or you'd do differently
- [ ] The PR diff includes:
  - Your Dockerfiles and `.dockerignore`s under `services/*/`
  - Your manifests under `k8s/`
  - Your evidence and write-ups under `submissions/week-01/` (see that folder's README)
- [ ] Evidence the app is live — `kubectl get all -n tickets` and `kubectl get pvc -n tickets`
      output, plus the end-to-end booking flow (the `curl` output or screenshots) hitting the
      NodePorts, pasted into the PR description or added under `submissions/week-01/`
- [ ] Anyone should be able to reproduce your setup from the repo: add a short "Run it on Kind"
      section to the root `README.md` with the exact commands, from `kind create cluster` to a
      confirmed booking
- [ ] No real secrets committed — if a Secret manifest is in the repo, it only holds throwaway
      local values, and the README says so
- [ ] Keep the PR scoped to week 1 — don't bundle in unrelated changes
- [ ] Commit history makes sense on its own (squash noisy WIP commits if needed)

I'll leave feedback as comments directly on the PR. Don't merge it yourself — leave it open until
I approve.

## Notes / blockers

_(fill in as you go — what broke, what you learned, what you'd do differently)_
