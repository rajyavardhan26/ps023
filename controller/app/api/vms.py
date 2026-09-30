from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from controller.app.database import get_db
from controller.app.models import VM
from controller.app.schemas import VMCreateRequest, VMResponse
from controller.app.services.vm_service import VMService, VMServiceError
from controller.app.scheduler import SchedulingError

router = APIRouter(prefix="/vms", tags=["Virtual Machines"])

@router.get("", response_model=List[VMResponse])
def list_vms(db: Session = Depends(get_db)):
    return db.query(VM).all()

@router.get("/{vm_id}", response_model=VMResponse)
def get_vm(vm_id: int, db: Session = Depends(get_db)):
    vm = db.query(VM).filter(VM.id == vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    return vm

@router.post("", response_model=VMResponse, status_code=status.HTTP_201_CREATED)
async def create_vm(req: VMCreateRequest, db: Session = Depends(get_db)):
    try:
        return await VMService.create_vm(db, req)
    except SchedulingError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except VMServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected provisioning error: {str(e)}")

@router.post("/{vm_id}/start", response_model=VMResponse)
async def start_vm(vm_id: int, db: Session = Depends(get_db)):
    try:
        return await VMService.start_vm(db, vm_id)
    except VMServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/{vm_id}/stop", response_model=VMResponse)
async def stop_vm(vm_id: int, db: Session = Depends(get_db)):
    try:
        return await VMService.stop_vm(db, vm_id)
    except VMServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post("/{vm_id}/restart", response_model=VMResponse)
async def restart_vm(vm_id: int, db: Session = Depends(get_db)):
    try:
        return await VMService.restart_vm(db, vm_id)
    except VMServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete("/{vm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vm(vm_id: int, db: Session = Depends(get_db)):
    try:
        await VMService.delete_vm(db, vm_id)
    except VMServiceError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
