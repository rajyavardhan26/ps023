from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class VirtualizationBackend(ABC):
    """
    Abstract interface for hypervisor management (real libvirt or mock engine).
    """

    @abstractmethod
    def create_vm(self, name: str, cpu: int, memory_mb: int, disk_gb: int, image: str) -> Dict[str, Any]:
        """Provisions storage, domain XML, and boots the VM."""
        pass

    @abstractmethod
    def start_vm(self, vm_uuid: str) -> bool:
        """Powers on an existing stopped VM."""
        pass

    @abstractmethod
    def stop_vm(self, vm_uuid: str) -> bool:
        """Gracefully shuts down or destroys a VM."""
        pass

    @abstractmethod
    def restart_vm(self, vm_uuid: str) -> bool:
        """Reboots a VM."""
        pass

    @abstractmethod
    def delete_vm(self, vm_uuid: str) -> bool:
        """Destroys domain and cleans up disk images."""
        pass

    @abstractmethod
    def get_vm(self, vm_uuid: str) -> Optional[Dict[str, Any]]:
        """Returns details for a single VM."""
        pass

    @abstractmethod
    def list_vms(self) -> List[Dict[str, Any]]:
        """Returns a list of all local VMs managed on this node."""
        pass

    @abstractmethod
    def get_vm_stats(self, vm_uuid: str) -> Dict[str, Any]:
        """Returns runtime CPU and memory metrics for a given VM."""
        pass
