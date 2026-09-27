# Week 1 submission

Put this week's evidence here:

- `manifests-explained.md` — every field in your manifests and every instruction in your
  Dockerfiles, explained in your own words (see section 10 of the checklist)
- `debugging.md` — your notes from the break-it-and-fix-it exercises (section 8)
- Output of `kubectl get all -n tickets` and `kubectl get pvc -n tickets` showing everything healthy
- Proof the app works end to end on Kind: the booking flow's `curl` output (or screenshots) through
  the NodePorts, ending in a `CONFIRMED` booking, plus the `notification-worker` log line
- Proof the Postgres data survived a pod deletion
- Anything else that backs up what you checked off in `weekly_progress/week-01/README.md`

Your Dockerfiles go in `services/*/` and your manifests in `k8s/`, not here.

See the "Submission" section of that checklist for what your PR should include.

