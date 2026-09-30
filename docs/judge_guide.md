# Hackathon Defense Guide: PS-023

## 1. Project Pitches

### 30-Second Elevator Pitch
"PS-023 is a lightweight, two-node Cloud Hypervisor VM Controller written in Python and FastAPI. Rather than relying on massive enterprise systems like OpenStack or Kubernetes, it directly orchestrates KVM/QEMU hypervisors through a clean libvirt abstraction layer. It implements automated node self-registration, periodic health heartbeats, resource-aware placement scheduling, and asynchronous state reconciliation with a live web dashboard."

### 1-Minute Pitch
"In cloud computing, managing VMs across distributed hardware requires coordination between a central control plane and local hypervisor agents. We built PS-023 to solve this with minimal complexity:
1. **Central Controller**: Maintains cluster state in SQLite, runs a weighted resource-aware scheduler balancing CPU and RAM headroom, and performs background state reconciliation.
2. **Node Agents**: Run on physical hypervisors, report live telemetry, and control KVM using standard libvirt Q35/VirtIO XML templates and qcow2 storage overlays.
3. **Resilience**: If a node stops sending heartbeats, the reconciler automatically detects the failure and marks it offline, while keeping audit logs of every cluster event."

### 3-Minute Technical Walkthrough
- Walk through the three tiers: Central Controller (`:8000`), Node Agent A (`:8001`), and Node Agent B (`:8002`).
- Demonstrate VM provisioning: Controller checks capacity, scheduler computes normalized resource scores, sends a cryptographically authenticated payload (`X-Node-Token`) to the selected node agent, which defines and boots the VM domain.
- Explain the dual-backend architecture: `RealLibvirtBackend` for hardware KVM virtualization, and `MockLibvirtBackend` for rapid developer simulation on a single laptop.

---

## 2. 30 Critical Judge Questions & Honest Technical Answers

1. **Why KVM over containers/Docker?**
   *Answer*: Containers share the host Linux kernel, whereas KVM provides hardware-assisted, full virtualization with dedicated kernels, memory isolation, and arbitrary operating systems.

2. **Why QEMU with KVM?**
   *Answer*: KVM is the Linux kernel module providing hardware CPU/MMU virtualization; QEMU provides hardware device emulation (disk, network, serial). Together, they form the standard Linux hypervisor.

3. **Why libvirt instead of calling `qemu-system-x86_64` directly?**
   *Answer*: Direct QEMU commands require complex, error-prone 50-line command lines and lack standardized domain lifecycle management, security isolation (sVirt/SELinux), and network bridge orchestration, which libvirt provides.

4. **Why not OpenStack?**
   *Answer*: OpenStack involves dozens of services (Nova, Neutron, Glance, Keystone, RabbitMQ, MariaDB) requiring tens of gigabytes of RAM. PS-023 implements the essential hypervisor scheduling and lifecycle concepts in ~1,000 lines of readable code.

5. **Where are the VM disk images stored?**
   *Answer*: On local node storage as qcow2 Copy-on-Write overlays pointing to an immutable base golden image.

6. **Can Node B run a VM if Node A crashes?**
   *Answer*: In local storage mode, no, because the disk bits physically reside on Node A. In shared storage mode (e.g. NFS mount), Node B can immediately launch the VM from the shared disk.

7. **How does your scheduler work?**
   *Answer*: It filters for `ONLINE` nodes, verifies that free RAM satisfies the VM requirement, and evaluates a composite score: `0.45 * Free_RAM + 0.35 * Free_CPU + 0.20 * VM_Balance`.

8. **How do you prevent over-allocation?**
   *Answer*: The scheduler performs strict admission control: any node with remaining memory less than the requested amount is assigned a negative score and eliminated.

9. **What happens if the Central Controller crashes?**
   *Answer*: The VMs on Node A and Node B continue running uninterrupted because libvirt runs domains as separate processes. When the Controller restarts, its reconciliation loop queries the nodes to recover the live state.

10. **How do nodes authenticate with the Controller?**
    *Answer*: Using pre-shared API security tokens passed via the `X-Node-Token` HTTP header on all inter-service requests.

11. **What is Desired State vs Actual State?**
    *Answer*: Desired state is what the user/database requested (e.g. `RUNNING`). Actual state is what the hypervisor reports (e.g. `STOPPED` if the guest crashed). The reconciler detects and logs discrepancies.

12. **How does the system detect that a node is down?**
    *Answer*: Each node transmits a heartbeat every 5 seconds. If the Controller does not receive a heartbeat for > 15 seconds, the node status is transitioned to `OFFLINE`.

13. **Why did you use SQLite instead of PostgreSQL?**
    *Answer*: For the MVP, SQLite requires zero setup, is embedded in-process, supports WAL mode for concurrency, and eliminates external database dependencies.

14. **Why did you choose FastAPI?**
    *Answer*: It offers native asynchronous support, automatic OpenAPI/Swagger documentation, strict Pydantic data validation, and high performance with uvicorn.

15. **How are VMs isolated from each other?**
    *Answer*: At the hardware level via KVM CPU rings and EPT (Extended Page Tables), and at the network level via distinct virtual interfaces connected to the libvirt bridge.

16. **Why do you use `qcow2` instead of `raw` images?**
    *Answer*: `qcow2` supports thin provisioning, snapshotting, and backing-file overlays, allowing instant VM creation without duplicating base OS files.

17. **What is cloud-init?**
    *Answer*: An industry standard multi-distribution tool that configures user accounts, SSH keys, and network settings upon the VM's first boot via a virtual ISO or NoCloud metadata.

18. **Why do you have a Mock mode?**
    *Answer*: To enable two-node distributed testing and rapid development on a single laptop without needing root access, nested virtualization, or multiple physical machines.

19. **How would you scale this to 100 nodes?**
    *Answer*: Replace SQLite with PostgreSQL, add an event queue for asynchronous provisioning, and group nodes into availability zones.

20. **Is live migration implemented?**
    *Answer*: Live migration is an engineering enhancement requiring shared NFS/SAN storage and identical CPU feature flags; in our local MVP, we simulate failure detection honestly rather than faking migration.
