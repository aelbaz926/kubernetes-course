# Demo 4: ReplicaSet

## Concept

A **ReplicaSet** ensures that a specified number of Pod replicas are running at any given time.

### The Problem it Solves

With standalone Pods:
- ❌ If a Pod crashes, nobody restarts it
- ❌ If you need 3 copies for high availability, you manage each manually
- ❌ If you want to scale up/down, you create/delete Pods one by one

With a ReplicaSet:
- ✅ Self-healing: crashed Pods are automatically replaced
- ✅ Desired state: you declare "I want 3 replicas" and Kubernetes ensures it
- ✅ Scaling: just change the replica count

### How does it know which Pods to manage?

**Labels and Selectors!** (from Demo 3)

The ReplicaSet uses a `selector` to find Pods with matching labels. If there are fewer Pods than desired, it creates new ones. If there are more, it deletes extras.

---

## Step-by-Step Demo

### 1. First, let's see the problem with standalone Pods

```bash
# Create a standalone Pod
kubectl apply -f standalone-pod.yaml

# Verify it's running
kubectl get pods

# Delete it (simulating a crash)
kubectl delete pod standalone-nginx

# Check again — it's gone forever!
kubectl get pods
```

Nobody brought it back. That's the problem.

### 2. Now create a ReplicaSet

```bash
kubectl apply -f replicaset.yaml
```

### 3. Verify the ReplicaSet and its Pods

```bash
# Check the ReplicaSet
kubectl get replicaset

# Check the Pods it created
kubectl get pods --show-labels
```

Notice: 3 Pods are running, all with the label `app: web-app`.

### 4. Self-healing: Delete a Pod and watch it come back

```bash
# Delete one Pod
kubectl delete pod <pod-name>

# Immediately check — a new one is created!
kubectl get pods
```

The ReplicaSet detected one Pod is missing and created a replacement.

### 5. Scaling: Change the number of replicas

```bash
# Scale up to 5 replicas
kubectl scale replicaset web-app-rs --replicas=5
kubectl get pods

# Scale down to 2 replicas
kubectl scale replicaset web-app-rs --replicas=2
kubectl get pods
```

### 6. Show the selector-label connection

```bash
# The ReplicaSet selects Pods with these labels
kubectl describe replicaset web-app-rs | grep -A 3 "Selector"

# Create a Pod manually with the SAME labels
kubectl apply -f adopted-pod.yaml

# Check Pods — the ReplicaSet sees 3 Pods but only wants 2!
# It will TERMINATE the extra one
kubectl get pods
```

### 7. Clean up

```bash
kubectl delete -f replicaset.yaml
kubectl delete -f standalone-pod.yaml --ignore-not-found
kubectl delete -f adopted-pod.yaml --ignore-not-found
```

---

## Key Takeaways

- ReplicaSet maintains a **desired number** of Pod replicas
- It uses **label selectors** to identify which Pods it manages
- It provides **self-healing** — crashed Pods are replaced automatically
- It can **adopt** existing Pods if their labels match
- You should **NOT** use ReplicaSet directly in production — use **Deployments** instead

## What's Next?

ReplicaSet handles replicas, but what about **updates**? How do you roll out a new version of your app without downtime? → Demo 5 (Deployment)
