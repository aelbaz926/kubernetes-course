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
│  Pod WITHOUT toleration → ❌ REJECTED                                │
│  Pod WITH toleration    → ✅ SCHEDULED (if it also selects this node)│
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
kubectl taint nodes node1 gpu=true:NoSchedule
kubectl taint nodes node1 env=production:NoSchedule
kubectl taint nodes node1 maintenance=true:NoExecute
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

### ⚠️ Docker Desktop Note

Docker Desktop has a **single node** (`docker-desktop`). Taints and tolerations still work — we'll taint that node and see pods get rejected, then add tolerations to fix it.

For pod anti-affinity demos, the single-node limitation means pods may stay Pending. This is expected behavior that proves the scheduling rules are working.

---

### Demo 1: Taint with NoSchedule

This demonstrates that tainting a node **prevents new pods from being scheduled** on it.

```bash
# Check your node name
kubectl get nodes
# Output: docker-desktop

# Apply a taint to the node
kubectl taint nodes docker-desktop dedicated=gpu:NoSchedule

# Try to deploy a pod WITHOUT a toleration
kubectl apply -f 01-taint-noschedule.yaml

# Check pod status — it will be PENDING (can't be scheduled!)
kubectl get pods -l demo=taint-noschedule
# STATUS: Pending

# Check why it's pending
kubectl describe pod -l demo=taint-noschedule | grep -A5 Events
# "0/1 nodes are available: 1 node(s) had untolerated taint {dedicated: gpu}"

# Clean up the taint (important!)
kubectl taint nodes docker-desktop dedicated=gpu:NoSchedule-

# Pod should now become Running
kubectl get pods -l demo=taint-noschedule -w
```

### Demo 2: Pod with Toleration

This pod **tolerates** the taint and CAN be scheduled:

```bash
# Re-apply the taint
kubectl taint nodes docker-desktop dedicated=gpu:NoSchedule

# Deploy pod WITH toleration
kubectl apply -f 02-toleration.yaml

# This pod runs fine — it tolerates the taint ✅
kubectl get pods -l demo=toleration
# STATUS: Running

# Meanwhile, the pod from demo 1 is still Pending ❌
kubectl get pods -l demo=taint-noschedule
# STATUS: Pending (no toleration)

# Clean up taint
kubectl taint nodes docker-desktop dedicated=gpu:NoSchedule-
```

### Demo 3: Taint with NoExecute (Eviction)

`NoExecute` is more aggressive — it **evicts existing running pods**:

```bash
# First clean up previous demos
kubectl delete -f 01-taint-noschedule.yaml -f 02-toleration.yaml 2>/dev/null

# Deploy a regular pod (no toleration)
kubectl apply -f 01-taint-noschedule.yaml
kubectl wait --for=condition=ready pod -l demo=taint-noschedule --timeout=60s

# Verify it's running
kubectl get pods -l demo=taint-noschedule
# STATUS: Running ✅

# Now apply a NoExecute taint — this EVICTS the running pod!
kubectl taint nodes docker-desktop maintenance=true:NoExecute

# Watch the pod get evicted
kubectl get pods -l demo=taint-noschedule
# STATUS: Terminated/Evicted → then Pending (can't reschedule)

# Deploy pod with NoExecute toleration (and tolerationSeconds)
kubectl apply -f 03-taint-noexecute.yaml

# This pod runs AND will be evicted after 60 seconds (tolerationSeconds)
kubectl get pods -l demo=noexecute-toleration
# STATUS: Running (for 60 seconds, then evicted)

# Clean up the taint (IMPORTANT — otherwise nothing can run!)
kubectl taint nodes docker-desktop maintenance=true:NoExecute-
```

### Demo 4: Node Selector

Simple label-based scheduling:

```bash
# Label the node
kubectl label nodes docker-desktop disktype=ssd

# Deploy pod with nodeSelector
kubectl apply -f 04-node-selector.yaml

# Pod runs on the labeled node ✅
kubectl get pods -l demo=node-selector -o wide
# NODE: docker-desktop

# Remove the label and try again
kubectl label nodes docker-desktop disktype-
kubectl delete -f 04-node-selector.yaml
kubectl apply -f 04-node-selector.yaml

# Pod is Pending — no node matches the selector
kubectl get pods -l demo=node-selector
# STATUS: Pending

# Re-add the label
kubectl label nodes docker-desktop disktype=ssd
# Pod becomes Running
```

### Demo 5: Node Affinity

Advanced node selection with operators:

```bash
# Label the node with zone info
kubectl label nodes docker-desktop zone=us-east-1a

# Deploy pod with node affinity
kubectl apply -f 05-node-affinity.yaml

# Pod runs — node matches affinity rules
kubectl get pods -l demo=node-affinity
# STATUS: Running

# Check which node it was scheduled on
kubectl get pod -l demo=node-affinity -o wide
```

### Demo 6: Pod Anti-Affinity (Spread Replicas)

Ensures replicas don't all land on the same node:

```bash
kubectl apply -f 06-pod-anti-affinity.yaml

# With single-node Docker Desktop:
# - First replica runs fine
# - Additional replicas will be Pending (can't find different node)
kubectl get pods -l demo=anti-affinity

# This proves anti-affinity is working! On a multi-node cluster,
# replicas would spread across different nodes.
kubectl describe pod -l demo=anti-affinity | grep -A3 "Events"
```

---

## Verify Scheduling with `kubectl describe`

```bash
# See why a pod is Pending
kubectl describe pod <pod-name>

# Common scheduling failure messages:
# "0/1 nodes are available: 1 node(s) had untolerated taint"
# "0/1 nodes are available: 1 node(s) didn't match node selector"
# "0/1 nodes are available: 1 node(s) didn't match pod anti-affinity rules"
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
# Delete all demo pods
kubectl delete -f .

# Remove node labels and taints
kubectl taint nodes docker-desktop dedicated=gpu:NoSchedule- 2>/dev/null
kubectl taint nodes docker-desktop maintenance=true:NoExecute- 2>/dev/null
kubectl label nodes docker-desktop disktype- zone- 2>/dev/null
```

---

## Key Takeaways

- **Taints** = nodes repel pods, **Tolerations** = pods accept taints
- **NoSchedule** = prevent scheduling, **NoExecute** = evict running pods
- **nodeSelector** = simple label matching (exact key=value)
- **Node Affinity** = advanced matching (In, NotIn, Exists, operators)
- **Pod Anti-Affinity** = spread replicas across failure domains
- Taints + Tolerations don't ATTRACT pods — they only remove the repulsion
- To guarantee a pod runs on a specific node, use **taint + toleration + nodeSelector**
- `tolerationSeconds` on NoExecute = "stay for X seconds, then leave"
