from typing import List
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from controller.app.database import get_db
from controller.app.models import Node, NodeStatus, VMEvent, EventType
from controller.app.schemas import NodeRegisterRequest, NodeHeartbeatRequest, NodeResponse
from controller.app.services.node_service import NodeService
from controller.app.config import settings

router = APIRouter(prefix="/nodes", tags=["Nodes"])

def verify_node_token(x_node_token: str = Header(None)):
    if not x_node_token or x_node_token != settings.NODE_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Node-Token header"
        )
    return True

@router.get("", response_model=List[NodeResponse])
def list_nodes(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()
    # Populate live VM count for response
    results = []
    for n in nodes:
        resp = NodeResponse.model_validate(n)
        resp.vm_count = len(n.vms) if n.vms else 0
        results.append(resp)
    return results

@router.get("/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    resp = NodeResponse.model_validate(node)
    resp.vm_count = len(node.vms) if node.vms else 0
    return resp

@router.post("/register", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def register_node(
    req: NodeRegisterRequest,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_node_token)
):
    node = NodeService.register_node(db, req)
    resp = NodeResponse.model_validate(node)
    resp.vm_count = len(node.vms) if node.vms else 0
    return resp

@router.post("/heartbeat")
def heartbeat(
    hb: NodeHeartbeatRequest,
    db: Session = Depends(get_db),
    authorized: bool = Depends(verify_node_token)
):
    node = NodeService.record_heartbeat(db, hb)
    if not node:
        raise HTTPException(status_code=404, detail=f"Unregistered node '{hb.node_id}'. Register first.")
    return {"status": "acknowledged", "node_id": hb.node_id}

@router.post("/{node_id}/simulate-failure")
def simulate_failure(node_id: str, db: Session = Depends(get_db)):
    """
    Simulation endpoint to demonstrate node failure detection.
    Sets last_seen to 60 seconds ago and status to OFFLINE.
    """
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.status = NodeStatus.OFFLINE
    node.last_seen = datetime.now(timezone.utc) - timedelta(seconds=60)
    db.add(VMEvent(
        event_type=EventType.NODE_OFFLINE,
        node_id=node.node_id,
        message=f"[DEMO SIMULATION] Node {node.node_id} manually forced to OFFLINE for failure demonstration",
        level="WARNING"
    ))
    db.commit()
    return {"message": f"Node {node_id} marked OFFLINE for simulation"}
