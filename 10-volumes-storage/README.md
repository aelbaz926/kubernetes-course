# Demo 10: Volumes & Persistent Storage

## Concept

Containers are **ephemeral** by default — when a container restarts, all data written inside it is lost. **Volumes** solve this by providing storage that outlives the container lifecycle.

### The Problem it Solves

Without Volumes:
- ❌ Data is lost when a container crashes or restarts
- ❌ Containers in the same Pod can't share files
- ❌ No way to persist database files, uploads, or logs
- ❌ Stateful apps (databases, caches) can't run reliably

With Volumes:
- ✅ **Data survives restarts** — volume persists across container restarts
- ✅ **Shared storage** — multiple containers in a Pod can read/write the same volume
- ✅ **Persistent data** — PersistentVolumes survive even Pod deletion
- ✅ **Storage abstraction** — decouple storage provisioning from consumption

---

## Volume Types (from simplest to most powerful)

### 1. emptyDir

- Created when a Pod is assigned to a Node
- Starts empty
- Survives container restarts **within the same Pod**
- **Deleted when the Pod is deleted**
- Use case: scratch space, sharing files between containers in a Pod

### 2. hostPath

- Mounts a file or directory from the **host Node's filesystem**
- Survives Pod deletion (data stays on the Node)
- **Tied to a specific Node** — Pod must run on that Node to access data
- Use case: accessing Docker socket, node-level logs, single-node development
- ⚠️ **Not recommended for production** (not portable across Nodes)

### 3. PersistentVolume (PV) + PersistentVolumeClaim (PVC)

- **PersistentVolume (PV)** — a piece of storage provisioned in the cluster (the actual disk)
- **PersistentVolumeClaim (PVC)** — a request for storage by a Pod (like ordering a disk)
- Decouples storage provisioning from consumption
- Survives Pod deletion — data persists until PV is deleted
- Use case: databases, file uploads, any stateful workload

### 4. StorageClass (Dynamic Provisioning)

- Automatically creates PersistentVolumes when a PVC is created
- No need to pre-create PVs manually!
- Different classes for different performance tiers (SSD vs HDD)
- Use case: production workloads where PVs are created on-demand

```
┌─────────────────────────────────────────────────────────┐
│                   Storage Hierarchy                      │
│                                                         │
│   StorageClass (defines HOW to provision)               │
│        │                                                │
│        ▼ (dynamically creates)                          │
│   PersistentVolume (the actual storage)                 │
│        │                                                │
│        ▼ (bound to)                                     │
│   PersistentVolumeClaim (Pod's request for storage)     │
│        │                                                │
│        ▼ (mounted in)                                   │
│   Pod → Container (uses the storage)                    │
└─────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Demo

### Part A: emptyDir (temporary shared storage)

#### 1. Create a Pod with emptyDir

```bash
kubectl apply -f pod-emptydir.yaml
```

This Pod has two containers sharing an emptyDir volume:
- `writer` container writes data to the volume
- `reader` container reads data from the same volume

#### 2. Verify shared storage works

```bash
# Check what the writer is producing
kubectl exec pod-emptydir -c writer -- cat /data/output.txt

# Check that the reader can see the same data
kubectl exec pod-emptydir -c reader -- cat /shared-data/output.txt
```

Both containers see the same files!

#### 3. Show that emptyDir survives container restarts but NOT Pod deletion

```bash
# Kill the writer container (Pod stays, container restarts)
kubectl exec pod-emptydir -c writer -- kill 1

# Wait for restart
kubectl get pod pod-emptydir --watch

# Data is still there after container restart!
kubectl exec pod-emptydir -c reader -- cat /shared-data/output.txt

# But delete the Pod — data is gone
kubectl delete pod pod-emptydir
kubectl apply -f pod-emptydir.yaml
kubectl exec pod-emptydir -c reader -- cat /shared-data/output.txt
# → "cat: can't open '/shared-data/output.txt': No such file or directory"
```

---

### Part B: hostPath (Node-level storage)

#### 4. Create a Pod with hostPath

```bash
kubectl apply -f pod-hostpath.yaml
```

#### 5. Write data and verify persistence across Pod deletion

```bash
# Write some data
kubectl exec pod-hostpath -- sh -c 'echo "This data survives Pod deletion!" > /data/important.txt'

# Verify
kubectl exec pod-hostpath -- cat /data/important.txt

# Delete the Pod
kubectl delete pod pod-hostpath

# Recreate the Pod
kubectl apply -f pod-hostpath.yaml

# Data is STILL there! (it's on the Node's filesystem)
kubectl exec pod-hostpath -- cat /data/important.txt
```

#### 6. See the data on the Node (Docker Desktop)

```bash
# On Docker Desktop, the "node" is the Docker VM
# The data is stored at /tmp/k8s-demo-data on the VM
```

> ⚠️ **hostPath limitation**: If you had multiple Nodes, the Pod must be scheduled on the same Node to see the data. That's why this is not portable.

---

### Part C: PersistentVolume & PersistentVolumeClaim

#### 7. Create a PersistentVolume (the actual storage)

```bash
kubectl apply -f pv.yaml
```

Inspect:

```bash
kubectl get pv
# STATUS should be "Available"
```

#### 8. Create a PersistentVolumeClaim (request for storage)

```bash
kubectl apply -f pvc.yaml
```

Inspect:

```bash
kubectl get pvc
# STATUS should be "Bound"

kubectl get pv
# STATUS changed from "Available" to "Bound"
```

The PVC matched the PV based on size and access mode!

#### 9. Use the PVC in a Pod

```bash
kubectl apply -f pod-pvc.yaml
```

Write and verify data:

```bash
# Write data
kubectl exec pod-with-pvc -- sh -c 'echo "Persistent data here!" > /app/data/myfile.txt'

# Verify
kubectl exec pod-with-pvc -- cat /app/data/myfile.txt
```

#### 10. Show data persists across Pod deletion

```bash
# Delete the Pod
kubectl delete pod pod-with-pvc

# Recreate it — same PVC, same data
kubectl apply -f pod-pvc.yaml

# Data survived!
kubectl exec pod-with-pvc -- cat /app/data/myfile.txt
```

---

### Part D: StorageClass (Dynamic Provisioning)

#### 11. Check available StorageClasses

```bash
kubectl get storageclass
```

On Docker Desktop, you'll see:

```
NAME                 PROVISIONER          RECLAIMPOLICY   VOLUMEBINDINGMODE
hostpath (default)   docker.io/hostpath   Delete          Immediate
```

Docker Desktop provides a built-in `hostpath` StorageClass that dynamically provisions storage.

#### 12. Create a PVC with dynamic provisioning (no pre-created PV needed!)

```bash
kubectl apply -f pvc-dynamic.yaml
```

Inspect:

```bash
# The PVC is bound — a PV was automatically created!
kubectl get pvc
kubectl get pv

# See which StorageClass was used
kubectl describe pvc dynamic-pvc
```

Notice: a PV was **automatically created** by the StorageClass — no manual PV needed!

#### 13. Use the dynamically provisioned PVC

```bash
kubectl apply -f pod-dynamic-pvc.yaml
```

Test it:

```bash
# Write data
kubectl exec pod-dynamic-storage -- sh -c 'echo "Dynamic provisioning works!" > /app/data/dynamic.txt'

# Verify
kubectl exec pod-dynamic-storage -- cat /app/data/dynamic.txt
```

#### 14. Show the difference: manual vs dynamic provisioning

```bash
# Manual: you create PV first, then PVC binds to it
kubectl get pv -o custom-columns=NAME:.metadata.name,STORAGECLASS:.spec.storageClassName,CLAIM:.spec.claimRef.name

# Dynamic: StorageClass creates PV automatically when PVC is created
# Look for PVs with storageClassName: hostpath
```

---

### 15. Clean up

```bash
kubectl delete -f pod-emptydir.yaml
kubectl delete -f pod-hostpath.yaml
kubectl delete -f pod-pvc.yaml
kubectl delete -f pod-dynamic-pvc.yaml
kubectl delete -f pvc.yaml
kubectl delete -f pvc-dynamic.yaml
kubectl delete -f pv.yaml

# Clean up hostPath data on the Node (Docker Desktop)
# The /tmp/k8s-demo-data directory will be cleaned on VM restart
```

---

## Key Takeaways

| Volume Type | Survives Container Restart? | Survives Pod Deletion? | Portable Across Nodes? |
|---|---|---|---|
| `emptyDir` | ✅ Yes | ❌ No | ❌ No (Pod-level) |
| `hostPath` | ✅ Yes | ✅ Yes (same Node) | ❌ No (Node-specific) |
| `PV + PVC` | ✅ Yes | ✅ Yes | ✅ Yes (cluster-level) |
| `StorageClass` | ✅ Yes | ✅ Yes | ✅ Yes (dynamic) |

- **emptyDir** = scratch space / inter-container sharing (dies with Pod)
- **hostPath** = Node-level persistence (good for dev, bad for prod)
- **PV + PVC** = proper persistent storage (manual provisioning)
- **StorageClass** = automatic storage provisioning (production pattern)
- On **Docker Desktop**, the built-in `hostpath` StorageClass handles dynamic provisioning automatically
- In production, StorageClasses map to real cloud storage (AWS EBS, GCP PD, Azure Disk)

## Docker Desktop Note

Docker Desktop provides a `hostpath` StorageClass as the default provisioner. This uses the Docker VM's filesystem for storage. In a cloud environment, you'd have StorageClasses like:
- `gp3` (AWS EBS)
- `pd-standard` / `pd-ssd` (GCP)
- `managed-premium` (Azure)

The concepts are identical — only the underlying storage provider changes.
