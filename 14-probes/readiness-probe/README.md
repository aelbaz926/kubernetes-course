# Readiness Probe Demo

## What is a Readiness Probe?

A readiness probe determines if a container is **ready to accept traffic**. If the probe fails, Kubernetes **removes the pod from Service endpoints** but does NOT restart it.

### When to Use
- Application depends on external services (database, cache, API)
- Application needs warm-up time after starting
- Application is temporarily overloaded

### Key Behavior
- Runs **periodically throughout the container's lifetime**
- On failure: Pod **removed from Service** (no traffic sent to it)
- On recovery: Pod **added back to Service** (traffic resumes)
- Container **keeps running** — no restart!

---

## Demo Application

The app has these endpoints:
- `GET /` — Returns status and request count
- `GET /health` — Liveness check (always 200)
- `GET /ready` — Readiness check (200 if ready, 503 if not)
- `GET /toggle-ready` — Toggle readiness state on/off

---

## Step-by-Step Demo

### 1. Deploy the application (3 replicas)

```bash
kubectl apply -f deployment.yaml

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app=readiness-demo --timeout=60s

# Check all 3 pods are ready (1/1)
kubectl get pods -l app=readiness-demo

# Check endpoints — all 3 pods should be listed
kubectl get endpoints readiness-demo
```

### 2. Send traffic to the service

```bash
# Port-forward to the service
kubectl port-forward svc/readiness-demo 8080:80 &

# Send requests — they're distributed across all 3 pods
for i in $(seq 1 6); do curl -s http://localhost:8080/ | grep requests_served; done
```

### 3. Make one pod "not ready" (simulate DB outage)

```bash
# Get one pod name
POD=$(kubectl get pods -l app=readiness-demo -o jsonpath='{.items[0].metadata.name}')
echo "Targeting pod: $POD"

# Toggle it to "not ready"
kubectl exec $POD -- curl -s http://localhost:8080/toggle-ready
# Response: "Application is now not ready"
```

### 4. Watch the pod become NotReady (but NOT restart)

```bash
# Watch pod status — it stays Running but becomes 0/1 Ready
kubectl get pods -l app=readiness-demo -w
```

You'll see:
```
NAME                              READY   STATUS    RESTARTS   AGE
readiness-demo-xxxxx-aaaaa        0/1     Running   0          3m   ← NOT READY (no restart!)
readiness-demo-xxxxx-bbbbb        1/1     Running   0          3m
readiness-demo-xxxxx-ccccc        1/1     Running   0          3m
```

### 5. Check endpoints — pod is removed from Service

```bash
# The not-ready pod is removed from endpoints
kubectl get endpoints readiness-demo
# Only 2 IPs now instead of 3!
```

### 6. Traffic now goes only to the 2 ready pods

```bash
# All requests go to the 2 healthy pods
for i in $(seq 1 6); do curl -s http://localhost:8080/ | grep requests_served; done
# No errors — traffic is automatically rerouted
```

### 7. Make the pod ready again

```bash
# Toggle it back to ready
kubectl exec $POD -- curl -s http://localhost:8080/toggle-ready
# Response: "Application is now ready"

# Pod becomes Ready again
kubectl get pods -l app=readiness-demo

# Endpoints include all 3 pods again
kubectl get endpoints readiness-demo
```

---

## Readiness vs Liveness — The Critical Difference

| | Readiness Probe | Liveness Probe |
|---|---|---|
| **Purpose** | Can it serve traffic? | Is it alive? |
| **On Failure** | Remove from Service | Kill & restart |
| **Container** | Keeps running | Gets killed |
| **Use For** | Temporary issues (DB down) | Permanent issues (deadlock) |
| **Recovery** | Automatic when probe passes again | New container starts fresh |

### When to use which?

```
Database goes down?        → READINESS (temp issue, will recover)
App deadlocks?             → LIVENESS (permanent, needs restart)
Cache is warming up?       → READINESS (will be ready soon)
Memory leak exhausted?     → LIVENESS (needs fresh start)
External API is slow?      → READINESS (don't restart, just wait)
```

---

## Understanding the Probe Configuration

```yaml
readinessProbe:
  httpGet:
    path: /ready            # Endpoint that checks dependencies
    port: 8080
  initialDelaySeconds: 5    # Wait 5s before first check
  periodSeconds: 5          # Check every 5 seconds
  failureThreshold: 4       # Remove from service after 4 failures (20s)
```

---

## Clean Up

```bash
kill %1 2>/dev/null  # Stop port-forward
kubectl delete -f deployment.yaml
```

## Key Takeaways

- Readiness probe controls **traffic routing**, not container lifecycle
- Failed readiness = **removed from Service** (container keeps running)
- Use for **temporary, recoverable** issues
- Essential for **zero-downtime deployments**
- Pod is automatically added back when probe passes again
- Combine with liveness probe for complete health management
