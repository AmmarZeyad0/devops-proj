---
name: next-step
description: Figure out where Ammar is in the weekly DevOps plan and hand them the next small task. Use when they ask "what's next?", "where was I?", or want to start a work session.
---

Work out the next step in the mentorship plan and hand it over. Delegate to the `devops-mentor`
agent with this brief (include any text the user passed as arguments):

1. Find the current week: the highest `weekly_progress/week-XX/` with unchecked items, cross-checked
   with the current git branch and which files exist (`services/*/Dockerfile`, `k8s/`,
   `.github/workflows/`, `terraform/`).
2. Read that week's checklist and list, in 3–5 lines, what's done and what's left.
3. Pick the **next unchecked item** (respect section order unless a later item is blocking) and
   give Ammar:
   - why it matters for this app, in one or two sentences
   - one concrete, small task (≈15–45 min) with the exact commands where relevant
   - a "done when…" check they can verify themselves
   - one "why" question they should be able to answer afterwards
4. Do not write any deliverable files for them.

Relay the mentor's answer to the user as-is.
