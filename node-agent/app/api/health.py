from fastapi import APIRouter, Request
from app.monitoring.metrics import collect_host_metrics
from app.config import settings

router = APIRouter(tags=["Agent Health"])

@router.get("/agent/health")
def agent_health(request: Request):
    backend = request.app.state.backend
    vms = backend.list_vms()
    return {
        "status": "healthy",
        "node_id": settings.NODE_ID,
        "mode": "MOCK" if settings.DEMO_MODE else "REAL_KVM",
        "active_vms": len(vms)
    }

@router.get("/agent/metrics")
def agent_metrics(request: Request):
    backend = request.app.state.backend
    vms = backend.list_vms()
    return collect_host_metrics(vm_count=len(vms), is_mock=settings.DEMO_MODE)
