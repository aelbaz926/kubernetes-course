# Demo 9: ConfigMaps & Secrets

## Concept

When you move applications to Kubernetes, you need a way to pass configuration and sensitive data to your containers **without hardcoding them into the image**.

### The Problem it Solves

Without ConfigMaps/Secrets:
- ❌ Configuration baked into container images (rebuild for every environment)
- ❌ Secrets (passwords, API keys) stored in Dockerfiles or code
- ❌ Can't change config without redeploying the entire image
- ❌ Same image can't be used across dev/staging/prod

With ConfigMaps & Secrets:
- ✅ **Decouple config from image** — same image, different config per environment
- ✅ **Secrets are stored separately** — not in your code or Dockerfile
- ✅ **Update config without rebuilding** — change the ConfigMap, restart the Pod
- ✅ **Kubernetes manages lifecycle** — config lives as cluster objects

### ConfigMap vs Secret

| | ConfigMap | Secret |
|--|----------|--------|
| **Purpose** | Non-sensitive config (URLs, feature flags, settings) | Sensitive data (passwords, tokens, keys) |
| **Stored as** | Plain text | Base64-encoded (NOT encrypted by default!) |
| **Example** | `DATABASE_HOST=postgres.svc` | `DATABASE_PASSWORD=s3cr3t!` |

> ⚠️ **Important**: Secrets are base64-encoded, NOT encrypted. For real security, use solutions like Sealed Secrets, HashiCorp Vault, or enable encryption at rest.

### How to Inject Config into Pods

Two methods:
1. **Environment Variables** — injected at container start
2. **Volume Mounts** — mounted as files inside the container

---

## Step-by-Step Demo

### 1. Create a ConfigMap (non-sensitive config)

```bash
kubectl apply -f configmap.yaml
```

Inspect it:

```bash
kubectl get configmap app-config
kubectl describe configmap app-config

# See the raw data
kubectl get configmap app-config -o yaml
```

### 2. Create a Secret (sensitive data)

```bash
kubectl apply -f secret.yaml
```

Inspect it:

```bash
kubectl get secret app-secret
kubectl describe secret app-secret

# Notice: values are base64-encoded
kubectl get secret app-secret -o yaml

# Decode a value manually:
echo "cG9zdGdyZXMtcGFzc3dvcmQxMjM=" | base64 --decode
```

### 3. Use ConfigMap & Secret as Environment Variables

```bash
kubectl apply -f pod-env-vars.yaml
```

Verify the environment variables are injected:

```bash
kubectl exec pod-with-env -- env | grep -E "APP_|DB_"
```

Expected output:
```
APP_ENV=production
APP_LOG_LEVEL=info
APP_MAX_CONNECTIONS=100
DB_USERNAME=admin
DB_PASSWORD=postgres-password123
```

### 4. Use ConfigMap as a Volume Mount (config files)

```bash
kubectl apply -f pod-volume-mount.yaml
```

Check the mounted config files:

```bash
# List mounted files
kubectl exec pod-with-volume -- ls /etc/config/

# Read the config file content
kubectl exec pod-with-volume -- cat /etc/config/nginx.conf

# Read the settings file
kubectl exec pod-with-volume -- cat /etc/config/settings.json
```

### 5. Create a ConfigMap from a file (common pattern)

```bash
# Create a ConfigMap from a local file
kubectl create configmap nginx-config --from-file=sample-nginx.conf

# Inspect it
kubectl get configmap nginx-config -o yaml
```

### 6. Create a Secret from literal values (imperative)

```bash
# Create a Secret imperatively (useful for quick setups)
kubectl create secret generic my-api-secret \
  --from-literal=api-key=abc123xyz \
  --from-literal=api-secret=supersecret456

# Inspect it
kubectl get secret my-api-secret -o yaml
```

### 7. Show the real-world pattern: same image, different config

```bash
# Deploy the same app image with "dev" config
kubectl apply -f pod-dev.yaml

# Deploy the same app image with "prod" config
kubectl apply -f pod-prod.yaml

# See different environments with same image:
kubectl exec pod-dev-app -- env | grep APP_
kubectl exec pod-prod-app -- env | grep APP_
```

### 8. Clean up

```bash
kubectl delete -f pod-env-vars.yaml
kubectl delete -f pod-volume-mount.yaml
kubectl delete -f pod-dev.yaml
kubectl delete -f pod-prod.yaml
kubectl delete -f configmap.yaml
kubectl delete -f secret.yaml
kubectl delete configmap nginx-config
kubectl delete secret my-api-secret
```

---

## Key Takeaways

- **ConfigMaps** store non-sensitive configuration as key-value pairs
- **Secrets** store sensitive data (base64-encoded, not encrypted!)
- Both can be injected as **environment variables** or **mounted as files**
- This enables the **same container image** across all environments (dev/staging/prod)
- ConfigMaps and Secrets decouple your app configuration from the container image
- Use `kubectl create configmap --from-file=` for config files, `--from-literal=` for key-value pairs

## What's Next?

We can configure our apps — but what about data that needs to survive Pod restarts? → Demo 10 (Volumes & Persistent Storage)
