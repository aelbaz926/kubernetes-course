# Demo 6: Namespaces

## Concept

A **Namespace** is a virtual cluster inside your physical cluster. It provides a way to divide cluster resources between multiple users, teams, or projects.

### The Problem it Solves

Without Namespaces:
- ❌ All resources live in one big pool — naming collisions everywhere
- ❌ No way to isolate teams from each other
- ❌ No way to apply resource quotas per team/project
- ❌ Permissions are all-or-nothing across the cluster

With Namespaces:
- ✅ **Isolation** — teams work in their own space without stepping on each other
- ✅ **Organization** — group related resources logically (dev, staging, prod)
- ✅ **Resource quotas** — limit CPU/memory per namespace
- ✅ **Access control** — restrict who can do what in each namespace

### Default Namespaces

Every cluster comes with these built-in namespaces:

| Namespace | Purpose |
|-----------|---------|
| `default` | Where your resources go if you don't specify a namespace |
| `kube-system` | Kubernetes system components (DNS, scheduler, etc.) |
| `kube-public` | Publicly readable resources (rarely used) |
| `kube-node-lease` | Node heartbeat tracking |

---

## Step-by-Step Demo

### 1. List existing namespaces

```bash
kubectl get namespaces
```

You'll see the default namespaces that come with every cluster.

### 2. See what's running in kube-system

```bash
# These are the Kubernetes internals
kubectl get pods -n kube-system
```

### 3. Create namespaces for different teams

```bash
kubectl apply -f namespaces.yaml
```

### 4. Deploy the same app in different namespaces

```bash
# Deploy to team-frontend namespace
kubectl apply -f app-frontend.yaml

# Deploy to team-backend namespace
kubectl apply -f app-backend.yaml
```

### 5. List Pods — namespace scoping

```bash
# Default namespace — nothing here
kubectl get pods

# Team frontend namespace
kubectl get pods -n team-frontend

# Team backend namespace
kubectl get pods -n team-backend

# ALL namespaces at once
kubectl get pods --all-namespaces
# or shorter:
kubectl get pods -A
```

### 6. Same name, different namespaces — no collision!

```bash
# Both namespaces have a Pod named with "web-app" but they don't conflict
kubectl get deployments -n team-frontend
kubectl get deployments -n team-backend
```

### 7. Apply a ResourceQuota to limit a namespace

```bash
kubectl apply -f resource-quota.yaml

# Check the quota
kubectl describe resourcequota team-frontend-quota -n team-frontend
```

### 8. Try to exceed the quota

```bash
# Scale up beyond the quota's Pod limit
kubectl scale deployment web-app -n team-frontend --replicas=10

# Check what happened
kubectl get deployment web-app -n team-frontend
kubectl describe deployment web-app -n team-frontend
```

Some Pods won't be created because they would exceed the quota!

### 9. Set a default namespace (so you don't type -n every time)

```bash
# Set team-frontend as your default context namespace
kubectl config set-context --current --namespace=team-frontend

# Now this shows team-frontend Pods
kubectl get pods

# Reset back to default
kubectl config set-context --current --namespace=default
```

### 10. Clean up

```bash
kubectl delete namespace team-frontend
kubectl delete namespace team-backend
```

Deleting a namespace deletes **everything** inside it!

---

## Key Takeaways

- Namespaces provide **logical isolation** within a cluster
- Resources in different namespaces can have the **same name** without conflict
- Use `-n <namespace>` to target a specific namespace, or `-A` for all
- **ResourceQuotas** can limit how much CPU/memory/Pods a namespace can use
- Deleting a namespace deletes **all resources** inside it
- Most resources are namespace-scoped, but some (like Nodes, PersistentVolumes) are **cluster-scoped**

## What's Next?

We can deploy Pods and organize them into namespaces, but how do Pods **talk to each other**? How does external traffic reach our Pods? → Demo 7 (Services)
