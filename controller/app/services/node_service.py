import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from controller.app.models import Node, NodeStatus, VMEvent, EventType
from controller.app.schemas import NodeRegisterRequest, NodeHeartbeatRequest
from controller.app.config import settings

logger = logging.getLogger("controller.node_service")

class NodeService:

    @staticmethod
    def register_node(db: Session, req: NodeRegisterRequest) -> Node:
        existing = db.query(Node).filter(Node.node_id == req.node_id).first()
        now = datetime.now(timezone.utc)
        if existing:
            logger.info(f"Re-registering existing node: {req.node_id}")
            existing.hostname = req.hostname
            existing.address = req.address
            existing.port = req.port
            existing.cpu_total = req.cpu_total
            existing.memory_total = req.memory_total
            existing.is_mock = req.is_mock
            existing.status = NodeStatus.ONLINE
            existing.last_seen = now
            node = existing
        else:
            logger.info(f"Registering new node: {req.node_id} ({req.address}:{req.port})")
            node = Node(
                node_id=req.node_id,
                hostname=req.hostname,
                address=req.address,
                port=req.port,
                status=NodeStatus.ONLINE,
                last_seen=now,
                cpu_total=req.cpu_total,
                memory_total=req.memory_total,
                is_mock=req.is_mock
            )
            db.add(node)

        # Audit event
        event = VMEvent(
            event_type=EventType.NODE_ONLINE,
            node_id=req.node_id,
            message=f"Node {req.node_id} registered and marked ONLINE ({req.address}:{req.port})",
            level="INFO"
        )
        db.add(event)
        db.commit()
        db.refresh(node)
        return node

    @staticmethod
    def record_heartbeat(db: Session, hb: NodeHeartbeatRequest) -> Optional[Node]:
        node = db.query(Node).filter(Node.node_id == hb.node_id).first()
        if not node:
            return None

        previous_status = node.status
        node.last_seen = datetime.now(timezone.utc)
        node.cpu_used_percent = hb.cpu_used_percent
        node.memory_used_mb = hb.memory_used_mb
        node.status = NodeStatus.ONLINE
        node.is_mock = hb.is_mock

        if previous_status == NodeStatus.OFFLINE:
            event = VMEvent(
                event_type=EventType.NODE_ONLINE,
                node_id=node.node_id,
                message=f"Node {node.node_id} recovered and is back ONLINE",
                level="INFO"
            )
            db.add(event)

        db.commit()
        return node

    @staticmethod
    def check_node_health(db: Session) -> int:
        """
        Marks nodes OFFLINE if their heartbeat exceeds HEARTBEAT_TIMEOUT.
        """
        timeout_threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.HEARTBEAT_TIMEOUT)
        stale_nodes = db.query(Node).filter(
            Node.status == NodeStatus.ONLINE,
            Node.last_seen < timeout_threshold
        ).all()

        count = 0
        for node in stale_nodes:
            logger.warning(f"Node {node.node_id} missed heartbeats. Marking OFFLINE.")
            node.status = NodeStatus.OFFLINE
            event = VMEvent(
                event_type=EventType.NODE_OFFLINE,
                node_id=node.node_id,
                message=f"Node {node.node_id} heartbeat timed out (> {settings.HEARTBEAT_TIMEOUT}s). Marked OFFLINE.",
                level="WARNING"
            )
            db.add(event)
            count += 1

        if count > 0:
            db.commit()
        return count
