# Demo 5: Deployment

## Concept

A **Deployment** is the recommended way to manage Pods in production. It wraps a ReplicaSet and adds:

- ✅ **Rolling updates** — update your app without downtime
- ✅ **Rollback** — undo a bad update instantly
- ✅ **Version history** — track what changed and when
- ✅ **Declarative updates** — just change the spec, Kubernetes handles the rest

### The Hierarchy

```
Deployment
  └── manages → ReplicaSet (current version)
                  └── manages → Pods (replicas)
```

When you update a Deployment, it:
1. Creates a **new ReplicaSet** with the updated Pod template
2. Gradually scales up the new ReplicaSet
3. Gradually scales down the old ReplicaSet
4. Result: zero-downtime rolling update!

---

## Step-by-Step Demo

### 1. Create a Deployment

```bash
kubectl apply -f deployment.yaml
```

### 2. Verify the Deployment, ReplicaSet, and Pods

```bash
# Check the Deployment
kubectl get deployment

# Check the ReplicaSet it created
kubectl get replicaset

# Check the Pods
kubectl get pods --show-labels
```

Notice: Deployment → created a ReplicaSet → created 3 Pods.

### 3. Show the relationship

```bash
kubectl describe deployment web-app-deploy | grep -A 5 "NewReplicaSet"
```

### 4. Rolling Update — change the image version

```bash
# Update from nginx:1.27 to nginx:1.27-alpine
kubectl set image deployment/web-app-deploy nginx=nginx:1.27-alpine

# Watch the rollout in real-time
kubectl rollout status deployment/web-app-deploy
```

### 5. Observe what happened under the hood

```bash
# Two ReplicaSets now exist!
kubectl get replicaset

# Old one scaled to 0, new one scaled to 3
# Pods are running the new image
kubectl get pods -o wide
```

### 6. Check rollout history

```bash
kubectl rollout history deployment/web-app-deploy
```

### 7. Rollback — undo the last update

```bash
# Oh no, the new version has a bug! Roll back!
kubectl rollout undo deployment/web-app-deploy

# Verify it rolled back
kubectl rollout status deployment/web-app-deploy
kubectl get replicaset
```

The old ReplicaSet is scaled back up, the new one scaled down!

### 8. Declarative update (edit the YAML)

```bash
# Apply the updated version
kubectl apply -f deployment-v2.yaml

# Watch the rollout
kubectl rollout status deployment/web-app-deploy
```

### 9. Scale the Deployment

```bash
kubectl scale deployment web-app-deploy --replicas=5
kubectl get pods
```

### 10. Clean up

```bash
kubectl delete -f deployment.yaml
```

---

## Key Takeaways

- **Deployment** is the standard way to run stateless apps in Kubernetes
- It manages ReplicaSets, which manage Pods
- Rolling updates happen automatically when you change the Pod template
- You can **rollback** to any previous version instantly
- Always use Deployments instead of ReplicaSets directly

## Summary: The Full Picture

```
┌─────────────────────────────────────────────────────┐
│                    DEPLOYMENT                         │
│  (manages rolling updates & rollbacks)               │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │              REPLICASET                        │   │
│  │  (ensures desired replica count)              │   │
│  │  (uses LABELS/SELECTORS to find Pods)         │   │
│  │                                               │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐      │   │
│  │  │   POD   │  │   POD   │  │   POD   │      │   │
│  │  │┌───────┐│  │┌───────┐│  │┌───────┐│      │   │
│  │  ││Container│  ││Container│  ││Container│      │   │
│  │  │└───────┘│  │└───────┘│  │└───────┘│      │   │
│  │  └─────────┘  └─────────┘  └─────────┘      │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```
