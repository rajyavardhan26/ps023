import asyncio
import logging
import httpx
from app.config import settings
from app.monitoring.metrics import collect_host_metrics
from app.libvirt.backend import VirtualizationBackend

logger = logging.getLogger("node.agent_service")

class AgentService:
    def __init__(self, backend: VirtualizationBackend):
        self.backend = backend
        self._running = False
        self._heartbeat_task = None

    async def register_with_controller(self, max_retries: int = 5):
        """
        Registers this Node Agent with the Central Cloud Controller.
        """
        metrics = collect_host_metrics()
        payload = {
            "node_id": settings.NODE_ID,
            "hostname": settings.HOSTNAME,
            "address": settings.NODE_HOST,
            "port": settings.NODE_PORT,
            "cpu_total": metrics["cpu_count"],
            "memory_total": metrics["memory_total_mb"],
            "is_mock": settings.DEMO_MODE
        }
        headers = {"X-Node-Token": settings.NODE_AUTH_TOKEN}
        url = f"{settings.CONTROLLER_URL}/nodes/register"

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code in [200, 201]:
                        logger.info(f"Node '{settings.NODE_ID}' successfully registered with Controller at {url}")
                        return True
                    else:
                        logger.warning(f"Registration rejected (HTTP {res.status_code}): {res.text}")
            except Exception as e:
                logger.warning(f"Registration attempt {attempt}/{max_retries} failed: {e}")

            await asyncio.sleep(2.0)

        logger.error("Could not register with Controller. Proceeding (will retry on heartbeats).")
        return False

    async def start_heartbeat_loop(self):
        """
        Periodically transmits live CPU, Memory, and VM count to Controller.
        """
        self._running = True
        logger.info(f"Starting heartbeat loop for node '{settings.NODE_ID}' (every {settings.HEARTBEAT_INTERVAL}s)")
        
        while self._running:
            try:
                vms = self.backend.list_vms()
                metrics = collect_host_metrics(vm_count=len(vms), is_mock=settings.DEMO_MODE)
                
                payload = {
                    "node_id": settings.NODE_ID,
                    "cpu_used_percent": metrics["cpu_used_percent"],
                    "memory_used_mb": metrics["memory_used_mb"],
                    "vm_count": len(vms),
                    "is_mock": settings.DEMO_MODE
                }
                headers = {"X-Node-Token": settings.NODE_AUTH_TOKEN}
                url = f"{settings.CONTROLLER_URL}/nodes/heartbeat"

                async with httpx.AsyncClient(timeout=4.0) as client:
                    res = await client.post(url, json=payload, headers=headers)
                    if res.status_code != 200:
                        logger.warning(f"Heartbeat unacknowledged: {res.status_code} - {res.text}")
            except Exception as e:
                logger.debug(f"Heartbeat dispatch failed: {e}")

            await asyncio.sleep(settings.HEARTBEAT_INTERVAL)

    def stop(self):
        self._running = False
