import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from controller.app.database import Base

class NodeStatus(str, enum.Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"

class VMStatus(str, enum.Enum):
    CREATING = "CREATING"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"
    DELETING = "DELETING"
    UNKNOWN = "UNKNOWN"

class EventType(str, enum.Enum):
    VM_CREATED = "VM_CREATED"
    VM_STARTED = "VM_STARTED"
    VM_STOPPED = "VM_STOPPED"
    VM_RESTARTED = "VM_RESTARTED"
    VM_DELETED = "VM_DELETED"
    VM_FAILED = "VM_FAILED"
    NODE_ONLINE = "NODE_ONLINE"
    NODE_OFFLINE = "NODE_OFFLINE"
    NODE_HEARTBEAT = "NODE_HEARTBEAT"
    RECONCILIATION = "RECONCILIATION"

class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(64), unique=True, index=True, nullable=False)
    hostname = Column(String(128), nullable=False)
    address = Column(String(64), nullable=False)
    port = Column(Integer, nullable=False)
    status = Column(Enum(NodeStatus), default=NodeStatus.ONLINE, nullable=False)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    cpu_total = Column(Integer, default=4)
    memory_total = Column(Integer, default=8192)  # In MB
    cpu_used_percent = Column(Float, default=0.0)
    memory_used_mb = Column(Integer, default=0)
    
    is_mock = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    vms = relationship("VM", back_populates="node", cascade="all, delete-orphan")

class VM(Base):
    __tablename__ = "vms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), unique=True, index=True, nullable=False)
    uuid = Column(String(64), unique=True, index=True, nullable=True)
    node_id = Column(String(64), ForeignKey("nodes.node_id"), nullable=False)
    
    # State tracking: Desired state vs Actual hypervisor state
    desired_state = Column(Enum(VMStatus), default=VMStatus.RUNNING, nullable=False)
    actual_state = Column(Enum(VMStatus), default=VMStatus.CREATING, nullable=False)
    
    cpu = Column(Integer, nullable=False, default=1)
    memory_mb = Column(Integer, nullable=False, default=1024)
    disk_gb = Column(Integer, nullable=False, default=10)
    image = Column(String(64), nullable=False, default="ubuntu-24.04")
    
    ip_address = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    node = relationship("Node", back_populates="vms")

class VMEvent(Base):
    __tablename__ = "vm_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    event_type = Column(Enum(EventType), nullable=False)
    vm_id = Column(Integer, nullable=True)
    vm_name = Column(String(64), nullable=True)
    node_id = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    level = Column(String(16), default="INFO")
