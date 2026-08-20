# Startup Probe Demo

## What is a Startup Probe?

A startup probe checks if the application **has started successfully**. It runs once during container startup, and **disables liveness and readiness probes until it succeeds**.

### When to Use
- Application takes a long time to initialize (Java apps, large databases)
- Loading large datasets into memory
- Establishing many connections (connection pools, service mesh)

### Key Behavior
- Runs **only during startup** (not ongoing like liveness/readiness)
- **Disables** liveness and readiness probes until it passes
- On failure (after threshold): Container is **killed and restarted**
- Once successful: **Never runs again** — liveness/readiness take over

---

## The Problem It Solves

Without a startup probe:

```yaml
# ❌ PROBLEM: App takes 30s to start, but liveness kills it at 15s!
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10   # Only waits 10s
  periodSeconds: 5
  failureThreshold: 3       # Kills at 10 + (3×5) = 25s — too early!
```

With a startup probe:

```yaml
# ✅ SOLUTION: Startup probe gives it 50s to start
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  periodSeconds: 5
  failureThreshold: 10      # 10 × 5 = 50s to start

# Liveness only starts AFTER startup succeeds
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  periodSeconds: 10
```

---

## Demo Application

The app simulates a slow-starting application (30-second startup delay):
- `GET /` — Returns app status and uptime
- `GET /startup` — Returns 503 during startup, 200 after 30 seconds

---

## Step-by-Step Demo

### 1. Deploy the slow-starting application

```bash
kubectl apply -f deployment.yaml

# Immediately check pod status
kubectl get pods -l app=startup-demo
# Pod is Running but NOT Ready (0/1)
```

### 2. Watch the startup process

```bash
# Watch pod events in real-time
kubectl get pods -l app=startup-demo -w
```

You'll see:
```
NAME                           READY   STATUS    RESTARTS   AGE
startup-demo-xxxxx-xxxxx       0/1     Running   0          5s    ← Starting...
startup-demo-xxxxx-xxxxx       0/1     Running   0          15s   ← Still starting...
startup-demo-xxxxx-xxxxx       0/1     Running   0          30s   ← Still starting...
startup-demo-xxxxx-xxxxx       1/1     Running   0          35s   ← Ready!
```

### 3. Check the events during startup

```bash
kubectl describe pod -l app=startup-demo
```

Events show:
```
Events:
  Warning  Unhealthy  Startup probe failed: HTTP probe failed with statuscode: 503
  Warning  Unhealthy  Startup probe failed: HTTP probe failed with statuscode: 503
  Warning  Unhealthy  Startup probe failed: HTTP probe failed with statuscode: 503
  ...
  # After ~30 seconds, probe succeeds and pod becomes Ready
```

### 4. Verify the app is working after startup

```bash
kubectl port-forward svc/startup-demo 8080:80 &
curl http://localhost:8080/
# Response: "App running! Uptime: Xs"
```

### 5. Understand the timing

```yaml
startupProbe:
  initialDelaySeconds: 5    # Wait 5s before first check
  periodSeconds: 5          # Check every 5s
  failureThreshold: 10      # Allow 10 failures = 5 + (10×5) = 55 seconds max
```

**Timeline:**
```
0s   — Container starts, app begins 30s initialization
5s   — First probe: FAIL (app still starting) — 1/10
10s  — Probe: FAIL (still starting) — 2/10
15s  — Probe: FAIL (still starting) — 3/10
20s  — Probe: FAIL (still starting) — 4/10
25s  — Probe: FAIL (still starting) — 5/10
30s  — Probe: FAIL (still starting) — 6/10
35s  — Probe: SUCCESS! ✅ — App is started
       → Liveness/readiness probes now activate
```

If the app took longer than 55 seconds, the container would be killed and restarted.

---

## Startup Probe vs Large initialDelaySeconds

Why not just use a large `initialDelaySeconds` on the liveness probe?

```yaml
# ❌ BAD: 60s delay means deadlocks go undetected for 60s on every restart
livenessProbe:
  initialDelaySeconds: 60   # Wastes time on subsequent restarts

# ✅ GOOD: Startup probe only affects first boot
startupProbe:
  failureThreshold: 12
  periodSeconds: 5          # 60s max for startup

livenessProbe:
  periodSeconds: 10         # Fast detection after startup
```

**Startup probe advantage**: After the first successful startup, liveness kicks in immediately on subsequent health issues.

---

## Clean Up

```bash
kill %1 2>/dev/null  # Stop port-forward
kubectl delete -f deployment.yaml
```

## Key Takeaways

- Startup probes protect **slow-starting apps** from premature liveness kills
- Set `failureThreshold × periodSeconds` > actual startup time
- Once startup succeeds, it **never runs again**
- Liveness and readiness probes are **disabled** until startup passes
- Better than large `initialDelaySeconds` because it doesn't slow down runtime detection
