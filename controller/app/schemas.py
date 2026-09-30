from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from controller.app.models import NodeStatus, VMStatus, EventType

class NodeRegisterRequest(BaseModel):
    node_id: str = Field(..., json_schema_extra={"example": "node-a"})
    hostname: str = Field(..., json_schema_extra={"example": "fedora-worker-1"})
    address: str = Field(..., json_schema_extra={"example": "127.0.0.1"})
    port: int = Field(..., json_schema_extra={"example": 8001})
    cpu_total: int = Field(default=8)
    memory_total: int = Field(default=16384)
    is_mock: bool = Field(default=False)

class NodeHeartbeatRequest(BaseModel):
    node_id: str
    cpu_used_percent: float
    memory_used_mb: int
    vm_count: int
    is_mock: bool = False

class NodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    node_id: str
    hostname: str
    address: str
    port: int
    status: NodeStatus
    last_seen: datetime
    cpu_total: int
    memory_total: int
    cpu_used_percent: float
    memory_used_mb: int
    is_mock: bool
    vm_count: Optional[int] = 0

class VMCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64, json_schema_extra={"example": "ubuntu-demo"})
    cpu: int = Field(default=2, ge=1, le=16)
    memory_mb: int = Field(default=2048, ge=512, le=32768)
    disk_gb: int = Field(default=10, ge=2, le=500)
    image: str = Field(default="ubuntu-24.04")
    preferred_node: Optional[str] = None

class VMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    uuid: Optional[str]
    node_id: str
    desired_state: VMStatus
    actual_state: VMStatus
    cpu: int
    memory_mb: int
    disk_gb: int
    image: str
    ip_address: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

class VMEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime
    event_type: EventType
    vm_id: Optional[int]
    vm_name: Optional[str]
    node_id: Optional[str]
    message: str
    level: str

class SystemStatsResponse(BaseModel):
    total_nodes: int
    online_nodes: int
    total_vms: int
    running_vms: int
    total_cpu_cores: int
    allocated_memory_mb: int
