# Kubernetes Objects - Session Demos

## Session Flow

| # | Topic | Demo | Key Takeaway |
|---|-------|------|--------------|
| 1 | Containers & Pods (Single Container) | `01-pod-single-container/` | A Pod is the smallest deployable unit wrapping one container |
| 2 | Pods (Multi-Container) | `02-pod-multi-container/` | Containers in the same Pod share network & storage |
| 3 | Labels & Selectors | `03-labels-selectors/` | Labels are how Kubernetes organizes and selects objects |
| 4 | ReplicaSet | `04-replicaset/` | ReplicaSet ensures a desired number of Pod replicas using selectors |
| 5 | Deployment | `05-deployment/` | Deployment manages ReplicaSets and enables rolling updates |

## Prerequisites

```bash
# A running cluster (minikube, kind, or any cluster)
minikube start

# Verify
kubectl cluster-info
```

## How to Use

Follow the demos in order. Each folder has its own README with step-by-step instructions.
