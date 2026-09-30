import asyncio
import logging
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session
from controller.app.database import SessionLocal
from controller.app.models import VM, Node, NodeStatus, VMStatus, VMEvent, EventType
from controller.app.services.node_service import NodeService
from controller.app.config import settings

logger = logging.getLogger("controller.reconciler")

async def run_reconciliation_loop():
    """
    Background worker that runs periodic health checks and state reconciliation.
    """
    logger.info("Starting background health check & reconciliation loop...")
    while True:
        try:
            db: Session = SessionLocal()
            try:
                # 1. Check for stale nodes and mark OFFLINE
                timed_out = NodeService.check_node_health(db)
                if timed_out > 0:
                    logger.warning(f"Reconciler marked {timed_out} node(s) OFFLINE")

                # 2. Check VM states on active nodes
                online_nodes = db.query(Node).filter(Node.status == NodeStatus.ONLINE).all()
                for node in online_nodes:
                    agent_url = f"http://{node.address}:{node.port}/agent/vms"
                    try:
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            res = await client.get(agent_url, headers={"X-Node-Token": settings.NODE_AUTH_TOKEN})
                            if res.status_code == 200:
                                live_vms = {v["uuid"]: v for v in res.json()}
                                node_db_vms = db.query(VM).filter(VM.node_id == node.node_id).all()
                                
                                for db_vm in node_db_vms:
                                    if db_vm.uuid in live_vms:
                                        reported_status = live_vms[db_vm.uuid].get("status")
                                        if reported_status and db_vm.actual_state.value != reported_status:
                                            logger.info(
                                                f"Reconciliation: VM '{db_vm.name}' actual state updated "
                                                f"from {db_vm.actual_state} to {reported_status}"
                                            )
                                            db_vm.actual_state = VMStatus(reported_status)
                                            db.commit()
                    except Exception as e:
                        logger.debug(f"Failed to query node {node.node_id} during reconciliation: {e}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in reconciliation loop: {e}")

        await asyncio.sleep(settings.RECONCILIATION_INTERVAL)
