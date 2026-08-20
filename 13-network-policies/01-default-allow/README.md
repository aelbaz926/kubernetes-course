# Scenario 1: Default Allow (No Network Policies)

## What This Demonstrates

The default Kubernetes behavior when no Network Policies are applied — **all pods can communicate with each other freely**. This is a security problem.

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │ ──► │ Backend  │ ──► │ Database │
│ (tier:web)│     │ (tier:api)│     │(tier:data)│
└──────────┘     └──────────┘     └──────────┘
      │                                 ▲
      └─────────── DIRECT ACCESS ───────┘  ← This shouldn't be allowed!
```

## Step-by-Step Demo

### 1. Deploy the pods

```bash
kubectl apply -f setup.yaml

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all --timeout=60s

# Verify pods are running
kubectl get pods -o wide
```

### 2. Test connectivity — everything works (this is the problem!)

```bash
# Frontend → Backend ✅ (this is expected)
kubectl exec frontend -- wget -qO- --timeout=3 http://backend

# Frontend → Database ✅ (this is BAD! frontend shouldn't access DB directly)
kubectl exec frontend -- wget -qO- --timeout=3 http://database

# Backend → Database ✅ (this is expected)
kubectl exec backend -- wget -qO- --timeout=3 http://database

# Database → Backend ✅ (this is BAD! DB shouldn't initiate connections)
kubectl exec database -- wget -qO- --timeout=3 http://backend
```

### 3. Observe the security issue

**All connections succeed** — no segmentation at all!

```
✅ frontend → backend    (OK - needed)
✅ frontend → database   (BAD - should go through backend!)
✅ backend → database    (OK - needed)
✅ database → backend    (BAD - DB shouldn't initiate outbound!)
```

## What We WANT Instead

```
✅ frontend → backend    (Allow)
❌ frontend → database   (Deny - must go through backend)
✅ backend → database    (Allow)
❌ database → backend    (Deny - DB is a sink, not a source)
```

We'll implement this in scenarios 02 and 03.

## Clean Up

```bash
kubectl delete -f setup.yaml
```

## Key Takeaway

Without Network Policies, Kubernetes has **zero network segmentation**. Any pod can reach any other pod — violating the principle of least privilege.
