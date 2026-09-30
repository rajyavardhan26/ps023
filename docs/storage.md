# Storage Architecture & Failover Realities

## 1. Storage Layout

Virtual machine storage uses `qcow2` (QEMU Copy-On-Write version 2).

```text
/tmp/ps023/images/
   └── ubuntu-24.04.qcow2 (Read-only Golden Base Image)
             ▲
             │ (Backing File Link)
/tmp/ps023/disks/
   ├── ubuntu-demo.qcow2 (Delta overlay for VM 1)
   └── worker-vm.qcow2   (Delta overlay for VM 2)
```

### Why qcow2 Overlays?
1. **Instant Provisioning**: Creating a delta overlay takes < 50ms compared to copying gigabytes of raw disk images.
2. **Storage Efficiency**: Multiple VMs share the immutable base OS sectors.
3. **Safety**: The base golden image is never modified.

---

## 2. Technical Truth: Local Disk vs Shared Storage Failover

In cloud hypervisor architectures, failover behavior depends entirely on storage topology:

| Scenario | Storage Location | If Node A Dies... | Can Node B Run the VM? |
| :--- | :--- | :--- | :--- |
| **Local Host Storage** *(Default MVP)* | Local NVMe/SSD on Node A | Node A hardware stops | **NO.** Node B cannot access Node A's local drive without network storage. |
| **Shared Network Storage** *(Production)* | NFS / iSCSI / Ceph SAN mount | Node A hardware stops | **YES.** Node B mounts the shared NFS directory and boots the VM XML from the existing disk. |

### Hackathon Honesty Policy
PS-023 clearly separates **Simulated Failover** (where node heartbeat loss is detected by the Controller) from **Shared-Storage Live Migration**. We do **not** claim live migration across two independent physical laptops without a shared NFS or cluster filesystem.
