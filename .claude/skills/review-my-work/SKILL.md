---
name: review-my-work
description: Mentor-style review of the Dockerfiles, manifests, workflows, Terraform, or write-ups Ammar wrote, before they open the week's PR. Pass a path to review just that, or nothing to review everything changed on the branch.
---

Delegate to the `devops-mentor` agent with this brief (include any path the user passed as
arguments):

1. Scope: the given path(s), or else everything changed vs. `main` (`git diff main...HEAD --stat`
   plus untracked files from `git status`).
2. Read the current week's checklist in `weekly_progress/week-XX/README.md` so the review checks
   its explicit requirements.
3. Review like the human mentor will, in this order:
   - **Will it work?** Ports, env var names, Service DNS names, image tags, selectors/labels,
     volume paths — checked against the actual code in `services/*/`.
   - **Checklist requirements** that are missing or only half-done.
   - **Security/hygiene:** real secrets committed, running as root, `latest` tags, `.env` baked in.
   - **Clarity:** anything they'd struggle to explain.
4. For each finding: `file:line`, what's wrong, why it matters, and a hint or question — **not**
   the corrected file. Group as "must fix" / "should fix" / "nice to have".
5. Finish with 3–5 questions the reviewer is likely to ask about these files.
6. Do not edit the files under review.

Relay the mentor's review to the user.
