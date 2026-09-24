# Ammar Zeyad — DevOps Mentorship Project

Unlike a typical starter repo, this one doesn't ship with a pre-built application. You bring a
Docker app you already have, and over six weeks we take that **same app** all the way from a local
container to a production-style deployment on AWS: Kubernetes first, then CI/CD, then your own
Terraform infrastructure, then observability.

Keeping one app through the whole track is on purpose. By week 6 you'll have a single project
you can walk an interviewer through end to end: "here's the app, here's how it's deployed, here's
the pipeline that ships it, here's the infra it runs on, and here's how I know it's healthy."

## Plan overview

| Week | Focus |
|------|-------|
| 1 | Deploy a Docker app live on a local Kind cluster, writing your own manifests |
| 2 | Build a GitHub Actions CI/CD pipeline for that same app |
| 3 | Write Terraform from scratch — AWS VPC/networking + compute target |
| 4 | Capstone: move the same stack to AWS via your own Terraform |
| 5 | Add an observability layer; polish and write up the project |
| 6 | LinkedIn, GitHub, and CV review; mock interviews |

The week-by-week checklists live in [`weekly_progress/`](weekly_progress/). Start with
[`weekly_progress/week-01/README.md`](weekly_progress/week-01/README.md).

## Repo layout

```
.
├── app/               # Your application source + Dockerfile (you bring this in week 1)
├── k8s/               # Kubernetes manifests you write yourself (week 1 onwards)
├── weekly_progress/   # One checklist per week — check items off as you go
└── submissions/       # Per-week evidence: command output, screenshots, write-ups
```

Later weeks will add folders like `.github/workflows/` (week 2) and `terraform/` (weeks 3–4).
You'll create those as you go; don't add them ahead of time.

## The app

_(Fill this in during week 1: what the app does, what language/framework it uses, what port it
listens on, and whether it depends on anything else like a database.)_
