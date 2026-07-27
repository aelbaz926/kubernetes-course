# Demo 2: Multi-Container Pods

## Concept

Sometimes containers need to work **tightly together** — they share data, communicate over localhost, or one supports the other. This is when you put multiple containers in the **same Pod**.

Containers in the same Pod share:
- ✅ Network namespace (same IP, communicate via `localhost`)
- ✅ Storage volumes
- ✅ Lifecycle (they start and stop together)

## Common Multi-Container Patterns

| Pattern | Description | Example |
|---------|-------------|---------|
| **Sidecar** | Helper container that enhances the main container | Log shipper, proxy |
| **Ambassador** | Proxy that simplifies external connections | Local proxy to a DB |
| **Adapter** | Transforms output of the main container | Format converter |

---

## Step-by-Step Demo

### 1. Create the multi-container Pod

```bash
kubectl apply -f sidecar-pod.yaml
```

This creates a Pod with:
- **Main container** (`app`): A simple app that writes logs to a shared volume
- **Sidecar container** (`log-sidecar`): Reads and displays those logs

### 2. Verify both containers are running

```bash
kubectl get pods
```

Expected output:
```
NAME          READY   STATUS    RESTARTS   AGE
sidecar-pod   2/2     Running   0          10s
```

Notice `2/2` — both containers are ready!

### 3. See the main app writing logs

```bash
kubectl logs sidecar-pod -c app
```

### 4. See the sidecar reading the same logs

```bash
kubectl logs sidecar-pod -c log-sidecar
```

Both containers see the **same file** because they share a volume!

### 5. Prove they share the same network (localhost)

```bash
kubectl apply -f shared-network-pod.yaml
```

```bash
# The busybox container can reach nginx via localhost
kubectl exec shared-network-pod -c busybox -- wget -qO- http://localhost
```

This works because both containers share the **same network namespace**.

### 6. Clean up

```bash
kubectl delete -f sidecar-pod.yaml
kubectl delete -f shared-network-pod.yaml
```

---

## Key Takeaways

- Multi-container Pods share network (localhost) and storage (volumes)
- Use multi-container Pods when containers are **tightly coupled**
- If containers can run independently → use separate Pods
- The sidecar pattern is the most common multi-container pattern

## What's Next?

Now we have Pods. But how does Kubernetes **organize** and **select** them? → Demo 3 (Labels & Selectors)
