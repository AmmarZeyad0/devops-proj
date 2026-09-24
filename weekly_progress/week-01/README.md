# Week 1 — Docker to Kind

Goal: take a Docker app you already have and run it live on a local Kubernetes cluster (Kind),
using manifests **you write yourself** — no `kubectl create deployment`, no Helm charts, no
copy-pasting a manifest you can't explain. By the end the app is reachable from your machine and
you can explain every field in every manifest you wrote.

The app you pick here is the one we'll carry through the rest of the track (CI/CD in week 2, AWS
in week 4), so pick something you're happy to keep working on.

## 1. Bring your app into the repo

- [ ] Copy your app's source code and its `Dockerfile` into `app/`
- [ ] Fill in "The app" section of the root [`README.md`](../../README.md): what it does, the
      language/framework, the port it listens on, and whether it needs anything else (a database,
      a cache, a volume for files)
- [ ] Build it and run it with plain Docker first, to make sure the image itself works before
      Kubernetes is involved:
  ```bash
  docker build -t <app-name>:v1 ./app
  docker run --rm -p <host-port>:<container-port> <app-name>:v1
  ```
- [ ] Hit it with `curl` or a browser and confirm it responds

Use a real tag like `v1`, not `latest` — you'll see why in section 3.

## 2. Kind setup & cluster basics

- [ ] Install `kind` and `kubectl`
- [ ] Read how Kind works: each Kubernetes "node" is actually a Docker container on your machine.
      Keep that in mind — it explains most of the surprises this week
- [ ] Write your own Kind cluster config at `k8s/kind-config.yaml`. Start with a single
      control-plane node. You'll come back to it in section 4 to add port mappings
- [ ] Create the cluster from your config:
  ```bash
  kind create cluster --name ammar --config k8s/kind-config.yaml
  ```
- [ ] Explore it and be able to explain what each command tells you:
  - [ ] `kubectl cluster-info`
  - [ ] `kubectl get nodes -o wide`
  - [ ] `kubectl get pods -A` — what are all these pods in `kube-system`, and what does each one do?
  - [ ] `docker ps` — find the container that *is* your Kind node
- [ ] Understand your kubeconfig: where it lives, what a "context" is, and how `kubectl` knows
      which cluster to talk to (`kubectl config get-contexts`)
- [ ] Create a namespace for your app instead of using `default`

## 3. Writing a Deployment manifest

- [ ] Write `k8s/deployment.yaml` by hand. At minimum it should include:
  - `replicas` (start with 2)
  - labels + a `selector` that matches them
  - the container `image`, `ports`, and an `imagePullPolicy` you chose on purpose
  - resource `requests` and `limits`
  - a `readinessProbe` and a `livenessProbe` (if your app has no health endpoint, add one, or
    use a TCP probe and explain why)
  - any env vars your app needs (hard-coded values are fine this week; use a ConfigMap if you want
    a stretch goal)
- [ ] Get your image into the cluster. Kind can't see images on your local Docker by default:
  ```bash
  kind load docker-image <app-name>:v1 --name ammar
  ```
  Then explain **why** that step is needed, and why using the `latest` tag here tends to cause
  `ErrImagePull` (hint: the default `imagePullPolicy` for `latest`)
- [ ] `kubectl apply -f k8s/deployment.yaml` and watch the pods come up (`kubectl get pods -w`)
- [ ] Delete one pod by hand and watch the Deployment replace it. Explain what brought it back
      (Deployment → ReplicaSet → Pod)
- [ ] Change the image to `v2` (make a small visible change to the app, rebuild, load it) and do a
      rolling update. Watch it with `kubectl rollout status`, then practice `kubectl rollout undo`

## 4. Writing a Service manifest (ClusterIP / NodePort)

- [ ] Write `k8s/service.yaml` as a **ClusterIP** Service first
  - [ ] Confirm it has endpoints (`kubectl get endpoints` or `kubectl get endpointslices`)
  - [ ] Reach it from inside the cluster with a throwaway pod:
    ```bash
    kubectl run tmp --rm -it --image=curlimages/curl -- sh
    # then: curl http://<service-name>.<namespace>.svc.cluster.local:<port>
    ```
  - [ ] Reach it from your machine with `kubectl port-forward svc/<service-name> 8080:<port>`
- [ ] Switch it to **NodePort** (or add a second Service) and pick a fixed `nodePort`
  - [ ] Try to hit it on `localhost:<nodePort>` — it won't work on Mac/Windows yet. Explain why
        (remember: the "node" is a Docker container)
  - [ ] Fix it by adding `extraPortMappings` to `k8s/kind-config.yaml` and recreating the cluster
  - [ ] Confirm the app is reachable from your browser with no `port-forward` running
- [ ] Be able to explain the difference between `port`, `targetPort`, `nodePort`, and the
      container's `containerPort`, and draw the path a request takes from your browser to the pod

## 5. Persistent storage basics (PVC) — only if your app needs it

Skip this section if your app is stateless, and say so in your PR. If it writes anything that
should survive a restart (a database, uploaded files, a SQLite file):

- [ ] Look at the StorageClass Kind gives you out of the box (`kubectl get storageclass`)
- [ ] Write `k8s/pvc.yaml` requesting a small volume, and mount it into your Deployment at the
      path your app writes to
- [ ] Prove it works: write some data, delete the pod, let it come back, and show the data is still
      there
- [ ] Explain the difference between a PersistentVolume, a PersistentVolumeClaim, and a
      StorageClass, and what `accessModes` means
- [ ] Note what happens to your data if you `kind delete cluster` — and why that's fine locally but
      not in production

If your app needs a database, running Postgres/MySQL as its own Deployment + PVC + Service inside
the cluster is a good exercise. Ask before you reach for a Helm chart for it — write it yourself.

## 6. Debugging pods (describe, logs, exec)

Break things on purpose so you recognize the symptoms when they happen for real. For each one:
break it, find the cause **using only kubectl**, fix it, and write a few lines in
`submissions/week-01/debugging.md` about what you saw and which command gave it away.

- [ ] **Bad image tag** — point the Deployment at a tag that doesn't exist → `ImagePullBackOff`
- [ ] **App crashes on start** — e.g. remove a required env var or override `command` with
      something that exits → `CrashLoopBackOff`
- [ ] **Wrong selector** — make the Service selector not match the pod labels → Service with no
      endpoints, requests hang or get refused
- [ ] **Wrong port** — set the Service `targetPort` to a port the app doesn't listen on
- [ ] **Impossible resources** — request more CPU/memory than your node has → pod stuck `Pending`
- [ ] **Failing probe** — point the readiness probe at a path that returns 404 → pod `Running`
      but never `Ready`

Commands you should be comfortable with by the end:

- [ ] `kubectl describe pod <pod>` — read the **Events** section at the bottom
- [ ] `kubectl logs <pod>`, `kubectl logs <pod> --previous`, `kubectl logs -f deploy/<name>`
- [ ] `kubectl exec -it <pod> -- sh` — look around inside the container (env vars, files, can it
      reach the Service?)
- [ ] `kubectl get events --sort-by=.lastTimestamp`
- [ ] `kubectl get pod <pod> -o yaml` — the full object, including what Kubernetes filled in for you

## 7. Explain every field — the deliverable

This is what I'll actually test you on. Write `submissions/week-01/manifests-explained.md` covering
**every field** in every file under `k8s/` — `apiVersion`, `kind`, `metadata`, and everything in
`spec` down to the last line. For each field: what it does, and what would happen if you removed it
or got it wrong.

- [ ] `kind-config.yaml` explained
- [ ] `deployment.yaml` explained
- [ ] `service.yaml` explained
- [ ] `pvc.yaml` explained (if you have one)
- [ ] Be ready to answer "why this value and not another?" for anything you set — replicas, resource
      numbers, probe timings, Service type

Expect me to point at a random line during review and ask about it.

## 8. Submission — opening your PR

When you're done with this week, open a PR against this repo's `main` branch. I'll review it the
same way I'd review any real PR — treat it that way.

- [ ] Work on a branch named `week-01` (not directly on `main`)
- [ ] PR title: `Week 1 — Docker to Kind`
- [ ] PR description includes:
  - A short summary of what you did and what you learned
  - Which checklist items above you completed vs. skipped, and why if skipped (e.g. no PVC because
    the app is stateless)
  - Anything that broke, confused you, or you'd do differently
- [ ] The PR diff includes:
  - Your app + `Dockerfile` under `app/`
  - Your manifests under `k8s/`
  - Your evidence and write-ups under `submissions/week-01/` (see that folder's README)
- [ ] Evidence the app is live — `kubectl get all` output plus a `curl`/browser screenshot hitting it
      through the NodePort, pasted into the PR description or added under `submissions/week-01/`
- [ ] Anyone should be able to reproduce your setup from the repo: add a short "Run it on Kind"
      section to the root `README.md` with the exact commands, from `kind create cluster` to
      opening the app
- [ ] Keep the PR scoped to week 1 — don't bundle in unrelated changes
- [ ] Commit history makes sense on its own (squash noisy WIP commits if needed)

I'll leave feedback as comments directly on the PR. Don't merge it yourself — leave it open until
I approve.

## Notes / blockers

_(fill in as you go — what broke, what you learned, what you'd do differently)_
