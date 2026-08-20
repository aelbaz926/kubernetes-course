# Demo 13: Network Policies

## Concept

**Network Policies** are Kubernetes resources that control traffic flow between pods. They act as a **firewall for your pods**, defining rules for ingress (incoming) and egress (outgoing) traffic.

### The Problem Without Network Policies

By default in Kubernetes:
- ❌ **Any pod can talk to any other pod** in the cluster
- ❌ Frontend pods can directly access database pods
- ❌ Compromised pods can scan and attack other services
- ❌ No network segmentation or isolation

With Network Policies:
- ✅ **Least privilege** — only allow required traffic
- ✅ **Segmentation** — enforce tier boundaries (frontend → backend → database)
- ✅ **Namespace isolation** — separate environments (prod/staging/dev)
- ✅ **Egress control** — prevent data exfiltration

### How Network Policies Work

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NETWORK POLICY MODEL                             │
│                                                                      │
│  podSelector:         WHO does this policy apply to?                 │
│    matchLabels:                                                      │
│      app: backend     → All pods with label app=backend              │
│                                                                      │
│  policyTypes:         WHAT direction of traffic?                     │
│  - Ingress            → Incoming traffic                             │
│  - Egress             → Outgoing traffic                             │
│                                                                      │
│  ingress/egress:      WHICH traffic is ALLOWED?                      │
│  - from/to:                                                          │
│    - podSelector      → Match by pod labels                          │
│    - namespaceSelector → Match by namespace labels                   │
│    - ipBlock          → Match by IP CIDR range                       │
│    ports:                                                            │
│    - port: 80         → Only on specific ports                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **podSelector** | Which pods this policy applies to (by labels) |
| **policyTypes** | Ingress, Egress, or both |
| **ingress.from** | Who CAN send traffic to selected pods |
| **egress.to** | Where selected pods CAN send traffic |
| **No policy** | All traffic allowed (default) |
| **Empty policy** | All traffic denied (deny-all baseline) |

### Default Behavior

- **No NetworkPolicy exists** → All traffic allowed (open by default)
- **NetworkPolicy with empty podSelector `{}`** → Applies to ALL pods in namespace
- **PolicyType specified but no rules** → All traffic of that type is DENIED

---

## ⚠️ Prerequisites: Installing Calico on Docker Desktop

**Docker Desktop's default CNI does NOT enforce Network Policies.** You must install Calico first.

### Install Calico

```bash
# Install Calico operator and CRDs
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# Install Calico custom resources (with default settings)
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml

# Wait for Calico to be ready (takes 1-2 minutes)
kubectl get pods -n calico-system -w

# Verify all Calico pods are Running
kubectl get pods -n calico-system
```

**Expected output:**
```
NAME                                       READY   STATUS    RESTARTS   AGE
calico-kube-controllers-xxxxx              1/1     Running   0          2m
calico-node-xxxxx                          1/1     Running   0          2m
calico-typha-xxxxx                         1/1     Running   0          2m
csi-node-driver-xxxxx                      2/2     Running   0          2m
```

### Verify Network Policy Support

```bash
# Check NetworkPolicy API is available
kubectl api-resources | grep networkpolicies

# Should show:
# networkpolicies   netpol   networking.k8s.io/v1   true   NetworkPolicy
```

### Troubleshooting Calico on Docker Desktop

If Calico pods are stuck or crashing:

```bash
# Check operator status
kubectl get pods -n tigera-operator

# Check Calico node logs
kubectl logs -n calico-system -l k8s-app=calico-node

# If stuck, try reinstalling
kubectl delete -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/custom-resources.yaml
kubectl delete -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml
# Then re-run the install steps above
```

---

## Demo Scenarios

This section contains 4 progressive scenarios:

```
13-network-policies/
├── 01-default-allow/          # See the problem: all pods can talk to each other
├── 02-deny-all/               # Security baseline: block everything
├── 03-allow-specific/         # Whitelist: frontend → backend → database
└── 04-namespace-isolation/    # Isolate environments (prod/staging/dev)
```

### Recommended Order

1. **01-default-allow** — Observe the security problem
2. **02-deny-all** — Apply deny-all baseline
3. **03-allow-specific** — Whitelist specific traffic paths
4. **04-namespace-isolation** — Isolate namespaces from each other

---

## Quick Reference

| Scenario | Use Case | Pattern |
|----------|----------|---------|
| Default Deny | Security baseline | Block all, then whitelist |
| Pod-to-Pod | Microservices | Frontend → Backend only |
| Namespace Isolation | Multi-tenancy | Prod ↔ Dev separation |
| Egress Control | Data exfiltration | Block unwanted outbound |
| DNS Allow | Required with deny-all | Always allow UDP/53 to kube-system |

## Key Takeaways

- Network Policies require a **CNI plugin that supports them** (Calico on Docker Desktop)
- **Default** = all traffic allowed (no policies)
- **Best practice** = deny-all baseline, then whitelist needed traffic
- **Don't forget DNS!** — Deny-all egress blocks DNS resolution too
- Policies are **additive** (OR logic) — if ANY policy allows it, traffic flows
- Policies are **namespace-scoped** — must be applied in each namespace
