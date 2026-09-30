import logging
import httpx
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from controller.app.models import VM, Node, NodeStatus, VMStatus, VMEvent, EventType
from controller.app.schemas import VMCreateRequest
from controller.app.scheduler import ResourceAwareScheduler, SchedulingError
from controller.app.config import settings

logger = logging.getLogger("controller.vm_service")

class VMServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

class VMService:

    @staticmethod
    def _get_node_headers() -> dict:
        return {"X-Node-Token": settings.NODE_AUTH_TOKEN}

    @classmethod
    async def create_vm(cls, db: Session, req: VMCreateRequest) -> VM:
        # Check duplicate name
        existing = db.query(VM).filter(VM.name == req.name).first()
        if existing:
            raise VMServiceError(f"A VM with name '{req.name}' already exists.", 409)

        # Retrieve eligible nodes
        nodes = db.query(Node).all()
        selected_node = ResourceAwareScheduler.select_node(req, nodes)

        # Initial DB record
        vm = VM(
            name=req.name,
            node_id=selected_node.node_id,
            desired_state=VMStatus.RUNNING,
            actual_state=VMStatus.CREATING,
            cpu=req.cpu,
            memory_mb=req.memory_mb,
            disk_gb=req.disk_gb,
            image=req.image
        )
        db.add(vm)
        db.commit()
        db.refresh(vm)

        # Audit Event
        db.add(VMEvent(
            event_type=EventType.VM_CREATED,
            vm_id=vm.id,
            vm_name=vm.name,
            node_id=selected_node.node_id,
            message=f"VM '{vm.name}' scheduled onto node '{selected_node.node_id}'"
        ))
        db.commit()

        # Send provisioning request to Node Agent
        agent_url = f"http://{selected_node.address}:{selected_node.port}/agent/vms"
        payload = {
            "name": vm.name,
            "cpu": vm.cpu,
            "memory_mb": vm.memory_mb,
            "disk_gb": vm.disk_gb,
            "image": vm.image
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                res = await client.post(agent_url, json=payload, headers=cls._get_node_headers())
                if res.status_code != 201:
                    raise Exception(f"Node agent returned {res.status_code}: {res.text}")
                data = res.json()
                vm.uuid = data.get("uuid")
                vm.actual_state = VMStatus.RUNNING
                vm.ip_address = data.get("ip_address")
                vm.error_message = None
                
                db.add(VMEvent(
                    event_type=EventType.VM_STARTED,
                    vm_id=vm.id,
                    vm_name=vm.name,
                    node_id=selected_node.node_id,
                    message=f"VM '{vm.name}' successfully provisioned and started on node '{selected_node.node_id}'"
                ))
                db.commit()
                db.refresh(vm)
                return vm
        except Exception as e:
            logger.error(f"Failed to provision VM {vm.name} on {selected_node.node_id}: {e}")
            vm.actual_state = VMStatus.ERROR
            vm.error_message = str(e)
            db.add(VMEvent(
                event_type=EventType.VM_FAILED,
                vm_id=vm.id,
                vm_name=vm.name,
                node_id=selected_node.node_id,
                message=f"Provisioning error for VM '{vm.name}': {str(e)}",
                level="ERROR"
            ))
            db.commit()
            raise VMServiceError(f"Node Agent failed to launch VM: {str(e)}", 500)

    @classmethod
    async def start_vm(cls, db: Session, vm_id: int) -> VM:
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            raise VMServiceError("VM not found", 404)
        if not vm.node or vm.node.status == NodeStatus.OFFLINE:
            raise VMServiceError(f"Host node '{vm.node_id}' is OFFLINE", 503)

        vm.desired_state = VMStatus.RUNNING
        node = vm.node
        agent_url = f"http://{node.address}:{node.port}/agent/vms/{vm.uuid}/start"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(agent_url, headers=cls._get_node_headers())
                if res.status_code != 200:
                    raise Exception(res.text)
                vm.actual_state = VMStatus.RUNNING
                vm.error_message = None
                db.add(VMEvent(
                    event_type=EventType.VM_STARTED,
                    vm_id=vm.id,
                    vm_name=vm.name,
                    node_id=vm.node_id,
                    message=f"VM '{vm.name}' power-on requested and running"
                ))
                db.commit()
                db.refresh(vm)
                return vm
        except Exception as e:
            vm.actual_state = VMStatus.ERROR
            vm.error_message = str(e)
            db.commit()
            raise VMServiceError(f"Failed to start VM: {e}", 500)

    @classmethod
    async def stop_vm(cls, db: Session, vm_id: int) -> VM:
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            raise VMServiceError("VM not found", 404)
        if not vm.node or vm.node.status == NodeStatus.OFFLINE:
            raise VMServiceError(f"Host node '{vm.node_id}' is OFFLINE", 503)

        vm.desired_state = VMStatus.STOPPED
        node = vm.node
        agent_url = f"http://{node.address}:{node.port}/agent/vms/{vm.uuid}/stop"

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.post(agent_url, headers=cls._get_node_headers())
                if res.status_code != 200:
                    raise Exception(res.text)
                vm.actual_state = VMStatus.STOPPED
                db.add(VMEvent(
                    event_type=EventType.VM_STOPPED,
                    vm_id=vm.id,
                    vm_name=vm.name,
                    node_id=vm.node_id,
                    message=f"VM '{vm.name}' shut down successfully"
                ))
                db.commit()
                db.refresh(vm)
                return vm
        except Exception as e:
            db.commit()
            raise VMServiceError(f"Failed to stop VM: {e}", 500)

    @classmethod
    async def restart_vm(cls, db: Session, vm_id: int) -> VM:
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            raise VMServiceError("VM not found", 404)
        if not vm.node or vm.node.status == NodeStatus.OFFLINE:
            raise VMServiceError(f"Host node '{vm.node_id}' is OFFLINE", 503)

        node = vm.node
        agent_url = f"http://{node.address}:{node.port}/agent/vms/{vm.uuid}/restart"

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                res = await client.post(agent_url, headers=cls._get_node_headers())
                if res.status_code != 200:
                    raise Exception(res.text)
                vm.desired_state = VMStatus.RUNNING
                vm.actual_state = VMStatus.RUNNING
                db.add(VMEvent(
                    event_type=EventType.VM_RESTARTED,
                    vm_id=vm.id,
                    vm_name=vm.name,
                    node_id=vm.node_id,
                    message=f"VM '{vm.name}' restarted"
                ))
                db.commit()
                db.refresh(vm)
                return vm
        except Exception as e:
            raise VMServiceError(f"Failed to restart VM: {e}", 500)

    @classmethod
    async def delete_vm(cls, db: Session, vm_id: int) -> None:
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if not vm:
            raise VMServiceError("VM not found", 404)

        node = vm.node
        # If node is online and uuid is present, request deletion on agent
        if node and node.status == NodeStatus.ONLINE and vm.uuid:
            agent_url = f"http://{node.address}:{node.port}/agent/vms/{vm.uuid}"
            try:
                async with httpx.AsyncClient(timeout=20.0) as client:
                    await client.delete(agent_url, headers=cls._get_node_headers())
            except Exception as e:
                logger.warning(f"Could not contact node agent to delete VM files: {e}")

        vm_name = vm.name
        node_id = vm.node_id
        db.delete(vm)
        db.add(VMEvent(
            event_type=EventType.VM_DELETED,
            vm_id=vm_id,
            vm_name=vm_name,
            node_id=node_id,
            message=f"VM '{vm_name}' removed from cluster"
        ))
        db.commit()
