# Scenario 2: Deny All Traffic

## What This Demonstrates

How to implement a **default-deny** policy that blocks all ingress and egress traffic. This is the recommended security baseline — deny everything, then whitelist what's needed.

## Step-by-Step Demo

### 1. Deploy pods (reuse from scenario 01)

```bash
kubectl apply -f ../01-default-allow/setup.yaml
kubectl wait --for=condition=ready pod --all --timeout=60s

# Verify connectivity works (before policy)
kubectl exec frontend -- wget -qO- --timeout=3 http://backend
# ✅ Should succeed
```

### 2. Apply the deny-all policy

```bash
kubectl apply -f deny-all.yaml

# Check the policy
kubectl get networkpolicies
kubectl describe networkpolicy deny-all
```

### 3. Test — everything is now blocked

```bash
# All connections now fail ❌
kubectl exec frontend -- wget -qO- --timeout=3 http://backend
# ❌ timeout

kubectl exec backend -- wget -qO- --timeout=3 http://database
# ❌ timeout

# Even DNS resolution fails!
kubectl exec frontend -- nslookup backend
# ❌ fails — can't resolve service names
```

### 4. Fix DNS (required for service discovery)

```bash
# Allow DNS egress to kube-system
kubectl apply -f allow-dns.yaml

# Now DNS resolution works
kubectl exec frontend -- nslookup backend
# ✅ resolves the name

# But connections still fail (ingress is still blocked)
kubectl exec frontend -- wget -qO- --timeout=3 http://backend
# ❌ timeout — we only allowed DNS, not actual traffic
```

## Understanding the Policy

```yaml
spec:
  podSelector: {}      # Empty = applies to ALL pods in the namespace
  policyTypes:
  - Ingress            # Control incoming traffic
  - Egress             # Control outgoing traffic
  # No rules defined = DENY EVERYTHING
```

**Key insight**: Specifying `policyTypes` without any rules = deny all traffic of that type.

## Expected Results After deny-all + allow-dns

```
❌ frontend → backend    (Ingress denied on backend)
❌ frontend → database   (Ingress denied on database)
❌ backend → database    (Ingress denied on database)
✅ Any pod → DNS         (Allowed by allow-dns policy)
❌ Any pod → Internet    (Egress denied)
```

## Why Start with Deny-All?

This is the **security baseline** for production:

1. Start with deny-all (assume nothing is allowed)
2. Explicitly whitelist only required traffic paths
3. Principle of least privilege
4. Easy to audit — if it's not in a policy, it's blocked

## Clean Up

```bash
kubectl delete -f deny-all.yaml
kubectl delete -f allow-dns.yaml
kubectl delete -f ../01-default-allow/setup.yaml
```

## Key Takeaways

- Empty `podSelector: {}` = applies to **all pods** in the namespace
- `policyTypes` specified without rules = **deny all**
- Deny-all egress **breaks DNS** — always add a DNS allow policy
- Multiple NetworkPolicies are **additive** (OR logic)
- This is the recommended production security baseline
