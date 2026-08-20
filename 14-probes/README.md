# Demo 14: Kubernetes Probes (Health Checks)

## Concept

**Probes** are health checks that the kubelet uses to determine the state of containers. They help Kubernetes make intelligent decisions about traffic routing, container restarts, and pod lifecycle management.

### The Problem Without Probes

Imagine deploying a web application that:
- Takes 30 seconds to initialize database connections
- Occasionally becomes unresponsive due to memory leaks
- Sometimes enters a deadlock state but the process keeps running

**Without probes:**
- ❌ Kubernetes sends traffic immediately after container starts → users get errors
- ❌ Unresponsive containers stay in service → users experience timeouts
- ❌ Deadlocked containers never restart → manual intervention required
- ❌ Failed containers might be marked "Running" even when broken

**With probes:**
- ✅ **Startup probe** — wait for app to fully initialize before serving traffic
- ✅ **Liveness probe** — detect deadlocks and auto-restart the container
- ✅ **Readiness probe** — temporarily remove pod from service during issues

### Three Types of Probes

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PROBE LIFECYCLE                                  │
│                                                                      │
│  Container    Startup Probe     Liveness Probe    Readiness Probe    │
│  Start ──────► (runs first) ──► (ongoing)         (ongoing)          │
│                                                                      │
│  Phase 1:     "Has the app      "Is the app       "Can the app      │
│               finished           still alive?"      serve traffic?"   │
│               starting?"                                             │
│                                                                      │
│  On Fail:     Kill & restart    Kill & restart    Remove from        │
│               container         container         Service endpoints  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

| Probe Type | Purpose | On Failure | Use When |
|------------|---------|------------|----------|
| **Startup** | Has the app started? | Kill & restart | Slow-starting apps |
| **Liveness** | Is the app alive? | Kill & restart | App can deadlock/hang |
| **Readiness** | Can the app serve traffic? | Remove from Service | Temporary dependency issues |

### Probe Check Mechanisms

```yaml
# 1. HTTP GET — for web apps and REST APIs
httpGet:
  path: /health
  port: 8080

# 2. TCP Socket — for databases, message queues
tcpSocket:
  port: 3306

# 3. Exec Command — for custom checks
exec:
  command: ["cat", "/tmp/healthy"]
```

### Configuration Parameters

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 10    # Wait before first probe
  periodSeconds: 5           # How often to check
  timeoutSeconds: 3          # Probe timeout
  successThreshold: 1        # Consecutive successes to be "healthy"
  failureThreshold: 3        # Consecutive failures before action
```

---

## Demo Structure

```
14-probes/
├── liveness-probe/     # Detects deadlocks → restarts container
├── readiness-probe/    # Manages traffic during dependency issues
└── startup-probe/      # Handles slow application startup
```

### Recommended Order

1. **liveness-probe** — Understand container restart on failure
2. **readiness-probe** — Understand traffic management
3. **startup-probe** — Understand startup protection

---

## Quick Reference

| Scenario | Probe Type | What Happens |
|----------|-----------|--------------|
| App deadlocks | Liveness | Container killed & restarted |
| Database goes down | Readiness | Pod removed from Service (no restart) |
| App takes 60s to start | Startup | Liveness/readiness probes wait until startup succeeds |
| App returns 500 errors | Readiness | Pod removed from Service until healthy |

## Key Takeaways

- **Liveness** = "Is it alive?" → Restart on failure (for permanent issues)
- **Readiness** = "Can it serve?" → Remove from service on failure (for temporary issues)
- **Startup** = "Is it started?" → Protect slow apps from premature liveness kills
- Always use **readiness** for dependency checks (DB, cache, etc.)
- Never use **liveness** for temporary issues — it causes unnecessary restarts
- Combine all three for complete health management
