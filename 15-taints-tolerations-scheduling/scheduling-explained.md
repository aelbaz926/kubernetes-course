# Scheduling Deep Dive: topologyKey & Weight Explained

## Understanding `topologyKey`

`topologyKey` tells Kubernetes: **"What defines a 'zone' for spreading/co-locating?"**

It refers to a **label on the nodes**. Nodes with the **same value** for that label are considered to be in the **same topology domain**.

### Example: 4-Node Cluster with Labels

```
Node       Labels
─────      ──────────────────────────────────────────────
node-1     kubernetes.io/hostname=node-1, zone=us-east-1a
node-2     kubernetes.io/hostname=node-2, zone=us-east-1a
node-3     kubernetes.io/hostname=node-3, zone=us-east-1b
node-4     kubernetes.io/hostname=node-4, zone=us-east-1b
```

### Scenario: Pod Anti-Affinity with 3 replicas

---

**Case 1: `topologyKey: kubernetes.io/hostname`** (per-node)

Each node has a unique hostname → each node is its own "zone":
```
Replica 1 → node-1 (zone = "node-1")
Replica 2 → node-2 (zone = "node-2")  ← different hostname ✅
Replica 3 → node-3 (zone = "node-3")  ← different hostname ✅
```
Result: **One replica per node** — maximum spread.

---

**Case 2: `topologyKey: topology.kubernetes.io/zone`** (per-AZ)

node-1 and node-2 share `zone=us-east-1a` → they're the **same "zone"**:
```
zone us-east-1a = [node-1, node-2]   ← same domain
zone us-east-1b = [node-3, node-4]   ← same domain
```

Anti-affinity says "don't put two replicas in the same zone":
```
Replica 1 → node-1 or node-2 (zone us-east-1a)
Replica 2 → node-3 or node-4 (zone us-east-1b)  ← different zone ✅
Replica 3 → PENDING ❌ (only 2 zones exist!)
```
Result: **One replica per AZ** — even if nodes have capacity, the rule is about zones not nodes.

---

**Case 3: `topologyKey: topology.kubernetes.io/region`** (per-region)

If all 4 nodes are in region `us-east-1`:
```
region us-east-1 = [node-1, node-2, node-3, node-4]   ← ALL same domain
```

Anti-affinity says "don't put two replicas in the same region":
```
Replica 1 → any node (region us-east-1)
Replica 2 → PENDING ❌ (no other region exists!)
```
Result: Only useful in **multi-region** clusters.

---

### Visual Summary

```
topologyKey = kubernetes.io/hostname (each node is unique)
┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│ node-1 │  │ node-2 │  │ node-3 │  │ node-4 │
│ Pod ✅ │  │ Pod ✅ │  │ Pod ✅ │  │        │
└────────┘  └────────┘  └────────┘  └────────┘
  4 domains → up to 4 replicas spread

topologyKey = topology.kubernetes.io/zone (nodes grouped by AZ)
┌─────────────────────┐  ┌─────────────────────┐
│   us-east-1a        │  │   us-east-1b        │
│ [node-1] [node-2]  │  │ [node-3] [node-4]  │
│   Pod ✅            │  │   Pod ✅            │
└─────────────────────┘  └─────────────────────┘
  2 domains → up to 2 replicas spread

topologyKey = topology.kubernetes.io/region (all nodes in one region)
┌─────────────────────────────────────────────┐
│               us-east-1                      │
│  [node-1] [node-2] [node-3] [node-4]       │
│   Pod ✅                                    │
└─────────────────────────────────────────────┘
  1 domain → only 1 replica (useless for spreading!)
```

### When to Use Each topologyKey

| topologyKey | Use Case | Example |
|-------------|----------|---------|
| `kubernetes.io/hostname` | Max spreading across nodes | Web servers — lose 1 node, lose 1 replica |
| `topology.kubernetes.io/zone` | AZ-level HA (cloud) | Database — survive entire AZ failure |
| `topology.kubernetes.io/region` | Multi-region (rare) | Global services — survive region outage |

### The Key Insight

**`topologyKey` doesn't create the groups — the node labels do.** The `topologyKey` just tells the scheduler which label to look at when deciding "are these two nodes in the same domain or different domains?"

---

## Understanding `weight` (Preferred Rules)

The `weight` field (1-100) is used in **preferred (soft) rules** — both in node affinity and pod affinity/anti-affinity. It tells the scheduler: "how much do I care about this preference?"

### How Weight Scoring Works

When multiple nodes are valid candidates, the scheduler **scores** each node. The weight is added to a node's score if it matches the preference.

### Example: Multiple Preferred Rules with Different Weights

```yaml
preferredDuringSchedulingIgnoredDuringExecution:
- weight: 80              # "I strongly prefer SSD"
  preference:
    matchExpressions:
    - key: disktype
      operator: In
      values: ["ssd"]
- weight: 20              # "I slightly prefer us-east-1a, but not a big deal"
  preference:
    matchExpressions:
    - key: zone
      operator: In
      values: ["us-east-1a"]
```

### Scoring Example with 4 Nodes

```
Node     Labels                        Score Calculation        Total
─────    ──────────────────────────    ─────────────────────   ─────
node-1   disktype=ssd, zone=us-east-1a  +80 (ssd) +20 (zone)   100  ← WINNER
node-2   disktype=ssd, zone=us-east-1b  +80 (ssd) +0           80
node-3   disktype=hdd, zone=us-east-1a  +0        +20 (zone)   20
node-4   disktype=hdd, zone=us-east-1b  +0        +0           0
```

The scheduler picks **node-1** (highest score). But if node-1 is full or unhealthy, it falls back to node-2, then node-3, etc.

### Weight in Pod Anti-Affinity

```yaml
podAntiAffinity:
  preferredDuringSchedulingIgnoredDuringExecution:
  - weight: 50
    podAffinityTerm:
      labelSelector:
        matchLabels:
          app: backend-app
      topologyKey: kubernetes.io/hostname
```

Here `weight: 50` means: "I'd prefer to avoid nodes with `backend-app` pods, but it's not critical. If all nodes have `backend-app`, schedule me anyway."

If this were `weight: 100`, the scheduler would try much harder to avoid those nodes — but still not as hard as `required` (which would make it Pending).

### Weight Guidelines

| Weight | Meaning | Example |
|--------|---------|---------|
| **100** | Very strong preference | "I really want SSD nodes" |
| **80** | Strong preference | "Prefer GPU nodes" |
| **50** | Moderate preference | "Nice to have, not critical" |
| **20** | Weak preference | "Slight tiebreaker if all else equal" |

### Key Points About Weights

- Weight is **NOT a probability** — it's a score added to the node
- Higher weight = stronger preference when choosing between nodes
- Multiple preferences **combine additively** (80 + 20 = 100)
- The pod **still schedules** even if NO preferred rule matches (score = 0)
- `required` rules **filter first**, then `preferred` weights break ties among remaining nodes
- The numbers are **relative to each other** — what matters is the ratio between your weights

---

## Required vs Preferred — Complete Comparison

| | Required | Preferred |
|---|---|---|
| **Keyword** | `requiredDuringScheduling...` | `preferredDuringScheduling...` |
| **Behavior** | Pod stays **Pending** if no match | Pod schedules **anyway** on best available |
| **Risk** | Pod may never run | Pod may land on suboptimal node |
| **Has weight?** | No | Yes (1-100) |
| **Use when** | "MUST have this" (SSD for DB) | "Nice to have" (prefer same AZ) |
| **Production tip** | Use sparingly — can cause Pending | Safer default — always schedules |

### Best Practice: Combine Both

```yaml
affinity:
  nodeAffinity:
    # MUST be in us-east-1 (hard requirement)
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.kubernetes.io/region
          operator: In
          values: ["us-east-1"]
    # PREFER zone-a, but zone-b is fine too
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 70
      preference:
        matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a"]
  podAntiAffinity:
    # PREFER spreading across nodes (soft — don't cause Pending)
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: my-app
        topologyKey: kubernetes.io/hostname
```

This says:
1. **Must** be in us-east-1 (hard rule — Pending if not possible)
2. **Prefer** zone-a (soft — score boost, won't block)
3. **Prefer** spreading across nodes (soft — co-locate if you must)
