# Scenario 4: Namespace Isolation

## What This Demonstrates

How to **isolate traffic between namespaces** using `namespaceSelector`. Essential for multi-tenant clusters or separating environments (prod/staging/dev).

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   production    │     │    staging      │     │  development    │
│                 │     │                 │     │                 │
│   ┌─────┐      │  ❌ │   ┌─────┐      │  ❌ │   ┌─────┐      │
│   │ app │◄─────┼──┘  │   │ app │◄─────┼──┘  │   │ app │      │
│   └─────┘      │     │   └─────┘      │     │   └─────┘      │
│                 │     │                 │     │                 │
│ Only same-ns   │     │ Only same-ns   │     │ Only same-ns   │
│ traffic allowed│     │ traffic allowed│     │ traffic allowed│
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Step-by-Step Demo

### 1. Create namespaces

```bash
kubectl apply -f namespaces.yaml

# Verify namespaces and their labels
kubectl get namespaces --show-labels | grep -E "production|staging|development"
```

### 2. Deploy apps in each namespace

```bash
kubectl apply -f apps.yaml

# Wait for pods in all namespaces
kubectl wait --for=condition=ready pod/app -n production --timeout=60s
kubectl wait --for=condition=ready pod/app -n staging --timeout=60s
kubectl wait --for=condition=ready pod/app -n development --timeout=60s
```

### 3. Test cross-namespace access BEFORE policies

```bash
# Production → Staging ✅ (no policies yet)
kubectl exec -n production app -- wget -qO- --timeout=3 http://app.staging

# Staging → Production ✅
kubectl exec -n staging app -- wget -qO- --timeout=3 http://app.production

# Development → Production ✅ (this is dangerous!)
kubectl exec -n development app -- wget -qO- --timeout=3 http://app.production
```

### 4. Apply namespace isolation policies

```bash
# Deny cross-namespace ingress (only allow same-namespace)
kubectl apply -f deny-cross-namespace.yaml

# Allow DNS + same-namespace egress
kubectl apply -f allow-dns.yaml
```

### 5. Test cross-namespace access AFTER policies

```bash
# Production → Staging ❌
kubectl exec -n production app -- wget -qO- --timeout=3 http://app.staging
# ❌ timeout

# Staging → Production ❌
kubectl exec -n staging app -- wget -qO- --timeout=3 http://app.production
# ❌ timeout

# Development → Production ❌
kubectl exec -n development app -- wget -qO- --timeout=3 http://app.production
# ❌ timeout
```

### 6. (Advanced) Allow staging → production access

Sometimes you need staging to test against production services:

```bash
kubectl apply -f allow-staging-to-production.yaml

# Now staging CAN access production ✅
kubectl exec -n staging app -- wget -qO- --timeout=3 http://app.production
# ✅ Should succeed!

# But production still cannot access staging ❌
kubectl exec -n production app -- wget -qO- --timeout=3 http://app.staging
# ❌ timeout — one-way access only
```

## Understanding Namespace Selectors

```yaml
# Allow from SAME namespace only (no namespaceSelector = same namespace)
ingress:
- from:
  - podSelector: {}    # All pods in THIS namespace

# Allow from a SPECIFIC namespace
ingress:
- from:
  - namespaceSelector:
      matchLabels:
        env: staging   # All pods in namespaces labeled env=staging
```

### AND vs OR logic

```yaml
# OR: Any pod in same namespace OR any pod in staging namespace
ingress:
- from:
  - podSelector: {}              # Separate list item = OR
  - namespaceSelector:
      matchLabels:
        env: staging             # Separate list item = OR

# AND: Only pods labeled app=frontend AND in staging namespace
ingress:
- from:
  - podSelector:                 # Same list item = AND
      matchLabels:
        app: frontend
    namespaceSelector:           # Same list item = AND
      matchLabels:
        env: staging
```

## Expected Results

After applying isolation policies:

```
❌ production → staging      (Denied)
❌ production → development  (Denied)
❌ staging → production      (Denied → then ✅ after allow-staging-to-production)
❌ staging → development     (Denied)
❌ development → production  (Denied)
❌ development → staging     (Denied)
✅ Within same namespace     (Allowed by podSelector: {})
```

## Clean Up

```bash
kubectl delete -f .
kubectl delete namespace production staging development
```

## Key Takeaways

- Use **namespace labels** for `namespaceSelector`
- `podSelector: {}` without a `namespaceSelector` = same namespace only
- Policies must be applied **in each namespace** you want to protect
- Great for: environment isolation, multi-tenancy, compliance zones
- Combine with pod-level policies for fine-grained control
