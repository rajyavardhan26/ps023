import psutil
from typing import Dict, Any

def collect_host_metrics(vm_count: int = 0, is_mock: bool = False) -> Dict[str, Any]:
    """
    Collects real-time physical/virtual host hardware metrics.
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "cpu_used_percent": round(cpu_percent, 1),
        "cpu_count": psutil.cpu_count(logical=True),
        "memory_total_mb": round(mem.total / (1024 * 1024)),
        "memory_used_mb": round(mem.used / (1024 * 1024)),
        "memory_free_mb": round(mem.available / (1024 * 1024)),
        "disk_total_gb": round(disk.total / (1024 * 1024 * 1024), 1),
        "disk_free_gb": round(disk.free / (1024 * 1024 * 1024), 1),
        "vm_count": vm_count,
        "is_mock": is_mock
    }
