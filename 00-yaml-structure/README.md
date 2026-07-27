# Kubernetes YAML Structure — The 4 Required Fields

Every Kubernetes object is defined using a YAML manifest with **4 top-level fields**:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
    - name: nginx
      image: nginx:1.27
```

---

## 1. `apiVersion`

**What is it?** The version of the Kubernetes API you're using to create this object.

**Why does it matter?** Kubernetes evolves over time. Different objects belong to different API groups and versions. This tells Kubernetes which schema to use when validating your YAML.

| Object | apiVersion |
|--------|-----------|
| Pod | `v1` |
| Service | `v1` |
| ConfigMap | `v1` |
| ReplicaSet | `apps/v1` |
| Deployment | `apps/v1` |
| Ingress | `networking.k8s.io/v1` |

**How to find the correct apiVersion:**

```bash
# List all available API resources and their versions
kubectl api-resources
```

---

## 2. `kind`

**What is it?** The type of Kubernetes object you want to create.

**Why does it matter?** It tells Kubernetes what you're declaring — a Pod, a Deployment, a Service, etc.

**Examples:**

```yaml
kind: Pod
kind: ReplicaSet
kind: Deployment
kind: Service
kind: ConfigMap
kind: Secret
```

> Think of `kind` as the **class** and the object you create as an **instance** of that class.

---

## 3. `metadata`

**What is it?** Data that uniquely identifies the object — its name, namespace, labels, and annotations.

**Common fields inside metadata:**

| Field | Description | Required? |
|-------|-------------|-----------|
| `name` | Unique name within the namespace | ✅ Yes |
| `namespace` | Which namespace it belongs to (default: `default`) | No |
| `labels` | Key-value pairs for organizing and selecting | No (but highly recommended) |
| `annotations` | Key-value pairs for non-identifying metadata | No |

**Example:**

```yaml
metadata:
  name: web-app-pod
  namespace: production
  labels:
    app: web-app
    tier: frontend
    env: production
  annotations:
    description: "Main frontend pod for the web application"
```

**Key difference — Labels vs Annotations:**
- **Labels** → used to **select** and **group** objects (ReplicaSet uses them!)
- **Annotations** → used to store **extra info** (not used for selection)

---

## 4. `spec`

**What is it?** The **desired state** — what you want this object to look like and how it should behave.

**Why does it matter?** This is where you define the actual configuration. The spec is **different for every `kind`**.

### Pod spec:

```yaml
spec:
  containers:
    - name: nginx
      image: nginx:1.27
      ports:
        - containerPort: 80
```

### ReplicaSet spec:

```yaml
spec:
  replicas: 3                    # How many Pods
  selector:                      # Which Pods to manage (using labels)
    matchLabels:
      app: web-app
  template:                      # Pod template (what each replica looks like)
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
```

### Deployment spec:

```yaml
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  strategy:                      # How to handle updates
    type: RollingUpdate
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
```

---

## Putting It All Together

```yaml
apiVersion: apps/v1          # ← Which API version?
kind: Deployment             # ← What type of object?
metadata:                    # ← Who is this object?
  name: web-app-deploy
  labels:
    app: web-app
spec:                        # ← What should it look like?
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
```

---

## Quick Reference

| Field | Answers the Question | Same across all objects? |
|-------|---------------------|------------------------|
| `apiVersion` | "Which API version am I using?" | No (depends on the kind) |
| `kind` | "What type of object is this?" | — |
| `metadata` | "What is its identity?" | Same structure for all |
| `spec` | "What is the desired state?" | No (different per kind) |

---

## Helpful Commands

```bash
# Find the apiVersion for any resource
kubectl api-resources | grep Deployment

# See the full spec structure for any object
kubectl explain pod.spec
kubectl explain deployment.spec
kubectl explain replicaset.spec

# Drill deeper
kubectl explain pod.spec.containers
kubectl explain deployment.spec.strategy
```
