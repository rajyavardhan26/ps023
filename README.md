# PS-023: Minimal Two-Node Cloud Hypervisor VM Controller

A clean, hackathon-ready, lightweight distributed Cloud Hypervisor VM Controller designed for Linux/Fedora. Built from scratch with **Python 3**, **FastAPI**, **libvirt**, **KVM/QEMU**, **SQLite**, and native **Fish shell** automation.

```text
                       Web Dashboard (Port 8000)
                                 │
                            REST API
                                 ▼
                    ┌─────────────────────────┐
                    │    Central Controller   │
                    │   - Admission Scheduler │
                    │   - SQLite Persistence  │
                    │   - State Reconciler    │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┴───────────────┐
                 │ HTTP (:8001)                  │ HTTP (:8002)
                 ▼                               ▼
        ┌─────────────────┐             ┌─────────────────┐
        │   Node Agent A  │             │   Node Agent B  │
        │  (libvirt/KVM)  │             │  (libvirt/KVM)  │
        └────────┬────────┘             └────────┬────────┘
                 ▼                               ▼
            [ VM Alpha ]                    [ VM Beta ]
```

---

## 1. Features

- **Automated Node Self-Registration**: Node Agents register their hardware specs (vCPU count, RAM capacity) with the Central Controller upon boot.
- **Heartbeat & Liveness Tracking**: Continuous telemetry (CPU %, RAM MB, VM counts) sent every 5 seconds. Nodes missing heartbeats for > 15 seconds are automatically marked `OFFLINE`.
- **Resource-Aware Scheduling**: Mathematically scores candidate nodes based on available RAM headroom, CPU headroom, and VM distribution balance.
- **Full VM Lifecycle**: Create, start, stop, restart, delete, inspect, and monitor virtual machines via REST or the embedded web dashboard.
- **Dual-Mode Virtualization**:
  - **Real KVM Mode**: Interacts directly with Linux KVM/QEMU via Python libvirt bindings and standard XML domain templates.
  - **Mock Demo Mode**: High-fidelity in-memory virtualization engine allowing two simulated nodes to run simultaneously on a single laptop without root privileges.
- **State Reconciliation**: Continually verifies that hypervisor actual states match requested desired states.
- **Cluster Audit Log**: Structured audit events tracking all cluster lifecycle changes.
- **100% Fish Shell Native**: All operational scripts are written for the Fish shell.

---

## 2. Quickstart (Fish Shell)

From the project root directory:

```fish
# 1. Bootstrap environment and install dependencies
./scripts/bootstrap.fish

# 2. Launch Controller, Node Agent A, and Node Agent B
./scripts/start-all.fish

# 3. Open the Dashboard in your browser
xdg-open http://localhost:8000
```

To run the automated test suite:
```fish
./scripts/test.fish
```

To run the live performance benchmark:
```fish
./scripts/benchmark.fish
```

To stop all background cluster services:
```fish
./scripts/stop-all.fish
```

---

## 3. Two-Node Architecture Modes

### Development Mode (Single Laptop)
- **Controller**: `http://localhost:8000`
- **Node Agent A**: `http://localhost:8001`
- **Node Agent B**: `http://localhost:8002`
- Both agents run locally with `DEMO_MODE=true` or separate libvirt sessions.

### Physical Two-Node Deployment (Two Separate Linux Machines)
- **Machine 1 (Node A)**: Run `./scripts/start-node-a.fish` with `NODE_HOST=192.168.1.10`, `CONTROLLER_URL=http://192.168.1.5:8000`
- **Machine 2 (Node B)**: Run `./scripts/start-node-b.fish` with `NODE_HOST=192.168.1.11`, `CONTROLLER_URL=http://192.168.1.5:8000`
- **Controller Server**: Run `./scripts/start-controller.fish` on `192.168.1.5:8000`

---

## 4. Feature Implementation Honesty Matrix

| Capability | Status | Implementation Details |
| :--- | :--- | :--- |
| **REST API VM Controller** | **Implemented** | FastAPI with Pydantic validation and SQLite persistence |
| **Two-Node Support** | **Implemented** | Independent agents running on distinct ports/hosts |
| **Resource-Aware Scheduler** | **Implemented** | Real weighted scoring (RAM, CPU, VM balance) |
| **Node Heartbeats & Timeouts** | **Implemented** | 5s heartbeats with 15s timeout detection |
| **Embedded Web Dashboard** | **Implemented** | Live auto-refreshing UI with action buttons & audit logs |
| **KVM/libvirt Integration** | **Implemented** | Python libvirt bindings with Q35 domain XML generation |
| **Mock Engine** | **Implemented** | Allows full simulation on a single laptop |
| **Failure Detection** | **Implemented** | Heartbeat timeout detects down nodes automatically |
| **Live Migration across nodes**| **Not Implemented** | Requires shared NFS/SAN network storage (documented in `docs/storage.md`) |
