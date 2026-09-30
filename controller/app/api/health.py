from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from controller.app.database import get_db
from controller.app.models import Node, VM, NodeStatus, VMStatus
from controller.app.schemas import SystemStatsResponse

router = APIRouter(tags=["Health & Stats"])

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ps023-cloud-controller",
        "version": "1.0.0"
    }

@router.get("/metrics", response_model=SystemStatsResponse)
def get_metrics(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()
    vms = db.query(VM).all()
    
    total_nodes = len(nodes)
    online_nodes = sum(1 for n in nodes if n.status == NodeStatus.ONLINE)
    total_vms = len(vms)
    running_vms = sum(1 for v in vms if v.actual_state == VMStatus.RUNNING)
    total_cpu_cores = sum(n.cpu_total for n in nodes if n.status == NodeStatus.ONLINE)
    allocated_memory_mb = sum(v.memory_mb for v in vms if v.actual_state == VMStatus.RUNNING)

    return SystemStatsResponse(
        total_nodes=total_nodes,
        online_nodes=online_nodes,
        total_vms=total_vms,
        running_vms=running_vms,
        total_cpu_cores=total_cpu_cores,
        allocated_memory_mb=allocated_memory_mb
    )
