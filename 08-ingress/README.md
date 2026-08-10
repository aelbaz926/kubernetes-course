# Demo 8: Ingress

## Concept

An **Ingress** manages external HTTP/HTTPS access to Services in your cluster. Think of it as a smart router that sits at the edge of your cluster and directs traffic based on hostnames and URL paths.

### The Problem it Solves

Without Ingress:
- ❌ Each Service needs its own LoadBalancer (expensive!)
- ❌ No way to route by hostname (e.g., `api.myapp.com` vs `web.myapp.com`)
- ❌ No way to route by path (e.g., `/api` vs `/web`)
- ❌ No centralized TLS termination
- ❌ NodePort exposes random high ports (30000-32767)

With Ingress:
- ✅ **Single entry point** — one IP/LoadBalancer for multiple Services
- ✅ **Host-based routing** — route by domain name
- ✅ **Path-based routing** — route by URL path
- ✅ **TLS termination** — handle HTTPS in one place
- ✅ **Clean URLs** — access apps on port 80/443

### How it Works

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────┐
│              INGRESS CONTROLLER                       │
│         (nginx, traefik, etc.)                       │
│                                                      │
│  Rules:                                              │
│  ├─ host: api.myapp.com   → Service: api-service    │
│  ├─ host: web.myapp.com   → Service: web-service    │
│  ├─ path: /api            → Service: api-service    │
│  └─ path: /               → Service: web-service    │
└──────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
  ┌─────────────┐            ┌─────────────┐
  │ api-service │            │ web-service │
  │  (Pods)     │            │  (Pods)     │
  └─────────────┘            └─────────────┘
```

### Two Components

1. **Ingress Resource** — YAML rules you write (what to route where)
2. **Ingress Controller** — the actual proxy that enforces the rules (must be installed separately!)

---

## Step-by-Step Demo

### 0. Enable the Ingress Controller (Docker Desktop)

Docker Desktop's Kubernetes doesn't come with an Ingress Controller. Install the NGINX Ingress Controller:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.0/deploy/static/provider/cloud/deploy.yaml
```

Wait for the controller to be ready:

```bash
kubectl get pods -n ingress-nginx --watch
# Wait until the controller pod shows Running (1/1)
```

Verify:

```bash
kubectl get svc -n ingress-nginx
# You should see ingress-nginx-controller with type LoadBalancer
# On Docker Desktop, EXTERNAL-IP will be "localhost"
```

### 1. Deploy two sample apps

```bash
kubectl apply -f apps.yaml
```

This creates:
- `web-app` Deployment + ClusterIP Service (returns "Hello from Web App!")
- `api-app` Deployment + ClusterIP Service (returns "Hello from API App!")

### 2. Verify the apps are running

```bash
kubectl get deployments
kubectl get services
```

---

### 3. Path-Based Routing

Route traffic based on the URL path:
- `/web` → web-app Service
- `/api` → api-app Service

```bash
kubectl apply -f ingress-path-based.yaml
```

Inspect the Ingress:

```bash
kubectl get ingress
kubectl describe ingress path-based-ingress
```

Test it (Docker Desktop — Ingress is accessible on localhost):

```bash
# These should route to different apps
curl http://localhost/web
# → "Hello from Web App!"

curl http://localhost/api
# → "Hello from API App!"
```

---

### 4. Host-Based Routing

Route traffic based on the hostname:
- `web.local` → web-app Service
- `api.local` → api-app Service

```bash
kubectl apply -f ingress-host-based.yaml
```

Add entries to your `/etc/hosts` file (so the hostnames resolve to localhost):

```bash
# Add these lines to /etc/hosts
echo "127.0.0.1 web.local" | sudo tee -a /etc/hosts
echo "127.0.0.1 api.local" | sudo tee -a /etc/hosts
```

Test it:

```bash
curl http://web.local
# → "Hello from Web App!"

curl http://api.local
# → "Hello from API App!"
```

### 5. Inspect what the Ingress Controller is doing

```bash
# See the rules it's enforcing
kubectl describe ingress host-based-ingress

# See the NGINX controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx
```

---

## Gateway API (High-Level Introduction)

The **Gateway API** is the next-generation replacement for Ingress. Think of it as "Ingress v2" — it does the same job (routing traffic) but solves real problems that teams hit when using Ingress in production.

### "But wait — can't each team just create their own Ingress resource?"

Yes! And that's the common pattern. Each team creates a separate Ingress in their own namespace:

```yaml
# Team A's Ingress (in orders-ns namespace)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orders-ingress
  namespace: orders-ns
spec:
  rules:
    - host: api.shop.com
      http:
        paths:
          - path: /orders
            backend:
              service:
                name: orders-service
---
# Team B's Ingress (in products-ns namespace)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: products-ingress
  namespace: products-ns
spec:
  rules:
    - host: api.shop.com
      http:
        paths:
          - path: /products
            backend:
              service:
                name: products-service
```

This works! So **why does Gateway API exist?** The problems are more subtle:

---

### The Real Problems with Ingress (even with separate files per team)

#### Problem 1: No Governance — Any Team Can Claim Any Hostname

All those separate Ingress resources share the **same Ingress Controller** (the NGINX pod). There's no built-in way to prevent conflicts.

What if Team B (accidentally or intentionally) creates:

```yaml
# Team B claims Team A's hostname!
spec:
  rules:
    - host: api.shop.com
      http:
        paths:
          - path: /orders    # ← This is Team A's path!
```

What happens? **Undefined behavior.** The Ingress Controller might pick one randomly, use creation order, or silently drop one. There's no built-in mechanism to say "only Team A is allowed to route `api.shop.com/orders`."

**With Gateway API**: The Gateway resource explicitly declares which namespaces can attach routes and for which hostnames:

```yaml
# Gateway (created by infra team)
spec:
  listeners:
    - name: http
      port: 80
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              routing-allowed: "true"    # Only labeled namespaces!
        hostnames:
          - "*.shop.com"
```

Now Team B literally **cannot** create a route for a hostname they don't own — the Gateway rejects it.

---

#### Problem 2: Traffic Splitting Requires Vendor-Specific Hacks

"Send 90% of traffic to v1 and 10% to the new v2 (canary deployment)"

With Ingress, you need controller-specific annotations that only work on ONE vendor:

```yaml
# NGINX-specific — breaks if you switch to Traefik or AWS ALB
annotations:
  nginx.ingress.kubernetes.io/canary: "true"
  nginx.ingress.kubernetes.io/canary-weight: "10"
```

Switch your Ingress Controller tomorrow? Rewrite all your annotations.

**With Gateway API** — built-in and portable across ANY controller:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
spec:
  rules:
    - backendRefs:
        - name: orders-v1
          port: 80
          weight: 90       # 90% → stable
        - name: orders-v2
          port: 80
          weight: 10       # 10% → canary
```

Works the same on NGINX, Envoy, Traefik, AWS ALB, or any Gateway API-compatible controller.

---

#### Problem 3: HTTP Only — No TCP, gRPC, or UDP

If Team C needs to expose a PostgreSQL database (TCP port 5432) or a gRPC service — Ingress simply **cannot do it**. Separate Ingress files per team doesn't help because the limitation is in the Ingress spec itself.

**With Gateway API:**
- **HTTPRoute** — HTTP/HTTPS traffic
- **GRPCRoute** — gRPC services
- **TCPRoute** — raw TCP (databases, custom protocols)
- **TLSRoute** — TLS passthrough

---

### So What IS Gateway API?

It splits the routing job into **three layers**, each owned by a different role:

```
┌─────────────────────────────────────────────────────────────┐
│  WHO: Cluster Admin / Platform Team                         │
│  WHAT: GatewayClass                                        │
│  WHY: "We use NGINX (or Envoy, or AWS ALB) as our proxy"  │
│                                                             │
│  Think of it like: choosing which BRAND of router to buy    │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│  WHO: Infrastructure / DevOps Team                          │
│  WHAT: Gateway                                             │
│  WHY: "Listen on port 443, with this TLS cert, and only    │
│        allow THESE namespaces to attach routes for THESE    │
│        hostnames"                                           │
│                                                             │
│  Think of it like: plugging in the router + setting up      │
│  which devices are ALLOWED to connect                       │
└─────────────────────────────────┬───────────────────────────┘
                                  │
┌─────────────────────────────────▼───────────────────────────┐
│  WHO: Application Developers (each team independently!)     │
│  WHAT: HTTPRoute (or TCPRoute, GRPCRoute, etc.)            │
│  WHY: "Route api.shop.com/orders → my orders service"      │
│                                                             │
│  Think of it like: connecting your device to the network    │
│  — but only within the permissions the admin gave you       │
└─────────────────────────────────────────────────────────────┘
```

---

### Real-World Scenario

#### E-commerce company with 3 teams

**Team A** — Orders (`api.shop.com/orders`)  
**Team B** — Products (`api.shop.com/products`)  
**Team C** — Payments (`payments.shop.com` + TCP for payment gateway)

**DevOps sets up the Gateway ONCE:**
```
"Here's the Gateway. It listens on ports 80/443.
 - orders-ns can route api.shop.com/orders/*
 - products-ns can route api.shop.com/products/*
 - payments-ns can route payments.shop.com/* and TCP port 5432
 
 Done. Teams — you manage your own HTTPRoutes now."
```

**Each team then works independently:**
- Team A changes their routes → can't accidentally touch Team B's paths
- Team B adds a new path → no risk of conflict, Gateway enforces boundaries
- Team C creates a TCPRoute → works natively, no workaround needed

---

### Honest Comparison

| | Separate Ingress per team | Gateway API |
|--|--|--|
| Each team has their own YAML file | ✅ Yes | ✅ Yes |
| Prevent team from claiming another team's hostname/path | ❌ No built-in way | ✅ Gateway enforces boundaries |
| Traffic splitting (canary) | ❌ Vendor-specific annotations | ✅ Native and portable |
| TCP / gRPC routing | ❌ Not possible with Ingress | ✅ Built-in (TCPRoute, GRPCRoute) |
| Portable across controllers | ❌ Annotations differ per vendor | ✅ Standard API everywhere |
| Complexity | Simple (fewer resources) | More YAML (3 resource types) |

---

### When to Use What?

| Situation | Use |
|-----------|-----|
| Learning / small team / simple app | **Ingress** (simpler, less YAML) |
| Multiple teams + need to prevent route conflicts | **Gateway API** (governance) |
| Need traffic splitting / canary deploys | **Gateway API** (built-in) |
| Need TCP/gRPC routing | **Gateway API** (multi-protocol) |
| Already using Ingress and it works fine | **Keep Ingress** (don't fix what's not broken) |

---

### Summary

Gateway API is NOT a different concept from Ingress — it's the **same idea** (route external traffic to Services). Each team can already have separate Ingress files, and that's fine for many setups.

Gateway API adds value when you need:
1. **Governance** — control who can route what hostname/path (prevent conflicts)
2. **Portability** — traffic splitting and advanced routing without vendor-specific annotations
3. **Multi-protocol** — TCP, gRPC, TLS routing (impossible with Ingress)

> **For this course**: We'll stick with Ingress since it's simpler and perfectly suitable for learning routing concepts. Just know that Gateway API exists and uses the same underlying principles — you'll likely encounter it in production environments.

---

### 6. Clean up

```bash
kubectl delete -f ingress-path-based.yaml
kubectl delete -f ingress-host-based.yaml
kubectl delete -f apps.yaml

# Remove /etc/hosts entries (optional)
sudo sed -i '' '/web.local/d' /etc/hosts
sudo sed -i '' '/api.local/d' /etc/hosts
```

---

## Key Takeaways

- **Ingress** provides HTTP/HTTPS routing to Services based on host and path rules
- You need an **Ingress Controller** (like NGINX) installed — the Ingress resource alone does nothing
- **Path-based routing**: one host, different paths → different Services
- **Host-based routing**: different hostnames → different Services
- **Gateway API** is the successor to Ingress — more powerful and role-oriented, but same core concepts
- On Docker Desktop, the Ingress Controller is accessible at `localhost`

## What's Next?

Now that traffic can reach our apps — how do we configure them without baking settings into the container image? → Demo 9 (ConfigMaps & Secrets)
