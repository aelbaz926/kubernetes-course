# Demo 3: Labels & Selectors

## Concept

**Labels** are key-value pairs attached to Kubernetes objects. They are the **primary mechanism** for organizing and selecting groups of objects.

**Selectors** are queries that filter objects based on their labels.

Think of labels like **tags** on items in a store:
- You can tag items by color, size, brand
- Then filter: "show me all items where color=red AND size=large"

## Why do Labels matter?

Labels are used by:
- **ReplicaSets** → to know which Pods to manage
- **Deployments** → to know which ReplicaSets to manage
- **Services** → to know which Pods to route traffic to
- **You** → to organize and query your resources

---

## Step-by-Step Demo

### 1. Create Pods with different labels

```bash
kubectl apply -f pods-with-labels.yaml
```

This creates 4 Pods with different label combinations.

### 2. List all Pods with their labels

```bash
kubectl get pods --show-labels
```

### 3. Filter by a single label (equality-based selector)

```bash
# Get all Pods in the "frontend" tier
kubectl get pods -l tier=frontend

# Get all Pods in the "production" environment
kubectl get pods -l env=production
```

### 4. Filter by multiple labels (AND condition)

```bash
# Get Pods that are BOTH frontend AND production
kubectl get pods -l tier=frontend,env=production
```

### 5. Use set-based selectors

```bash
# Get Pods where env is either "production" or "staging"
kubectl get pods -l 'env in (production, staging)'

# Get Pods that are NOT in development
kubectl get pods -l 'env notin (development)'
```

### 6. Add a label to an existing Pod

```bash
kubectl label pod app-frontend-prod version=v1
kubectl get pod app-frontend-prod --show-labels
```

### 7. Remove a label from a Pod

```bash
kubectl label pod app-frontend-prod version-
kubectl get pod app-frontend-prod --show-labels
```

### 8. Clean up

```bash
kubectl delete -f pods-with-labels.yaml
```

---

## Key Takeaways

- Labels are key-value pairs for organizing objects
- Selectors filter objects by their labels
- Labels are NOT unique — multiple objects can share the same labels
- Labels are the **glue** between higher-level objects (ReplicaSet, Deployment, Service) and Pods
- This is how a ReplicaSet "knows" which Pods belong to it!

## What's Next?

Now that we understand how labels connect things, let's see how a ReplicaSet uses them to manage Pod replicas → Demo 4 (ReplicaSet)
