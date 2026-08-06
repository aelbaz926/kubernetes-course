# Demo 7: Services

## Concept

A **Service** provides a stable network endpoint to access a set of Pods. Since Pods are ephemeral (they get new IPs every time they restart), you need something permanent to point to.

### The Problem it Solves

Without Services:
- ❌ Pod IPs change every time a Pod is recreated
- ❌ Clients need to know the exact IP of every Pod
- ❌ No load balancing across multiple Pod replicas
- ❌ No way for external traffic to reach your Pods

With Services:
- ✅ **Stable endpoint** — one DNS name / IP that never changes
- ✅ **Load balancing** — traffic is distributed across all matching Pods
- ✅ **Service discovery** — other Pods can find your app by name
- ✅ **External access** — expose your app to the outside world

### How does a Service find its Pods?

**Labels and Selectors!** (from Demo 3)

A Service uses a `selector` to find Pods with matching labels — just like ReplicaSets and Deployments.

### Service Types

| Type | Description | Accessible From |
|------|-------------|-----------------|
| `ClusterIP` | Internal-only (default) | Inside the cluster only |
| `NodePort` | Exposes on each Node's IP at a static port | Outside the cluster via `<NodeIP>:<NodePort>` |
| `LoadBalancer` | Provisions an external load balancer (cloud) | Internet (via cloud LB) |

---

## Step-by-Step Demo

### 1. Create a Deployment (our backend Pods)

```bash
kubectl apply -f deployment.yaml
```

### 2. Verify the Pods are running

```bash
kubectl get pods -o wide --show-labels
```

Notice each Pod has a **different IP**. These IPs are ephemeral!

### 3. The problem: Pod IPs are unreliable

```bash
# Get a Pod IP
kubectl get pods -o wide

# Delete the Pod
kubectl delete pod <pod-name>

# The new Pod has a DIFFERENT IP!
kubectl get pods -o wide
```

Anyone pointing to the old IP is now broken.

### 4. Create a ClusterIP Service (internal)

```bash
kubectl apply -f service-clusterip.yaml
```

### 5. Inspect the Service

```bash
kubectl get service

# See which Pods it targets
kubectl describe service web-app-service
```

Notice the `Endpoints` — these are the Pod IPs the Service routes to.

### 6. Test internal access using DNS

```bash
# Run a temporary Pod to test connectivity
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh

# Inside the Pod, curl the Service by NAME
wget -qO- http://web-app-service
# or with full DNS:
wget -qO- http://web-app-service.default.svc.cluster.local

# Exit when done
exit
```

The Service DNS name works from any Pod in the cluster!

### 7. Create a NodePort Service (external access)

```bash
kubectl apply -f service-nodeport.yaml
```

### 8. Access the app from outside the cluster

```bash
# Get the NodePort
kubectl get service web-app-nodeport

# For minikube, get the URL directly:
minikube service web-app-nodeport --url

# Or manually: access via http://<node-ip>:<nodeport>
```

### 9. Show the label-selector connection

```bash
# The Service selects Pods with these labels
kubectl describe service web-app-service | grep -A 3 "Selector"

# Scale the Deployment — new Pods auto-register with the Service!
kubectl scale deployment web-app-deploy --replicas=5
kubectl describe service web-app-service | grep "Endpoints"

# Scale down — removed Pods auto-deregister!
kubectl scale deployment web-app-deploy --replicas=2
kubectl describe service web-app-service | grep "Endpoints"
```

### 10. Cross-namespace Service access

```bash
# Create a namespace with an app
kubectl create namespace other-team
kubectl apply -f cross-namespace-app.yaml

# From default namespace, access the Service in other-team:
kubectl run test-pod --image=busybox --rm -it --restart=Never -- sh

# Use the full DNS name: <service>.<namespace>.svc.cluster.local
wget -qO- http://web-app-service.other-team.svc.cluster.local

exit
```

### 11. Clean up

```bash
kubectl delete -f deployment.yaml
kubectl delete -f service-clusterip.yaml
kubectl delete -f service-nodeport.yaml
kubectl delete -f cross-namespace-app.yaml
kubectl delete namespace other-team
```

---

## Key Takeaways

- A Service provides a **stable endpoint** (IP + DNS) for ephemeral Pods
- It uses **label selectors** to discover which Pods to route traffic to
- **ClusterIP** = internal only (default), **NodePort** = external access, **LoadBalancer** = cloud LB
- Pods auto-register/deregister as they scale up/down
- Services enable **DNS-based service discovery**: `<service>.<namespace>.svc.cluster.local`
- Cross-namespace communication works using the full DNS name

## Summary: How Everything Connects

```
                         ┌─────────────────────────────────────┐
  External Traffic       │           SERVICE (NodePort)         │
  ────────────────────►  │     selector: app=web-app           │
                         └──────────────┬──────────────────────┘
                                        │ routes to matching Pods
                         ┌──────────────▼──────────────────────┐
                         │           SERVICE (ClusterIP)        │
  Internal Pods ───────► │     selector: app=web-app           │
                         └──────────────┬──────────────────────┘
                                        │ load balances across
               ┌────────────────────────┼────────────────────────┐
               ▼                        ▼                        ▼
        ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
        │  Pod (v1)   │         │  Pod (v1)   │         │  Pod (v1)   │
        │ app=web-app │         │ app=web-app │         │ app=web-app │
        │ IP: 10.0.1.2│         │ IP: 10.0.1.3│         │ IP: 10.0.1.4│
        └─────────────┘         └─────────────┘         └─────────────┘
```
