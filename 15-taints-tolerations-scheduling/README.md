# Demo 15: Taints, Tolerations & Pod Scheduling

## Concept

Kubernetes provides multiple mechanisms to control **which nodes pods run on**. This demo covers:

1. **Taints & Tolerations** — Nodes repel pods unless the pod tolerates the taint
2. **Node Selectors** — Pods select nodes by label (simple)
3. **Node Affinity** — Pods select nodes by label (advanced, with operators)
4. **Pod Affinity/Anti-Affinity** — Pods attract or repel other pods

### The Problem These Solve

Without scheduling controls:
- ❌ GPU workloads land on nodes without GPUs
- ❌ Production and dev workloads compete for the same nodes
- ❌ Latency-sensitive services run far from each other
- ❌ A noisy neighbor pod saturates a shared node
- ❌ All replicas land on one node (single point of failure)

With scheduling controls:
- ✅ **Dedicated nodes** — GPU pods only on GPU nodes
- ✅ **Isolation** — Production workloads on dedicated node pools
- ✅ **Co-location** — Related services run on the same node (low latency)
- ✅ **Spreading** — Replicas spread across failure domains
- ✅ **Eviction** — Drain nodes for maintenance without killing critical workloads

---

## Cluster Setup

This demo uses a **4-node cluster**. Check your nodes:

```bash
kubectl get nodes
# NAME       STATUS   ROLES           AGE   VERSION
# node-1     Ready    control-plane   ..    ..
# node-2     Ready    <none>          ..    ..
# node-3     Ready    <none>          ..    ..
# node-4     Ready    <none>          ..    ..
```

> **Note:** Throughout this demo, replace `node-2`, `node-3`, `node-4` with your actual node names from `kubectl get nodes`.

---

## Taints & Tolerations

### How They Work

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TAINTS & TOLERATIONS                              │
│                                                                      │
│  NODE (has taints)              POD (has tolerations)                 │
│  ─────────────────              ──────────────────────               │
│                                                                      │
│  "I'm special —                 "I can handle that                    │
│   stay away unless               special requirement"                 │
│   you can handle me"                                                 │
│                                                                      │
│  Taint: gpu=true:NoSchedule     Toleration: gpu=true:NoSchedule     │
│                                                                      │
│  Pod WITHOUT toleration → ❌ REJECTED from this node                 │
│  Pod WITH toleration    → ✅ CAN schedule on this node               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Taint Effects

| Effect | Behavior |
|--------|----------|
| `NoSchedule` | New pods won't be scheduled (existing pods stay) |
| `PreferNoSchedule` | Scheduler tries to avoid, but not guaranteed |
| `NoExecute` | Evicts existing pods AND prevents new scheduling |

### Taint Format

```bash
# Add a taint to a node
kubectl taint nodes <node> key=value:Effect

# Examples
kubectl taint nodes node-2 gpu=true:NoSchedule
kubectl taint nodes node-3 env=production:NoSchedule
kubectl taint nodes node-4 maintenance=true:NoExecute

# Remove a taint (add minus at the end)
kubectl taint nodes node-2 gpu=true:NoSchedule-
```

### Toleration Format

```yaml
tolerations:
- key: "gpu"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"

# Or match any value for the key
- key: "gpu"
  operator: "Exists"
  effect: "NoSchedule"
```

---

## Node Selectors & Affinity

### nodeSelector (Simple)

```yaml
spec:
  nodeSelector:
    disktype: ssd       # Pod only runs on nodes with this label
```

### Node Affinity (Advanced)

```yaml
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:    # HARD rule (must match)
        nodeSelectorTerms:
        - matchExpressions:
          - key: disktype
            operator: In
            values: ["ssd", "nvme"]
      preferredDuringSchedulingIgnoredDuringExecution:   # SOFT rule (prefers)
      - weight: 80
        preference:
          matchExpressions:
          - key: zone
            operator: In
            values: ["us-east-1a"]
```

### Pod Affinity/Anti-Affinity

```yaml
spec:
  affinity:
    podAffinity:           # Run NEAR these pods
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: cache
        topologyKey: kubernetes.io/hostname

    podAntiAffinity:       # Run AWAY from these pods
      requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: web
        topologyKey: kubernetes.io/hostname
```

---

## Demo Files

```
15-taints-tolerations-scheduling/
├── 01-taint-noschedule.yaml          # Basic taint: NoSchedule
├── 02-toleration.yaml                # Pod that tolerates the taint
├── 03-taint-noexecute.yaml           # Eviction taint
├── 04-node-selector.yaml             # Simple node selection
├── 05-node-affinity.yaml             # Advanced node affinity
├── 06-pod-anti-affinity.yaml         # Spread replicas across nodes
└── README.md
```

---

## Step-by-Step Demo

### Demo 1: Taint with NoSchedule

This demonstrates that tainting a node **prevents new pods from being scheduled** on it.

```bash
# Check your nodes
kubectl get nodes
# Pick a worker node (e.g., node-2)

# Apply a taint to ONE node
kubectl taint nodes node-2 dedicated=gpu:NoSchedule

# Try to deploy a pod WITHOUT a toleration
kubectl apply -f 01-taint-noschedule.yaml

# Check which node it landed on — it avoids node-2!
kubectl get pods -l demo=taint-noschedule -o wide
# NODE: node-3 or node-4 (never node-2)

# Scale up to see the pattern
kubectl run taint-test-1 --image=nginx:alpine -l demo=taint-noschedule
kubectl run taint-test-2 --image=nginx:alpine -l demo=taint-noschedule

# All pods avoid the tainted node
kubectl get pods -l demo=taint-noschedule -o wide
# None on node-2!
```

Now taint ALL worker nodes to see a pod go Pending:

```bash
# Taint ALL worker nodes
kubectl taint nodes node-3 dedicated=gpu:NoSchedule
kubectl taint nodes node-4 dedicated=gpu:NoSchedule

# Delete and recreate the pod
kubectl delete pod -l demo=taint-noschedule
kubectl apply -f 01-taint-noschedule.yaml

# Now it's PENDING — no untainted node available!
kubectl get pods -l demo=taint-noschedule
# STATUS: Pending

kubectl describe pod -l demo=taint-noschedule | grep -A3 Events
# "0/4 nodes are available: 3 node(s) had untolerated taint, 1 node(s) had taint that the pod didn't tolerate"

# Clean up all taints
kubectl taint nodes node-2 dedicated=gpu:NoSchedule-
kubectl taint nodes node-3 dedicated=gpu:NoSchedule-
kubectl taint nodes node-4 dedicated=gpu:NoSchedule-

# Pod becomes Running
kubectl get pods -l demo=taint-noschedule -w
```

### Demo 2: Pod with Toleration

This pod **tolerates** the taint and CAN be scheduled on the tainted node:

```bash
# Taint one node
kubectl taint nodes node-2 dedicated=gpu:NoSchedule

# Deploy pod WITH toleration
kubectl apply -f 02-toleration.yaml

# This pod CAN run on node-2 (it tolerates the taint) ✅
kubectl get pods -l demo=toleration -o wide
# It might land on node-2, node-3, or node-4 (toleration allows it but doesn't force it)

# Deploy pod WITHOUT toleration (from demo 1)
kubectl delete -f 01-taint-noschedule.yaml 2>/dev/null
kubectl apply -f 01-taint-noschedule.yaml

# This pod CANNOT run on node-2 ❌
kubectl get pods -l demo=taint-noschedule -o wide
# Always on node-3 or node-4 (never node-2)

# Clean up taint
kubectl taint nodes node-2 dedicated=gpu:NoSchedule-
```

### Demo 3: Taint with NoExecute (Eviction)

`NoExecute` is more aggressive — it **evicts existing running pods**:

```bash
# Clean up previous demos
kubectl delete -f 01-taint-noschedule.yaml -f 02-toleration.yaml 2>/dev/null

# Deploy some regular pods
kubectl run eviction-test-1 --image=nginx:alpine -l demo=eviction
kubectl run eviction-test-2 --image=nginx:alpine -l demo=eviction
kubectl wait --for=condition=ready pod -l demo=eviction --timeout=60s

# Check which nodes they're on
kubectl get pods -l demo=eviction -o wide

# Now apply a NoExecute taint to one of those nodes
# (replace node-X with the node one of the pods is on)
kubectl taint nodes node-2 maintenance=true:NoExecute

# Watch pods get EVICTED from that node!
kubectl get pods -l demo=eviction -o wide -w
# Pods on node-2 get terminated and rescheduled to other nodes

# Deploy pod with NoExecute toleration + tolerationSeconds
kubectl apply -f 03-taint-noexecute.yaml

# This pod CAN run on the tainted node, but only for 60 seconds
kubectl get pods -l demo=noexecute-toleration -o wide -w
# After 60 seconds, it gets evicted even though it has the toleration

# Clean up
kubectl taint nodes node-2 maintenance=true:NoExecute-
kubectl delete pod -l demo=eviction
```

### Demo 4: Node Selector

Simple label-based scheduling:

```bash
# Label ONE specific node
kubectl label nodes node-3 disktype=ssd

# Deploy pod with nodeSelector
kubectl apply -f 04-node-selector.yaml

# Pod runs ONLY on the labeled node ✅
kubectl get pods -l demo=node-selector -o wide
# NODE: node-3 (the only one with disktype=ssd)

# Try removing the label (pod stays — labels checked at scheduling time only)
kubectl label nodes node-3 disktype-

# Delete and recreate — now it goes Pending (no matching node)
kubectl delete -f 04-node-selector.yaml
kubectl apply -f 04-node-selector.yaml
kubectl get pods -l demo=node-selector
# STATUS: Pending

# Re-add label to fix it
kubectl label nodes node-3 disktype=ssd
kubectl get pods -l demo=node-selector -w
# STATUS: Running
```

### Demo 5: Node Affinity

Advanced node selection with required + preferred rules:

```bash
# Label nodes with zone info
kubectl label nodes node-2 zone=us-east-1a
kubectl label nodes node-3 zone=us-east-1a disktype=ssd
kubectl label nodes node-4 zone=us-east-1b

# Deploy pod with node affinity
kubectl apply -f 05-node-affinity.yaml

# Pod runs on a node in zone us-east-1a or us-east-1b (required)
# And PREFERS nodes with disktype=ssd (preferred, weight 80)
kubectl get pod -l demo=node-affinity -o wide
# Most likely on node-3 (matches zone AND has ssd preference)

# Check scheduling decision
kubectl describe pod -l demo=node-affinity | grep "Node:"
```

### Demo 6: Pod Anti-Affinity (Spread Replicas)

With 4 nodes, replicas actually **spread across different nodes**:

```bash
kubectl apply -f 06-pod-anti-affinity.yaml

# Watch replicas spread across nodes ✅
kubectl get pods -l demo=anti-affinity -o wide
# NAME                          NODE
# web-spread-xxxxx-aaaaa        node-2
# web-spread-xxxxx-bbbbb        node-3
# web-spread-xxxxx-ccccc        node-4
# Each replica on a DIFFERENT node!

# The deployment has 3 replicas and we have 3+ worker nodes
# So all replicas can be satisfied

# Try scaling to more than available nodes
kubectl scale deployment web-spread --replicas=5
kubectl get pods -l app=web-spread -o wide
# 3-4 running, extras may be Pending (can't find unique node)
```

---

## Verify Scheduling with `kubectl describe`

```bash
# See why a pod is Pending
kubectl describe pod <pod-name>

# Common scheduling failure messages:
# "0/4 nodes are available: 3 node(s) had untolerated taint"
# "0/4 nodes are available: 4 node(s) didn't match node selector"
# "0/4 nodes are available: 1 node(s) had untolerated taint, 3 didn't match pod anti-affinity rules"
```

---

## Real-World Use Cases

| Scenario | Mechanism | Example |
|----------|-----------|---------|
| GPU workloads | Taint + Toleration | Only ML pods on GPU nodes |
| Production isolation | Taint + Toleration | Prod nodes for prod pods only |
| Node maintenance | NoExecute taint | Drain node gracefully |
| SSD-required workloads | nodeSelector/Affinity | Database on SSD nodes |
| High-availability | Pod Anti-Affinity | Spread replicas across nodes |
| Low-latency | Pod Affinity | Co-locate app + cache |
| Zone spreading | Topology spreading | Replicas across AZs |

---

## Clean Up

```bash
# Delete all demo pods/deployments
kubectl delete -f .

# Remove node labels
kubectl label nodes node-2 zone- disktype- 2>/dev/null
kubectl label nodes node-3 zone- disktype- 2>/dev/null
kubectl label nodes node-4 zone- disktype- 2>/dev/null

# Remove any lingering taints
kubectl taint nodes node-2 dedicated=gpu:NoSchedule- 2>/dev/null
kubectl taint nodes node-3 dedicated=gpu:NoSchedule- 2>/dev/null
kubectl taint nodes node-4 dedicated=gpu:NoSchedule- 2>/dev/null
kubectl taint nodes node-2 maintenance=true:NoExecute- 2>/dev/null

# Delete extra test pods
kubectl delete pod -l demo=eviction 2>/dev/null
```

---

## Key Takeaways

- **Taints** = nodes repel pods, **Tolerations** = pods accept taints
- **NoSchedule** = prevent scheduling, **NoExecute** = evict running pods
- Tolerations don't ATTRACT pods — they only remove the repulsion
- **nodeSelector** = simple label matching (exact key=value)
- **Node Affinity** = advanced matching (In, NotIn, Exists, operators, weights)
- **Pod Anti-Affinity** = spread replicas across failure domains
- To guarantee a pod on a specific node: **taint + toleration + nodeSelector**
- `tolerationSeconds` on NoExecute = "stay for X seconds, then get evicted"
- With 4 nodes, anti-affinity can spread 3 replicas perfectly across worker nodes
