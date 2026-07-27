# Demo 1: Containers & Pods (Single Container)

## Concept

A **Pod** is the smallest deployable unit in Kubernetes. It wraps one or more containers, but the most common pattern is **one container per Pod**.

Think of it this way:
- Docker runs **containers**
- Kubernetes runs **Pods** (which contain containers)

## Why not just run containers directly?

Kubernetes adds a layer (the Pod) because:
- Pods get their own IP address
- Pods can be scheduled, scaled, and managed as a unit
- Pods provide shared networking and storage for their containers

---

## Step-by-Step Demo

### 1. Create the Pod

```bash
kubectl apply -f pod.yaml
```

### 2. Verify the Pod is running

```bash
kubectl get pods
```

Expected output:
```
NAME        READY   STATUS    RESTARTS   AGE
nginx-pod   1/1     Running   0          10s
```

### 3. Inspect the Pod details

```bash
kubectl describe pod nginx-pod
```

Notice:
- The Pod has its own IP address
- It has one container (`nginx-container`)
- Events show the scheduling and startup process

### 4. Access the container inside the Pod

```bash
# Execute a command inside the container
kubectl exec nginx-pod -- curl localhost
```

### 5. View logs from the container

```bash
kubectl logs nginx-pod
```

### 6. Port-forward to access from your machine

```bash
kubectl port-forward pod/nginx-pod 8080:80
# Visit http://localhost:8080 in your browser
```

### 7. Clean up

```bash
kubectl delete -f pod.yaml
```

---

## Key Takeaways

- A Pod is a wrapper around container(s)
- One container per Pod is the most common pattern
- Pods get their own IP, lifecycle, and identity in the cluster
- This is the **building block** for everything else in Kubernetes

## What's Next?

But what if containers need to work together closely? → Demo 2 (Multi-Container Pods)
