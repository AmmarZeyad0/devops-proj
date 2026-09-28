# CLAUDE.md

This repo is a DevOps mentorship project. The application under `services/` (five Python
components: auth-, event-, booking-service, payment- and notification-worker) is given; **Ammar
builds everything DevOps around it themselves**, week by week — Dockerfiles, Kind/Kubernetes
manifests, GitHub Actions, Terraform, AWS, observability. A human mentor reviews each week's PR
line by line.

## Where things are

- `README.md` — architecture, components, ports (8001–8003), event catalog, week plan
- `weekly_progress/week-XX/README.md` — the checklist for each week (source of truth for scope)
- `submissions/week-XX/` — evidence and write-ups for that week
- `services/*/.env.example`, `services/*/app/config.py` — every env var each component reads
- `k8s/`, later `.github/workflows/` and `terraform/` — Ammar's own work

## Rules for Claude in this repo

- This is a learning project. **Don't write the graded deliverables** (Dockerfiles,
  `.dockerignore`s, `k8s/**`, `.github/workflows/**`, `terraform/**`, `submissions/**` write-ups)
  unless Ammar explicitly asks for the finished file — prefer hints, skeletons with blanks, and
  review. The week-1 checklist forbids copy-pasting anything they can't explain.
- For mentoring, use the `devops-mentor` agent, or the commands `/next-step`,
  `/review-my-work`, `/quiz`.
- Don't modify application code under `services/*/app/` unless a checklist item calls for it
  (e.g. the week-1 `/health` change for a rolling update).
- Never commit real secrets; Secret manifests hold throwaway local values only.
