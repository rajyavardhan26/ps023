# PS-023 Architecture Blueprint

## 1. System Overview

PS-023 is a lightweight, resource-aware, two-node Cloud Hypervisor VM Controller designed for Linux/Fedora environments using KVM, QEMU, libvirt, FastAPI, and SQLite.

```text
                           Web Dashboard (UI)
                                   |
                                REST API
                                   |
                         +---------+---------+
                         |  Central Controller |
                         |  - Scheduler       |
                         |  - Reconciliation |
                         |  - Event Audit Log |
                         |  - SQLite Database |
                         +---------+---------+
                                   |
                 +-----------------+-----------------+
                 | HTTP (Port 8001)                  | HTTP (Port 8002)
                 v                                   v
        +-----------------+                 +-----------------+
        |   Node Agent A  |                 |   Node Agent B  |
        | - Host Metrics  |                 | - Host Metrics  |
        | - libvirt / KVM |                 | - libvirt / KVM |
        +--------+--------+                 +--------+--------+
                 |                                   |
             libvirt                             libvirt
                 |                                   |
            QEMU / KVM                          QEMU / KVM
                 |                                   |
              [ VM 1 ]                            [ VM 2 ]
```

---

## 2. Core Components

### A. Central Controller (`:8000`)
- **State Store**: Embedded SQLite database (`cloud_controller.db`) tracking compute nodes, registered VMs, desired vs actual states, and audit events.
- **Resource-Aware Scheduler**: Evaluates candidate nodes using a weighted formula (45% RAM headroom, 35% CPU headroom, 20% VM count balance factor).
- **State Reconciliation Worker**: Asynchronous background loop that verifies VM actual state against desired state and automatically marks stale nodes `OFFLINE` if heartbeats lapse past `HEARTBEAT_TIMEOUT` (default: 15s).
- **Embedded Web Dashboard**: Accessible directly at `http://localhost:8000/`.

### B. Node Agents (`:8001`, `:8002`)
- **Node Self-Registration**: Automatically contacts the Controller upon boot with its hardware specifications (CPU cores, RAM capacity, IP, port).
- **Heartbeat Telemetry**: Dispatches live host CPU usage %, RAM consumption, and active VM counts every 5 seconds.
- **Virtualization Abstraction Layer**:
  - `RealLibvirtBackend`: Uses Python libvirt bindings and standard Q35/VirtIO XML templates to control KVM/QEMU directly.
  - `MockLibvirtBackend`: High-fidelity in-memory virtualization engine allowing full hackathon demonstration and multi-node testing on a single development machine without needing root privileges.
