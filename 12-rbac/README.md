# Demo 12: RBAC (Role-Based Access Control)

## Concept

**RBAC** controls **who** can do **what** on **which resources** in your cluster. It answers:

- Can this developer view Pods in production?
- Can this CI/CD pipeline create Deployments?
- Can this microservice read Secrets?

### The Problem it Solves

Without RBAC:
- ❌ Every user/application has full cluster admin access
- ❌ A compromised Pod can read Secrets, delete Deployments, access other namespaces
- ❌ No audit trail of who did what
- ❌ No principle of least privilege

With RBAC:
- ✅ **Least privilege** — only grant what's needed
- ✅ **Isolation** — restrict access per namespace
- ✅ **Service accounts** — Pods only access what they need
- ✅ **Auditability** — clear mapping of permissions to identities

### RBAC Building Blocks

```
┌─────────────────────────────────────────────────────────────────────┐
│                         RBAC MODEL                                   │
│                                                                      │
│  WHO                    BINDING              WHAT                     │
│  ─────────────         ──────────────       ───────────────          │
│  │ ServiceAccount │     │ RoleBinding  │     │ Role         │        │
│  │ User          │ ──► │              │ ──► │  - resources │        │
│  │ Group         │     │              │     │  - verbs     │        │
│  └───────────────┘     └──────────────┘     └─────────────┘         │
│                                                                      │
│  Namespace-scoped:  ServiceAccount + RoleBinding + Role              │
│  Cluster-scoped:    ServiceAccount + ClusterRoleBinding + ClusterRole│
└─────────────────────────────────────────────────────────────────────┘
```

### Key Terms

| Term | Scope | Purpose |
|------|-------|---------|
| **Role** | Namespace | Defines permissions (what you CAN do) within a namespace |
| **ClusterRole** | Cluster-wide | Defines permissions across all namespaces |
| **RoleBinding** | Namespace | Grants a Role to a subject in a namespace |
| **ClusterRoleBinding** | Cluster-wide | Grants a ClusterRole across the entire cluster |
| **ServiceAccount** | Namespace | Identity for Pods (apps running in the cluster) |

### Common Verbs

| Verb | Meaning |
|------|---------|
| `get` | Read a specific resource by name |
| `list` | List all resources of a type |
| `watch` | Stream real-time changes |
| `create` | Create new resources |
| `update` | Modify existing resources |
| `patch` | Partially modify resources |
| `delete` | Remove resources |

---

## Step-by-Step Demo

### 1. Create a ServiceAccount

A ServiceAccount is the identity your Pod will use:

```bash
kubectl apply -f serviceaccount.yaml

# Verify
kubectl get serviceaccounts
```

### 2. Create a Role (namespace-scoped permissions)

```bash
kubectl apply -f role.yaml

# Inspect the role
kubectl describe role pod-reader
```

This role allows: `get`, `list`, `watch` Pods + `get` Pod logs — **in the default namespace only**.

### 3. Bind the Role to the ServiceAccount

```bash
kubectl apply -f rolebinding.yaml

# Verify
kubectl describe rolebinding read-pods-binding
```

Now `app-reader` ServiceAccount has permission to read Pods in the `default` namespace.

### 4. Test the permissions — deploy a Pod with the ServiceAccount

```bash
kubectl apply -f pod-rbac-test.yaml

# Wait for it to be ready
kubectl wait --for=condition=Ready pod/rbac-test --timeout=60s
```

### 5. Test ALLOWED actions (reading Pods)

```bash
# Exec into the Pod and use kubectl as the ServiceAccount
kubectl exec -it rbac-test -- kubectl get pods
```

✅ This should work — our Role allows `get` and `list` on Pods.

```bash
# Reading Pod logs — also allowed
kubectl exec -it rbac-test -- kubectl logs rbac-test
```

### 6. Test DENIED actions (things we didn't grant)

```bash
# Try to delete a Pod
kubectl exec -it rbac-test -- kubectl delete pod rbac-test
```

❌ **Forbidden** — our Role doesn't include the `delete` verb.

```bash
# Try to list Secrets
kubectl exec -it rbac-test -- kubectl get secrets
```

❌ **Forbidden** — our Role only covers `pods` and `pods/log`, not `secrets`.

```bash
# Try to create a Deployment
kubectl exec -it rbac-test -- kubectl create deployment test --image=nginx
```

❌ **Forbidden** — no permissions on deployments.

### 7. Test cluster-scoped resources — they fail with just a Role

```bash
# Try to list namespaces (cluster-scoped resource)
kubectl exec -it rbac-test -- kubectl get namespaces
```

❌ **Forbidden** — Roles are namespace-scoped, can't access cluster resources.

### 8. Add a ClusterRole and ClusterRoleBinding

```bash
kubectl apply -f clusterrole.yaml
kubectl apply -f clusterrolebinding.yaml
```

### 9. Test cluster-scoped access

```bash
# Now listing namespaces works
kubectl exec -it rbac-test -- kubectl get namespaces

# Listing nodes works too
kubectl exec -it rbac-test -- kubectl get nodes
```

✅ ClusterRole grants access to cluster-wide resources.

### 10. Verify using `kubectl auth can-i`

The `can-i` command lets you check permissions without trial and error:

```bash
# Check as the ServiceAccount
kubectl auth can-i get pods --as=system:serviceaccount:default:app-reader
# yes

kubectl auth can-i delete pods --as=system:serviceaccount:default:app-reader
# no

kubectl auth can-i get secrets --as=system:serviceaccount:default:app-reader
# no

kubectl auth can-i get namespaces --as=system:serviceaccount:default:app-reader
# yes (because of our ClusterRole)

# Check what you can do overall
kubectl auth can-i --list --as=system:serviceaccount:default:app-reader
```

### 11. Bonus — see the broader "deployment-manager" Role

```bash
cat role-deployment-manager.yaml
```

This shows a more realistic role that allows managing Deployments, viewing Pods, and managing Services.

---

## Role vs ClusterRole — When to Use Which

| | Role + RoleBinding | ClusterRole + ClusterRoleBinding |
|---|---|---|
| **Scope** | Single namespace | Entire cluster |
| **Use for** | App-specific access | Cluster admins, monitoring, logging |
| **Example** | "Read Pods in `production` namespace" | "Read nodes and namespaces cluster-wide" |
| **Risk** | Limited blast radius | High blast radius — be careful! |

### Tip: ClusterRole + RoleBinding

You can also bind a ClusterRole with a RoleBinding to restrict it to one namespace:

```bash
# This gives the built-in "view" ClusterRole, but ONLY in the default namespace
kubectl create rolebinding view-default \
  --clusterrole=view \
  --serviceaccount=default:app-reader \
  --namespace=default
```

---

## Real-World RBAC Patterns

| Persona | Permissions |
|---------|-------------|
| **Developer** | View Pods/logs in their namespace, create Deployments in staging |
| **CI/CD Pipeline** | Create/update Deployments and Services in specific namespaces |
| **Monitoring** | Read-only access to all Pods, metrics, events cluster-wide |
| **Cluster Admin** | Full access (use sparingly, bind the built-in `cluster-admin` ClusterRole) |
| **App Pod** | Read Secrets/ConfigMaps it needs, nothing else |

---

## Clean Up

```bash
kubectl delete -f pod-rbac-test.yaml
kubectl delete -f rolebinding.yaml
kubectl delete -f clusterrolebinding.yaml
kubectl delete -f role.yaml
kubectl delete -f role-deployment-manager.yaml
kubectl delete -f clusterrole.yaml
kubectl delete -f serviceaccount.yaml

# Clean up the bonus rolebinding if created
kubectl delete rolebinding view-default 2>/dev/null
```

---

## Key Takeaways

- RBAC follows **three steps**: create a Subject (who), create a Role (what), create a Binding (connect them)
- **Role** = namespace-scoped, **ClusterRole** = cluster-scoped
- **ServiceAccounts** are the identity for Pods — always create specific ones, never use `default`
- Use `kubectl auth can-i` to test permissions without deploying
- Follow **least privilege** — grant only what's needed, nothing more
- Built-in ClusterRoles (`view`, `edit`, `admin`, `cluster-admin`) cover common patterns

## Built-in ClusterRoles Reference

```bash
# See all built-in roles
kubectl get clusterroles | grep -v "system:"

# Key ones:
# view   — read-only access to most resources in a namespace
# edit   — read/write access (no RBAC changes, no secrets by default)
# admin  — full namespace access including RBAC
# cluster-admin — god mode (use sparingly!)
```
