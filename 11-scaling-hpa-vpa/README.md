# Demo 11: Scaling — HPA & VPA

## Concept

Kubernetes offers two autoscaling mechanisms to handle varying workloads:

| Scaler | What it does | When to use |
|--------|--------------|-------------|
| **HPA** (Horizontal Pod Autoscaler) | Adds/removes Pod replicas | Stateless apps that handle more load with more instances |
| **VPA** (Vertical Pod Autoscaler) | Adjusts CPU/memory of existing Pods | Stateful apps or when you don't know the right resource requests |

---

## HPA — Scale Out/In (More Pods)

```
Load increases →  HPA detects high CPU/memory → adds more Pods
Load decreases → HPA detects low utilization → removes Pods

┌──────────────────────────────────────────────────────────────┐
│  HPA: target 50% CPU                                         │
│                                                              │
│  Before (1 Pod @ 90% CPU):      After (4 Pods @ 25% CPU):   │
│  ┌─────┐                        ┌─────┐ ┌─────┐            │
│  │ 90% │          ──────►       │ 25% │ │ 25% │            │
│  └─────┘                        ┌─────┐ ┌─────┐            │
│                                  │ 25% │ │ 25% │            │
│                                  └─────┘ └─────┘            │
└──────────────────────────────────────────────────────────────┘
```

### How HPA Calculates Replicas

```
desiredReplicas = ceil(currentReplicas × (currentMetricValue / desiredMetricValue))

Example: 1 Pod at 90% CPU, target is 50%
  = ceil(1 × (90 / 50))
  = ceil(1.8)
  = 2 replicas
```

---

## VPA — Scale Up/Down (More Resources Per Pod)

```
VPA observes actual usage → recommends or adjusts resource requests

┌──────────────────────────────────────────────────────────────┐
│  VPA: adjusts resource requests based on real usage          │
│                                                              │
│  Current:                       Recommended:                 │
│  ┌─────────────┐               ┌─────────────┐             │
│  │ requests:   │               │ requests:   │             │
│  │  cpu: 200m  │    ──────►    │  cpu: 400m  │             │
│  │  mem: 64Mi  │               │  mem: 200Mi │             │
│  └─────────────┘               └─────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

### VPA `updateMode` Options

| Mode | Behavior | Pod Restart? | Use Case |
|------|----------|--------------|----------|
| `"Off"` | Only generates recommendations, never changes Pods | No | Safe exploration — see what VPA suggests without risk |
| `"Initial"` | Applies recommendations only when Pods are first created | Only new Pods | Good for Jobs/CronJobs — existing Pods are untouched |
| `"Recreate"` | Evicts and recreates Pods when resources need adjustment | **Yes** (kills Pod) | When you want VPA to act, but accept downtime per Pod |
| `"Auto"` | Currently behaves like `Recreate`, will use in-place resize when available | **Yes** (for now) | Recommended mode when you want full automation |

### The Historical Problem With VPA: Pod Restarts

The biggest complaint about VPA has been: **to change resource requests, VPA had to kill and restart the Pod**. This was because the Kubernetes API treated `resources.requests` and `resources.limits` as immutable fields after Pod creation.

This meant:
- ❌ Applying a VPA recommendation caused **Pod disruption**
- ❌ For single-replica workloads, this meant **downtime**
- ❌ For stateful apps, restarts were expensive (reconnect to DB, rebuild cache)
- ❌ Users avoided `"Auto"` mode and stuck with `"Off"` just to get recommendations

### The Fix: In-Place Pod Resize (KEP-1287)

Starting with **Kubernetes 1.33** (stable), the [In-Place Pod Vertical Scaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/#in-place-resizing) feature allows changing a Pod's CPU and memory **without restarting it**:

- ✅ `resources.requests` and `resources.limits` are now **mutable** for CPU and memory
- ✅ The kubelet resizes the container's cgroup limits live
- ✅ VPA `"Auto"` mode can (once VPA integrates this) adjust resources without eviction
- ✅ No Pod disruption, no lost connections, no cache rebuilds

```bash
# You can now patch resources on a running Pod (Kubernetes 1.33+):
kubectl patch pod my-pod --subresource resize --patch \
  '{"spec":{"containers":[{"name":"app","resources":{"requests":{"cpu":"300m"},"limits":{"cpu":"500m"}}}]}}'
```

> **Status as of 2025:** In-place resize is stable in Kubernetes 1.33. The VPA project is working on integrating it so that `"Auto"` mode will use in-place resize instead of Pod eviction. Until VPA ships that integration, `"Auto"` still uses the evict-and-recreate approach.

---

## Prerequisites — Metrics Server

HPA needs real-time metrics. Most clusters require the **Metrics Server**:

```bash
# Check if metrics-server is already installed
kubectl top nodes

# If you get an error, install it:
# For Docker Desktop / minikube:
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For minikube specifically:
minikube addons enable metrics-server

# Wait ~60 seconds, then verify:
kubectl top nodes
kubectl top pods
```

> **Note:** VPA requires the [VPA components](https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler) installed separately. The HPA demo works out of the box; the VPA section shows the manifest structure and concepts.

---

## Step-by-Step Demo: HPA

### Why `registry.k8s.io/hpa-example` instead of nginx?

Nginx is extremely efficient — even under heavy HTTP traffic it barely uses CPU. To actually trigger HPA scaling, we need a container that **does real computation** per request. The `hpa-example` image is the official Kubernetes test image that runs a CPU-intensive `sqrt()` loop on every request. This guarantees the CPU spike that triggers scaling.

### 1. Deploy the app with resource requests

```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

Resource requests are **required** for HPA to work — it measures utilization as a percentage of requests.

### 2. Verify Pods are running

```bash
kubectl get pods
kubectl top pods    # might show <unknown> for ~30 seconds
```

### 3. Create the HPA

```bash
kubectl apply -f hpa.yaml
```

### 4. Inspect the HPA

```bash
kubectl get hpa

# Detailed view
kubectl describe hpa php-apache-hpa
```

You'll see `<unknown>/50%` for the first ~15-30 seconds until metrics populate.
Wait until it shows something like `0%/50%` before generating load.

### 5. Generate load to trigger scaling

Open **two terminals**:

**Terminal 1 — watch the HPA:**
```bash
kubectl get hpa php-apache-hpa -w
```

**Terminal 2 — start the load generator:**
```bash
kubectl apply -f load-generator.yaml
```

### 6. Watch the HPA scale up

Within ~30-60 seconds you should see CPU rise above 50% and replicas increase:

```bash
# Terminal 1 output will look like:
# NAME              REFERENCE              TARGETS    MINPODS   MAXPODS   REPLICAS
# php-apache-hpa   Deployment/php-apache   250%/50%   1         10        1
# php-apache-hpa   Deployment/php-apache   250%/50%   1         10        5
# php-apache-hpa   Deployment/php-apache   48%/50%    1         10        5
```

```bash
# Check in another terminal:
kubectl get pods
kubectl top pods
```

### 7. Stop the load and watch scale-down

```bash
kubectl delete pod load-generator

# Scale-down takes ~5 minutes (stabilization window prevents flapping)
# Keep watching Terminal 1
```

### 8. Check HPA events for the full story

```bash
kubectl describe hpa php-apache-hpa
```

Look at the **Events** section — it shows every scaling decision and why.

---

## Step-by-Step Demo: VPA

### 9. Look at the VPA manifest

```bash
cat vpa.yaml
```

Key settings:
- `updateMode: "Off"` — only generates recommendations, no changes
- `minAllowed` / `maxAllowed` — guardrails so VPA doesn't set crazy values
- `controlledResources` — which resources VPA manages (cpu, memory, or both)

### 10. Apply the VPA (recommendation mode)

```bash
kubectl apply -f vpa.yaml
```

### 11. Check VPA recommendations

```bash
# Might take 1-2 minutes to generate recommendations
kubectl describe vpa php-apache-vpa
```

After running under load, VPA will show:
```
Recommendation:
  Container Recommendations:
    Container Name: php-apache
    Lower Bound:    Cpu: 100m,  Memory: 50Mi
    Target:         Cpu: 400m,  Memory: 150Mi    ← "Use this"
    Upper Bound:    Cpu: 800m,  Memory: 300Mi
    Uncapped Target: Cpu: 400m, Memory: 150Mi
```

**What the bounds mean:**
- **Lower Bound** — minimum the container needs to not be starved
- **Target** — the recommended value (what VPA would set in Auto mode)
- **Upper Bound** — the peak the container might need under burst
- **Uncapped Target** — what VPA would recommend if you had no min/max guardrails

### 12. What would happen in "Auto" mode?

If you set `updateMode: "Auto"`:
1. VPA compares current requests vs. its target recommendation
2. If they differ significantly, VPA **evicts** the Pod
3. The Pod is recreated by the Deployment with the **new resource requests**
4. On Kubernetes 1.33+ (once VPA integrates it), this will happen **in-place** without restart

---

## HPA vs VPA — When to Use Which

| | HPA | VPA |
|---|-----|-----|
| **Scales** | Number of Pods (horizontal) | Resources per Pod (vertical) |
| **Best for** | Stateless apps (web servers, APIs) | Stateful/single-instance apps, right-sizing |
| **Requires** | Resource requests + Metrics Server | VPA controller installed |
| **Speed** | Scales in ~15-30 seconds | Requires Pod restart (until in-place resize) |
| **Risk** | Low — just adds/removes Pods | Medium — restarts Pods (in Recreate/Auto mode) |
| **Use together?** | ⚠️ Don't scale both on the same metric | See below |

### Can you combine HPA + VPA?

Yes, but carefully:
- ✅ HPA on a **custom metric** (requests/sec) + VPA on CPU/memory — no conflict
- ✅ VPA in `"Off"` mode (recommendations only) + HPA doing the actual scaling
- ❌ Both on CPU — they'll fight (HPA adds Pods, VPA says "give each Pod more CPU")

---

## KEDA — Event-Driven Autoscaling

[**KEDA**](https://keda.sh) (Kubernetes Event-Driven Autoscaling) extends HPA to scale based on **external event sources**, not just CPU/memory.

### Why KEDA?

HPA is limited to metrics available in the Metrics Server (CPU, memory, or custom metrics you expose yourself). Real apps need to scale based on:
- 📬 Messages in a queue (SQS, RabbitMQ, Kafka consumer lag)
- 📊 Database connections or query load
- ☁️ Cloud metrics (CloudWatch, Azure Monitor, Datadog)
- 🕐 Cron schedules (scale up before peak hours)
- 🌐 HTTP request rate from an ingress

### How KEDA Works

```
┌─────────────────────────────────────────────────────────────────┐
│                         KEDA Architecture                        │
│                                                                  │
│  External Source         KEDA                    Kubernetes       │
│  ──────────────         ──────                   ──────────      │
│  │ SQS Queue   │        │ ScaledObject │         │ HPA      │   │
│  │ Kafka Topic │  ───►  │ (defines     │  ───►   │ (scales  │   │
│  │ Cron        │        │  triggers)   │         │  Pods)   │   │
│  │ Prometheus  │        │              │         │          │   │
│  └─────────────┘        └──────────────┘         └──────────┘   │
│                                                                  │
│  KEDA can even scale to ZERO (HPA cannot — min is 1)            │
└─────────────────────────────────────────────────────────────────┘
```

### KEDA Example — Scale on SQS Queue Depth

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: sqs-scaler
spec:
  scaleTargetRef:
    name: order-processor     # Deployment to scale
  minReplicaCount: 0          # Scale to zero when queue is empty!
  maxReplicaCount: 20
  triggers:
    - type: aws-sqs-queue
      metadata:
        queueURL: https://sqs.us-east-1.amazonaws.com/123456789/orders
        queueLength: "5"      # 1 Pod per 5 messages
        awsRegion: us-east-1
```

### KEDA vs HPA

| | HPA | KEDA |
|---|-----|------|
| **Metrics source** | CPU, memory, custom metrics API | 60+ external sources (SQS, Kafka, Cron, etc.) |
| **Scale to zero** | ❌ No (minimum 1 Pod) | ✅ Yes |
| **Install** | Built-in | Requires installing KEDA operator |
| **Relationship** | Standalone | KEDA **creates and manages HPA objects** under the hood |
| **Best for** | CPU/memory-bound workloads | Event-driven, queue-based, scheduled workloads |

### Installing KEDA (reference)

```bash
# Using Helm
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace

# Or using kubectl
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.16.1/keda-2.16.1.yaml
```

> KEDA is not included in this hands-on demo since it requires external event sources, but understanding where it fits in the scaling story is important.

---

## Clean Up

```bash
kubectl delete -f load-generator.yaml 2>/dev/null
kubectl delete -f hpa.yaml
kubectl delete -f vpa.yaml
kubectl delete -f service.yaml
kubectl delete -f deployment.yaml
```

---

## Key Takeaways

- **HPA** scales Pod count based on CPU, memory, or custom metrics
- **VPA** adjusts resource requests/limits based on actual usage patterns
- HPA **requires** resource requests and a working Metrics Server
- VPA has four modes: `Off` (recommend), `Initial` (new Pods only), `Recreate` (evict), `Auto` (evict, future: in-place)
- The **historical pain** of VPA was forced Pod restarts — **Kubernetes 1.33 fixes this** with in-place Pod resize
- Don't use HPA and VPA on the **same metric** — they'll conflict
- **KEDA** extends HPA to scale on external events (queues, cron, cloud metrics) and can scale to zero
- Scale-up is fast (~15-30s); scale-down has a **5-minute stabilization window** to prevent flapping

## What's Next?

We can scale workloads automatically, but who's allowed to do what in the cluster? → Demo 12 (RBAC)
