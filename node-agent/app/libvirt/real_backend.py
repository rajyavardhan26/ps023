import os
import uuid
import subprocess
import logging
from typing import Dict, List, Any, Optional

from app.libvirt.backend import VirtualizationBackend
from app.libvirt.xml_generator import generate_domain_xml
from app.config import settings

logger = logging.getLogger("node.real_backend")

try:
    import libvirt
    LIBVIRT_AVAILABLE = True
except ImportError:
    libvirt = None
    LIBVIRT_AVAILABLE = False

class RealLibvirtBackend(VirtualizationBackend):
    """
    Production-grade libvirt/KVM backend interfacing directly with QEMU hypervisor.
    """

    def __init__(self, uri: str = "qemu:///system"):
        if not LIBVIRT_AVAILABLE:
            raise RuntimeError(
                "libvirt-python is not installed. Run 'sudo dnf install python3-libvirt' or pip install libvirt-python"
            )
        self.uri = uri
        self._ensure_storage_dir()

    def _ensure_storage_dir(self):
        os.makedirs(settings.VM_STORAGE_DIR, exist_ok=True)
        os.makedirs(settings.BASE_IMAGE_DIR, exist_ok=True)

    def _get_connection(self):
        try:
            conn = libvirt.open(self.uri)
            if not conn:
                raise RuntimeError(f"Failed to open connection to libvirt URI: {self.uri}")
            return conn
        except libvirt.libvirtError as e:
            logger.error(f"Libvirt connection error: {e}")
            raise RuntimeError(f"Cannot connect to libvirt ({self.uri}): {e}")

    def create_vm(self, name: str, cpu: int, memory_mb: int, disk_gb: int, image: str) -> Dict[str, Any]:
        vm_uuid = str(uuid.uuid4())
        disk_path = os.path.join(settings.VM_STORAGE_DIR, f"{name}.qcow2")
        base_image_path = os.path.join(settings.BASE_IMAGE_DIR, f"{image}.qcow2")

        if os.path.exists(base_image_path):
            cmd = ["qemu-img", "create", "-f", "qcow2", "-b", base_image_path, "-F", "qcow2", disk_path, f"{disk_gb}G"]
        else:
            logger.warning(f"Base image '{base_image_path}' not found. Creating blank {disk_gb}G qcow2 disk.")
            cmd = ["qemu-img", "create", "-f", "qcow2", disk_path, f"{disk_gb}G"]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"qemu-img disk creation failed: {e.stderr.decode()}")

        xml_content = generate_domain_xml(
            name=name,
            uuid_str=vm_uuid,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_path=disk_path
        )

        conn = self._get_connection()
        try:
            dom = conn.defineXML(xml_content)
            if not dom:
                raise RuntimeError(f"Failed to define libvirt domain for {name}")
            dom.create()
            logger.info(f"Successfully launched KVM domain {name} ({vm_uuid})")
            return {
                "uuid": vm_uuid,
                "name": name,
                "status": "RUNNING",
                "cpu": cpu,
                "memory_mb": memory_mb,
                "disk_gb": disk_gb,
                "image": image,
                "ip_address": None
            }
        finally:
            conn.close()

    def start_vm(self, vm_uuid: str) -> bool:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            if not dom.isActive():
                dom.create()
            return True
        finally:
            conn.close()

    def stop_vm(self, vm_uuid: str) -> bool:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            if dom.isActive():
                dom.destroy()
            return True
        finally:
            conn.close()

    def restart_vm(self, vm_uuid: str) -> bool:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            if dom.isActive():
                dom.reboot(0)
            else:
                dom.create()
            return True
        finally:
            conn.close()

    def delete_vm(self, vm_uuid: str) -> bool:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            name = dom.name()
            if dom.isActive():
                dom.destroy()
            dom.undefine()
            disk_path = os.path.join(settings.VM_STORAGE_DIR, f"{name}.qcow2")
            if os.path.exists(disk_path):
                os.remove(disk_path)
            return True
        finally:
            conn.close()

    def get_vm(self, vm_uuid: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            return self._domain_to_dict(dom)
        except Exception:
            return None
        finally:
            conn.close()

    def list_vms(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            domains = conn.listAllDomains(0)
            return [self._domain_to_dict(d) for d in domains]
        finally:
            conn.close()

    def get_vm_stats(self, vm_uuid: str) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            dom = conn.lookupByUUIDString(vm_uuid)
            info = dom.info()
            return {
                "uuid": vm_uuid,
                "status": "RUNNING" if dom.isActive() else "STOPPED",
                "max_mem_kib": info[1],
                "memory_used_kib": info[2],
                "vcpus": info[3],
                "cpu_time_ns": info[4]
            }
        finally:
            conn.close()

    def _domain_to_dict(self, dom) -> Dict[str, Any]:
        status_map = {
            libvirt.VIR_DOMAIN_NOSTATE: "UNKNOWN",
            libvirt.VIR_DOMAIN_RUNNING: "RUNNING",
            libvirt.VIR_DOMAIN_BLOCKED: "STOPPED",
            libvirt.VIR_DOMAIN_PAUSED: "STOPPED",
            libvirt.VIR_DOMAIN_SHUTDOWN: "STOPPED",
            libvirt.VIR_DOMAIN_SHUTOFF: "STOPPED",
            libvirt.VIR_DOMAIN_CRASHED: "ERROR",
            libvirt.VIR_DOMAIN_PMSUSPENDED: "STOPPED"
        }
        state, _ = dom.state()
        status_str = status_map.get(state, "UNKNOWN")
        
        ip_addr = None
        if dom.isActive():
            try:
                ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
                for iface_name, iface in ifaces.items():
                    for addr in iface.get('addrs', []):
                        if addr.get('type') == libvirt.VIR_IP_ADDR_TYPE_IPV4:
                            ip_addr = addr.get('addr')
                            break
            except Exception:
                pass

        return {
            "uuid": dom.UUIDString(),
            "name": dom.name(),
            "status": status_str,
            "ip_address": ip_addr
        }
