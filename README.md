# Kubernetes Objects - Session Demos

## Session Flow

| # | Topic | Demo | Key Takeaway |
|---|-------|------|--------------|
| 1 | Containers & Pods (Single Container) | `01-pod-single-container/` | A Pod is the smallest deployable unit wrapping one container |
| 2 | Pods (Multi-Container) | `02-pod-multi-container/` | Containers in the same Pod share network & storage |
| 3 | Labels & Selectors | `03-labels-selectors/` | Labels are how Kubernetes organizes and selects objects |
| 4 | ReplicaSet | `04-replicaset/` | ReplicaSet ensures a desired number of Pod replicas using selectors |
| 5 | Deployment | `05-deployment/` | Deployment manages ReplicaSets and enables rolling updates |
| 6 | Namespaces | `06-namespaces/` | Namespaces provide logical isolation and resource quotas within a cluster |
| 7 | Services | `07-services/` | Services provide stable endpoints and load balancing for ephemeral Pods |
| 8 | Ingress | `08-ingress/` | Ingress provides HTTP routing via host-based and path-based rules |
| 9 | ConfigMaps & Secrets | `09-configmaps-secrets/` | Decouple configuration and sensitive data from container images |
| 10 | Volumes & Persistent Storage | `10-volumes-storage/` | Volumes provide data persistence beyond the container lifecycle |
| 11 | Scaling (HPA & VPA) | `11-scaling-hpa-vpa/` | Autoscale Pods horizontally (more replicas) or vertically (more resources) |
| 12 | RBAC | `12-rbac/` | Control who can do what on which resources using roles and bindings |

## Prerequisites

```bash
# A running cluster (Docker Desktop Kubernetes, minikube, or kind)
# Enable Kubernetes in Docker Desktop → Settings → Kubernetes → Enable

# Verify
kubectl cluster-info
```

## How to Use

Follow the demos in order. Each folder has its own README with step-by-step instructions.
