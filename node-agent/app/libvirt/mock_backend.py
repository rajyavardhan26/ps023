import uuid
import time
import random
import logging
from typing import Dict, List, Any, Optional
from app.libvirt.backend import VirtualizationBackend

logger = logging.getLogger("node.mock_backend")

class MockLibvirtBackend(VirtualizationBackend):
    """
    In-memory Mock Virtualization backend for development and hackathon demonstration.
    Faithfully simulates VM states and lifecycle without needing root privileges.
    """

    def __init__(self):
        self._vms: Dict[str, Dict[str, Any]] = {}
        logger.info("[MOCK BACKEND] Initialized mock virtualization engine.")

    def create_vm(self, name: str, cpu: int, memory_mb: int, disk_gb: int, image: str) -> Dict[str, Any]:
        vm_uuid = str(uuid.uuid4())
        ip_suffix = random.randint(10, 250)
        simulated_ip = f"192.168.122.{ip_suffix}"
        
        vm_data = {
            "uuid": vm_uuid,
            "name": name,
            "status": "RUNNING",
            "cpu": cpu,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb,
            "image": image,
            "ip_address": simulated_ip,
            "created_at": time.time(),
            "cpu_time_ns": 0
        }
        self._vms[vm_uuid] = vm_data
        logger.info(f"[MOCK BACKEND] Created virtual domain '{name}' (UUID: {vm_uuid}, IP: {simulated_ip})")
        return vm_data

    def start_vm(self, vm_uuid: str) -> bool:
        if vm_uuid not in self._vms:
            raise ValueError(f"VM '{vm_uuid}' does not exist.")
        self._vms[vm_uuid]["status"] = "RUNNING"
        logger.info(f"[MOCK BACKEND] VM '{vm_uuid}' transitioned to RUNNING")
        return True

    def stop_vm(self, vm_uuid: str) -> bool:
        if vm_uuid not in self._vms:
            raise ValueError(f"VM '{vm_uuid}' does not exist.")
        self._vms[vm_uuid]["status"] = "STOPPED"
        logger.info(f"[MOCK BACKEND] VM '{vm_uuid}' transitioned to STOPPED")
        return True

    def restart_vm(self, vm_uuid: str) -> bool:
        self.stop_vm(vm_uuid)
        time.sleep(0.5)
        self.start_vm(vm_uuid)
        logger.info(f"[MOCK BACKEND] VM '{vm_uuid}' restarted")
        return True

    def delete_vm(self, vm_uuid: str) -> bool:
        if vm_uuid not in self._vms:
            raise ValueError(f"VM '{vm_uuid}' does not exist.")
        del self._vms[vm_uuid]
        logger.info(f"[MOCK BACKEND] Deleted VM '{vm_uuid}' and released resources")
        return True

    def get_vm(self, vm_uuid: str) -> Optional[Dict[str, Any]]:
        return self._vms.get(vm_uuid)

    def list_vms(self) -> List[Dict[str, Any]]:
        return list(self._vms.values())

    def get_vm_stats(self, vm_uuid: str) -> Dict[str, Any]:
        vm = self._vms.get(vm_uuid)
        if not vm:
            raise ValueError(f"VM '{vm_uuid}' not found.")
        
        if vm["status"] == "RUNNING":
            cpu_usage = round(random.uniform(5.0, 35.0), 2)
            mem_usage = round(random.uniform(256.0, float(vm["memory_mb"])), 2)
        else:
            cpu_usage = 0.0
            mem_usage = 0.0

        return {
            "uuid": vm_uuid,
            "status": vm["status"],
            "cpu_usage_percent": cpu_usage,
            "memory_used_mb": mem_usage,
            "memory_total_mb": vm["memory_mb"]
        }
