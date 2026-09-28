---
name: quiz
description: Rapid-fire "explain this line" quiz on Ammar's own Dockerfiles and manifests (or a named topic), mimicking the mentor's review. Use to prepare for the weekly review or the "explain every field" deliverable.
---

Run an interactive quiz, acting as the `devops-mentor`. If the user passed a file or topic as an
argument, focus on that; otherwise pick from the files Ammar wrote this week (`services/*/Dockerfile`,
`k8s/**`, `.github/workflows/**`, `terraform/**`) — fall back to the current week's checklist
concepts if nothing is written yet.

Rules:

1. Ask **one question at a time**, then stop and wait for the answer. Don't reveal the answer in
   the same message.
2. Point at a real line (`k8s/apps/booking.yaml:23 — imagePullPolicy: IfNotPresent`) and ask
   what it does, why that value, and what breaks if it's removed or wrong. Mix in scenario
   questions from the app ("booking returns 401 but every pod is Ready — where do you look?").
3. After each answer: say right / partly / wrong, give the precise explanation in 2–4 sentences,
   and cite the doc or `kubectl explain` path.
4. Do 5 questions unless told otherwise, getting harder as they go. End with a score and the
   2–3 topics to revisit, and offer to add them to the week's "Notes / blockers".
