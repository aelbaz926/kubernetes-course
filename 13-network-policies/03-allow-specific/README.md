# Scenario 3: Allow Specific Pod-to-Pod Traffic

## What This Demonstrates

How to **whitelist specific traffic** between pods using label selectors. This implements proper application tier segmentation: Frontend → Backend → Database.

## Architecture

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│ Frontend │ ──✅──► │ Backend  │ ──✅──► │ Database │
│ (app:    │         │ (app:    │         │ (app:    │
│  frontend)│         │  backend)│         │  database)│
└──────────┘         └──────────┘         └──────────┘
      │                                         ▲
      └──────────── ❌ BLOCKED ─────────────────┘
```

## Step-by-Step Demo

### 1. Deploy pods and apply deny-all baseline

```bash
# Deploy the three-tier app
kubectl apply -f ../01-default-allow/setup.yaml
kubectl wait --for=condition=ready pod --all --timeout=60s

# Apply deny-all (security baseline)
kubectl apply -f ../02-deny-all/deny-all.yaml

# Verify everything is blocked
kubectl exec frontend -- wget -qO- --timeout=3 http://backend
# ❌ timeout
```

### 2. Allow DNS (required for service names to resolve)

```bash
kubectl apply -f allow-dns-egress.yaml
```

### 3. Allow Frontend → Backend (ingress + egress)

```bash
# Allow backend to ACCEPT traffic from frontend
kubectl apply -f allow-frontend-to-backend.yaml

# Allow frontend to SEND traffic to backend
kubectl apply -f allow-egress-to-services.yaml

# Test: Frontend → Backend ✅
kubectl exec frontend -- wget -qO- --timeout=3 http://backend
# ✅ Should succeed!
```

### 4. Allow Backend → Database

```bash
# Allow database to ACCEPT traffic from backend
kubectl apply -f allow-backend-to-database.yaml

# (Egress from backend is already allowed by allow-egress-to-services.yaml)

# Test: Backend → Database ✅
kubectl exec backend -- wget -qO- --timeout=3 http://database
# ✅ Should succeed!
```

### 5. Verify unauthorized paths are still blocked

```bash
# Frontend → Database ❌ (must go through backend)
kubectl exec frontend -- wget -qO- --timeout=3 http://database
# ❌ timeout — no policy allows this path

# Database → Backend ❌ (DB shouldn't initiate connections)
kubectl exec database -- wget -qO- --timeout=3 http://backend
# ❌ timeout — database has no egress policy
```

### 6. View all applied policies

```bash
kubectl get networkpolicies

# Describe a specific policy
kubectl describe networkpolicy backend-allow-frontend
```

## Expected Results

```
✅ frontend → backend    (Allowed: ingress policy + egress policy)
❌ frontend → database   (Denied: no ingress policy on database for frontend)
✅ backend → database    (Allowed: ingress policy + egress policy)
❌ database → backend    (Denied: no egress policy for database)
✅ All pods → DNS        (Allowed: DNS egress policy)
```

## Understanding the Policies

### Ingress Policy (allow traffic INTO backend)
```yaml
podSelector:
  matchLabels:
    app: backend        # Apply to backend pods
ingress:
- from:
  - podSelector:
      matchLabels:
        app: frontend   # Allow FROM frontend pods
  ports:
  - port: 80           # Only on port 80
```

**Reads as**: "Backend pods accept traffic from frontend pods on port 80"

### Egress Policy (allow traffic OUT FROM frontend)
```yaml
podSelector:
  matchLabels:
    app: frontend       # Apply to frontend pods
egress:
- to:
  - podSelector:
      matchLabels:
        app: backend    # Allow TO backend pods
```

**Reads as**: "Frontend pods can send traffic to backend pods"

### Why Both Ingress AND Egress?

For traffic to flow: `frontend → backend`
- Frontend needs **egress** to backend (allowed to send)
- Backend needs **ingress** from frontend (allowed to receive)

Both sides must allow it!

## Clean Up

```bash
kubectl delete -f .
kubectl delete -f ../02-deny-all/deny-all.yaml
kubectl delete -f ../01-default-allow/setup.yaml
```

## Key Takeaways

- Use **label selectors** to target specific pods
- Both **ingress AND egress** must be allowed for communication to work
- Policies are **additive** — multiple policies combine (OR logic)
- Always allow DNS when using deny-all egress
- This pattern enforces proper tier boundaries in microservices
