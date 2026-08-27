# Demo 16: Helm — The Kubernetes Package Manager

## What is a Package Manager?

A **package manager** automates installing, upgrading, configuring, and removing software. You already use them daily:

| OS / Language | Package Manager | Example |
|---------------|-----------------|---------|
| macOS | Homebrew | `brew install nginx` |
| Ubuntu | apt | `apt install nginx` |
| Python | pip | `pip install flask` |
| Node.js | npm | `npm install express` |
| **Kubernetes** | **Helm** | `helm install my-app ./chart` |

Without a package manager, you'd manually download binaries, configure paths, resolve dependencies. In Kubernetes, without Helm you'd manually manage dozens of YAML files, copy-paste between environments, and have no versioning or rollback for your deployments.

---

## What is Helm?

**Helm** is the package manager for Kubernetes. It packages multiple Kubernetes resources (Deployments, Services, Secrets, ConfigMaps, etc.) into a single **Chart** that can be:

- Installed with one command
- Configured per environment using **values files**
- Versioned and rolled back
- Shared via repositories

### Key Terminology

| Term | Meaning |
|------|---------|
| **Chart** | A Helm package — a folder containing templates + values + metadata |
| **Release** | A specific installation of a chart (you can install the same chart multiple times with different release names) |
| **Values** | Configuration that gets injected into templates (like variables) |
| **Template** | Kubernetes YAML with Go template placeholders (`{{ .Values.xxx }}`) |
| **Repository** | A place where charts are stored and shared (like Docker Hub for images) |

### Chart Structure

```
my-chart/
├── Chart.yaml          # Metadata (name, version, description)
├── values.yaml         # Default configuration values
├── templates/          # Kubernetes manifests with template syntax
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── secret.yaml
│   └── _helpers.tpl    # Reusable template functions
├── values-dev.yaml     # (optional) Dev environment overrides
└── values-prod.yaml    # (optional) Prod environment overrides
```

---

## Why Helm is Useful

### The Problem: Managing Kubernetes YAML at Scale

Imagine deploying the Feedback App (Frontend + Backend + PostgreSQL) to 3 environments:

**Without Helm:**
```
k8s-dev/
  ├── frontend-deployment.yaml    (replicas: 1, tag: latest)
  ├── backend-deployment.yaml     (replicas: 1)
  ├── postgres-deployment.yaml    (password: devpass)
  ├── db-secret.yaml
  └── postgres-init-configmap.yaml

k8s-staging/
  ├── frontend-deployment.yaml    (replicas: 2, tag: v1.2.0)  ← copy-paste from dev, change values
  ├── backend-deployment.yaml     (replicas: 2)
  ├── ... (same 5 files, slightly different)

k8s-prod/
  ├── frontend-deployment.yaml    (replicas: 3, tag: v1.2.0)  ← another copy-paste
  ├── ... (same 5 files, slightly different)
```

Problems:
- ❌ **15 files** to manage (5 × 3 environments)
- ❌ Copy-paste errors — forgot to update a value in staging?
- ❌ No versioning — which version is deployed in prod?
- ❌ No rollback — "undo" means finding the old YAML and re-applying
- ❌ No reusability — another team wants the same app structure?

**With Helm:**
```
feedback-app-chart/
  ├── Chart.yaml
  ├── values.yaml           (defaults)
  ├── values-dev.yaml       (dev overrides)
  ├── values-prod.yaml      (prod overrides)
  └── templates/            (one set of templates)
```

```bash
# Deploy to dev
helm install feedback-dev ./feedback-app-chart -f values-dev.yaml

# Deploy to prod (same chart, different values!)
helm install feedback-prod ./feedback-app-chart -f values-prod.yaml

# Oops, prod is broken — rollback in one command!
helm rollback feedback-prod 1
```

Benefits:
- ✅ **One set of templates** — single source of truth
- ✅ **Values per environment** — just override what's different
- ✅ **Versioned releases** — Helm tracks every deployment
- ✅ **One-command rollback** — `helm rollback`
- ✅ **Shareable** — push the chart to a repo, other teams install it

---

## Helm Installation

```bash
# macOS (Homebrew)
brew install helm

# Linux (script)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Windows (Chocolatey)
choco install kubernetes-helm

# Verify
helm version
```

---

## Demo 1: Hello World Helm Chart

Let's start with the simplest possible Helm chart to understand the structure.

### 1. Look at the chart structure

```bash
ls hello-world-chart/
# Chart.yaml  values.yaml  templates/

cat hello-world-chart/Chart.yaml
cat hello-world-chart/values.yaml
cat hello-world-chart/templates/deployment.yaml
cat hello-world-chart/templates/service.yaml
```

### 2. Preview what Helm will generate (dry-run)

```bash
# "template" renders the templates without installing
helm template my-hello ./hello-world-chart
```

Notice how `{{ .Release.Name }}` becomes `my-hello` and `{{ .Values.image.repository }}` becomes `nginx`.

### 3. Install the chart

```bash
helm install my-hello ./hello-world-chart
```

### 4. Verify

```bash
# Helm tracks the release
helm list

# Kubernetes resources are created
kubectl get deployment
kubectl get service
kubectl get pods
```

### 5. Override values at install time

```bash
# Change replicas and image tag without editing any file
helm install my-hello-v2 ./hello-world-chart \
  --set replicaCount=3 \
  --set image.tag=latest

kubectl get pods
# → 3 pods running!
```

### 6. Upgrade a release

```bash
helm upgrade my-hello ./hello-world-chart --set replicaCount=3

# Check the release history
helm history my-hello
```

### 7. Rollback

```bash
helm rollback my-hello 1

kubectl get pods
# → back to 1 pod
```

### 8. Uninstall

```bash
helm uninstall my-hello
helm uninstall my-hello-v2
```

---

## Key Helm CLI Commands

| Command | What it does |
|---------|--------------|
| `helm install <name> <chart>` | Install a chart as a named release |
| `helm upgrade <name> <chart>` | Upgrade an existing release |
| `helm uninstall <name>` | Remove a release and its resources |
| `helm list` | List all releases in current namespace |
| `helm history <name>` | Show revision history of a release |
| `helm rollback <name> <revision>` | Rollback to a previous revision |
| `helm template <name> <chart>` | Render templates locally (dry-run, no install) |
| `helm lint <chart>` | Check chart for errors |
| `helm package <chart>` | Package chart into a `.tgz` archive |
| `helm repo add <name> <url>` | Add a chart repository |
| `helm repo update` | Refresh repository index |
| `helm search repo <keyword>` | Search charts in added repos |
| `helm show values <chart>` | Show default values of a chart |
| `helm get values <release>` | Show values used by an installed release |
| `helm install <name> <chart> -f values.yaml` | Install with custom values file |
| `helm install <name> <chart> --set key=val` | Install with inline value overrides |
| `helm install <name> <chart> --dry-run` | Simulate install without applying |
| `helm install <name> <chart> -n <ns> --create-namespace` | Install into a specific namespace |

### Values Override Priority (lowest to highest)

```
values.yaml (chart defaults)
    ↓ overridden by
-f values-prod.yaml (values file)
    ↓ overridden by
--set key=value (command line)
```

---

## Demo 2: Converting the Feedback App to a Helm Chart

Now let's see the real power of Helm — taking our [Feedback App](https://github.com/aelbaz926/feedback-app) with its 5 separate YAML files and converting it into a single, reusable, configurable Helm chart.

### Original app (hardcoded YAML):
```
k8s/
├── backend-deployment.yaml       # hardcoded image tag, replicas
├── db-secret.yaml                # hardcoded password
├── frontend-deployment.yaml      # hardcoded image tag, NodePort
├── postgres-deployment.yaml      # hardcoded everything
└── postgres-init-configmap.yaml
```

### Helm chart (templated):
```
feedback-app-chart/
├── Chart.yaml
├── values.yaml              # defaults
├── values-dev.yaml          # dev overrides
├── values-prod.yaml         # prod overrides
└── templates/
    ├── _helpers.tpl         # reusable template functions
    ├── backend.yaml         # Deployment + Service
    ├── frontend.yaml        # Deployment + Service
    ├── postgres.yaml        # Deployment + Service (conditionally enabled!)
    ├── configmap.yaml       # Init SQL script
    └── secret.yaml          # DB password (auto base64 encoded!)
```

### What we templated:

| Hardcoded before | Templated now |
|------------------|---------------|
| `replicas: 1` | `replicas: {{ .Values.frontend.replicaCount }}` |
| `image: ahmedhedihed/feedback-frontend:81` | `image: "{{ .Values.frontend.image.repository }}:{{ .Values.frontend.image.tag }}"` |
| `password: cGFzc3dvcmQ=` (pre-encoded) | `password: {{ .Values.database.password \| b64enc }}` (auto-encoded!) |
| `type: NodePort` / `nodePort: 30080` | Configurable per environment |
| Database always deployed | `{{- if .Values.database.enabled }}` — optional! |
| Resource names collide | `{{ .Release.Name }}-frontend` — unique per release |

### 3. Deploy to Dev

```bash
helm install feedback-dev ./feedback-app-chart -f ./feedback-app-chart/values-dev.yaml
```

```bash
# Verify
helm list
kubectl get all

# Access the app
kubectl port-forward svc/feedback-dev-frontend-service 8080:80
# Open http://localhost:8080
```

### 4. Deploy to Prod (same chart, different values!)

```bash
helm install feedback-prod ./feedback-app-chart -f ./feedback-app-chart/values-prod.yaml
```

```bash
# Two completely separate deployments from the SAME chart
helm list

# Dev has 1 replica, Prod has 3
kubectl get pods -l app=frontend
```

### 5. Upgrade prod with a new image tag

```bash
helm upgrade feedback-prod ./feedback-app-chart \
  -f ./feedback-app-chart/values-prod.yaml \
  --set frontend.image.tag="82"

# Check the history
helm history feedback-prod
```

### 6. Rollback prod

```bash
helm rollback feedback-prod 1

# Verify it's back to the previous tag
helm get values feedback-prod
```

### 7. Preview what Helm generates

```bash
# See the rendered YAML without installing
helm template feedback-dev ./feedback-app-chart -f ./feedback-app-chart/values-dev.yaml
```

### 8. Clean up

```bash
helm uninstall feedback-dev
helm uninstall feedback-prod
```

---

## Helm Repositories

Charts can be shared via **repositories** — just like Docker images on Docker Hub.

### Popular Helm Repos

| Repo | URL | Contains |
|------|-----|----------|
| Bitnami | `https://charts.bitnami.com/bitnami` | PostgreSQL, Redis, MongoDB, WordPress, etc. |
| Ingress-NGINX | `https://kubernetes.github.io/ingress-nginx` | NGINX Ingress Controller |
| Prometheus | `https://prometheus-community.github.io/helm-charts` | Prometheus, Grafana stack |
| Jetstack | `https://charts.jetstack.io` | cert-manager |

### Working with Repos

```bash
# Add a repository
helm repo add bitnami https://charts.bitnami.com/bitnami

# Update repo index (like apt update)
helm repo update

# Search for charts
helm search repo postgresql
helm search repo bitnami/nginx

# See a chart's default values BEFORE installing
helm show values bitnami/postgresql

# Install a community chart
helm install my-db bitnami/postgresql --set auth.postgresPassword=mypassword

# Install a specific version
helm install my-db bitnami/postgresql --version 12.5.8

# List installed releases
helm list

# Uninstall
helm uninstall my-db
```

### Creating Your Own Repo (optional)

```bash
# Package your chart
helm package ./feedback-app-chart
# → feedback-app-1.0.0.tgz

# Create index file for repo
helm repo index . --url https://your-org.github.io/helm-charts/

# Host via GitHub Pages, S3, or any HTTP server
```

---

## Template Syntax Quick Reference

| Syntax | Meaning | Example |
|--------|---------|---------|
| `{{ .Values.x }}` | Read from values.yaml | `{{ .Values.frontend.replicaCount }}` |
| `{{ .Release.Name }}` | Name of the release | `my-app` |
| `{{ .Chart.Name }}` | Chart name from Chart.yaml | `feedback-app` |
| `{{ .Release.Namespace }}` | Namespace installed into | `default` |
| `{{ include "tpl" . }}` | Include a named template | `{{ include "app.labels" . }}` |
| `{{- if .Values.x }}` | Conditional block | Only render if value is truthy |
| `{{- range .Values.list }}` | Loop over a list | Iterate over items |
| `{{ .Values.x \| b64enc }}` | Pipe to a function | Base64 encode |
| `{{ .Values.x \| quote }}` | Wrap in quotes | `"value"` |
| `{{ nindent 4 }}` | Add newline + indent | Properly format YAML blocks |

---

## Summary: Before vs After Helm

| Without Helm | With Helm |
|-------------|-----------|
| Copy-paste YAML per environment | One chart, multiple values files |
| Manual `kubectl apply -f` per file | `helm install` one command |
| No versioning | Full revision history |
| Rollback = find old YAML, re-apply | `helm rollback <name> <revision>` |
| Sharing = zip a folder of YAML | Push chart to a repository |
| Naming collisions between environments | `{{ .Release.Name }}` prefixes everything |
| Secrets in plain base64 in YAML | `{{ .Values.password \| b64enc }}` auto-encodes |

---

## Clean Up

```bash
# Remove all Helm releases from this demo
helm uninstall my-hello 2>/dev/null
helm uninstall my-hello-v2 2>/dev/null
helm uninstall feedback-dev 2>/dev/null
helm uninstall feedback-prod 2>/dev/null
```

---

## Key Takeaways

- **Helm is the Kubernetes package manager** — it packages, versions, and manages deployments
- A **Chart** is a folder of templates + values + metadata
- A **Release** is a specific installation of a chart
- **Values files** separate configuration from templates — one chart, many environments
- `helm install`, `helm upgrade`, `helm rollback` — simple lifecycle management
- **Repositories** let you share charts across teams and the community
- Helm eliminates copy-paste, adds versioning, and makes rollbacks trivial
