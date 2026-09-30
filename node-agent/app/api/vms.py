from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Request, HTTPException, Header, status
from app.config import settings

router = APIRouter(prefix="/agent/vms", tags=["Agent VM Management"])

def verify_agent_token(x_node_token: str = Header(None)):
    if not x_node_token or x_node_token != settings.NODE_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid X-Node-Token"
        )
    return True

class AgentVMCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    cpu: int = Field(default=1, ge=1, le=16)
    memory_mb: int = Field(default=1024, ge=512, le=32768)
    disk_gb: int = Field(default=10, ge=1, le=500)
    image: str = Field(default="ubuntu-24.04")

@router.get("")
def list_vms(request: Request):
    backend = request.app.state.backend
    return backend.list_vms()

@router.get("/{uuid}")
def get_vm(uuid: str, request: Request):
    backend = request.app.state.backend
    vm = backend.get_vm(uuid)
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found on this node")
    return vm

@router.post("", status_code=status.HTTP_201_CREATED)
def create_vm(
    req: AgentVMCreateRequest,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        vm = backend.create_vm(
            name=req.name,
            cpu=req.cpu,
            memory_mb=req.memory_mb,
            disk_gb=req.disk_gb,
            image=req.image
        )
        return vm
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{uuid}/start")
def start_vm(
    uuid: str,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        backend.start_vm(uuid)
        return {"status": "RUNNING", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{uuid}/stop")
def stop_vm(
    uuid: str,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        backend.stop_vm(uuid)
        return {"status": "STOPPED", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{uuid}/restart")
def restart_vm(
    uuid: str,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        backend.restart_vm(uuid)
        return {"status": "RUNNING", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{uuid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vm(
    uuid: str,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        backend.delete_vm(uuid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{uuid}/stats")
def get_vm_stats(
    uuid: str,
    request: Request,
    x_node_token: str = Header(None)
):
    verify_agent_token(x_node_token)
    backend = request.app.state.backend
    try:
        return backend.get_vm_stats(uuid)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
