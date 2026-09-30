# PS-023 Troubleshooting & Debugging Guide

### 1. `/dev/kvm` does not exist or permission denied
- **Symptom**: `RuntimeError: /dev/kvm not found`
- **Cause**: AMD-V/Intel VT-x disabled in BIOS/UEFI, or current user is not in `kvm` group.
- **Diagnostic**: `ls -la /dev/kvm`
- **Fix**:
  ```fish
  sudo usermod -aG kvm (whoami)
  sudo usermod -aG libvirt (whoami)
  newgrp kvm
  ```

### 2. `qemu:///system` connection failed
- **Symptom**: `libvirtError: Failed to connect socket to '/run/user/1000/libvirt/virtqemud-sock'`
- **Cause**: libvirt system daemon is not started.
- **Diagnostic**: `systemctl status libvirtd` or `systemctl status virtqemud`
- **Fix**:
  ```fish
  sudo systemctl enable --now libvirtd
  ```

### 3. Port already in use (8000, 8001, 8002)
- **Symptom**: `OSError: [Errno 98] address already in use`
- **Cause**: Previous background uvicorn instances are still running.
- **Fix**:
  ```fish
  ./scripts/stop-all.fish
  ```

### 4. Node heartbeat timeout (Node marked OFFLINE)
- **Symptom**: Node status turns red (`OFFLINE`) on the dashboard after 15 seconds.
- **Cause**: Node Agent process crashed or network latency exceeded `HEARTBEAT_TIMEOUT`.
- **Diagnostic**: Check `logs/node-a.log` or `logs/node-b.log`.
