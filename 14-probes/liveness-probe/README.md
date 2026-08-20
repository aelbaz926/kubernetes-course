# Liveness Probe Demo

## What is a Liveness Probe?

A liveness probe determines if a container is **still running properly**. If the probe fails, Kubernetes **kills the container and restarts it**.

### When to Use
- Application can enter a deadlock state
- Application has memory leaks that make it unresponsive
- Process is running but can't serve requests

### Key Behavior
- Runs **periodically throughout the container's lifetime**
- On failure: Container is **killed and restarted**
- Use for: **Permanent, unrecoverable** failures

---

## Demo Application

The app has these endpoints:
- `GET /` — Returns app status and uptime
- `GET /health` — Health check endpoint (200 if healthy, 500 if broken)
- `GET /break` — Simulates a deadlock (makes /health return 500)
- `GET /fix` — Recovers the app (makes /health return 200 again)

---

## Step-by-Step Demo

### 1. Deploy the application

```bash
kubectl apply -f deployment.yaml

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app=liveness-demo --timeout=60s

# Check pod is running
kubectl get pods -l app=liveness-demo
```

### 2. Test the healthy application

```bash
# Port-forward to access the app
kubectl port-forward svc/liveness-demo 8080:80 &

# Test the app
curl http://localhost:8080/
# Response: "App healthy! Uptime: Xs"

# Test the health endpoint
curl http://localhost:8080/health
# Response: "OK" (HTTP 200)
```

### 3. Break the application (simulate deadlock)

```bash
# This simulates the app entering a deadlock state
curl http://localhost:8080/break
# Response: "Application is now broken! Liveness probe will fail."

# Health endpoint now returns 500
curl http://localhost:8080/health
# Response: "Unhealthy" (HTTP 500)
```

### 4. Watch Kubernetes detect and restart the container

```bash
# Stop port-forward first
kill %1 2>/dev/null

# Watch the pod — it will restart after ~15 seconds (3 failures × 5s period)
kubectl get pods -l app=liveness-demo -w
```

You'll see:
```
NAME                             READY   STATUS    RESTARTS   AGE
liveness-demo-xxxxx-xxxxx        1/1     Running   0          2m
liveness-demo-xxxxx-xxxxx        1/1     Running   1          2m30s  ← RESTARTED!
```

### 5. Check the events

```bash
kubectl describe pod -l app=liveness-demo
```

Look for events like:
```
Events:
  Warning  Unhealthy  Liveness probe failed: HTTP probe failed with statuscode: 500
  Normal   Killing    Container app failed liveness probe, will be restarted
  Normal   Started    Started container app
```

### 6. Verify the app is healthy again after restart

```bash
kubectl port-forward svc/liveness-demo 8080:80 &
curl http://localhost:8080/
# Response: "App healthy! Uptime: Xs" (uptime reset = container was restarted)

# Check restart count
kubectl get pods -l app=liveness-demo
# RESTARTS column shows 1+
```

---

## Understanding the Probe Configuration

```yaml
livenessProbe:
  httpGet:
    path: /health           # Endpoint to check
    port: 8080              # Port to check on
  initialDelaySeconds: 10   # Wait 10s before first check (let app start)
  periodSeconds: 5          # Check every 5 seconds
  failureThreshold: 3       # Kill after 3 consecutive failures (15s total)
```

**Timeline when app breaks:**
```
0s  — /break called, app enters deadlock
5s  — Probe check: FAIL (1/3)
10s — Probe check: FAIL (2/3)
15s — Probe check: FAIL (3/3) → KILL & RESTART
16s — New container starts fresh and healthy
```

---

## Common Mistake: Using Liveness for Temporary Issues

```yaml
# ❌ BAD: Database outage will cause unnecessary restarts
livenessProbe:
  httpGet:
    path: /db-check    # Fails when DB is down
    port: 8080

# ✅ GOOD: Use readiness probe for dependency issues
readinessProbe:
  httpGet:
    path: /db-check    # Removes from service, no restart
    port: 8080
```

---

## Clean Up

```bash
kill %1 2>/dev/null  # Stop port-forward
kubectl delete -f deployment.yaml
```

## Key Takeaways

- Liveness probes detect **permanent, unrecoverable** failures
- Failed liveness probe = **container restart**
- Don't use for temporary issues (use readiness instead)
- Set `initialDelaySeconds` to give the app time to start
- Monitor `RESTARTS` column: high counts = application problem, not probe problem
