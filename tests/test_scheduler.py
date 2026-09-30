import pytest
from controller.app.models import Node, NodeStatus
from controller.app.schemas import VMCreateRequest
from controller.app.scheduler import ResourceAwareScheduler, SchedulingError

def test_scheduler_selects_least_loaded_node():
    # Node A: 8GB total, 6GB used -> 2GB free
    node_a = Node(
        id=1,
        node_id="node-a",
        hostname="srv-a",
        address="127.0.0.1",
        port=8001,
        status=NodeStatus.ONLINE,
        cpu_total=8,
        memory_total=8192,
        cpu_used_percent=50.0,
        memory_used_mb=6000,
        vms=[]
    )

    # Node B: 8GB total, 1GB used -> 7GB free
    node_b = Node(
        id=2,
        node_id="node-b",
        hostname="srv-b",
        address="127.0.0.1",
        port=8002,
        status=NodeStatus.ONLINE,
        cpu_total=8,
        memory_total=8192,
        cpu_used_percent=10.0,
        memory_used_mb=1024,
        vms=[]
    )

    vm_req = VMCreateRequest(name="test-vm", cpu=2, memory_mb=2048)
    selected = ResourceAwareScheduler.select_node(vm_req, [node_a, node_b])
    
    # Node B has significantly more free memory and lower CPU usage
    assert selected.node_id == "node-b"

def test_scheduler_skips_offline_node():
    node_a = Node(
        id=1,
        node_id="node-a",
        hostname="srv-a",
        address="127.0.0.1",
        port=8001,
        status=NodeStatus.OFFLINE,
        cpu_total=8,
        memory_total=8192,
        cpu_used_percent=0.0,
        memory_used_mb=0,
        vms=[]
    )
    node_b = Node(
        id=2,
        node_id="node-b",
        hostname="srv-b",
        address="127.0.0.1",
        port=8002,
        status=NodeStatus.ONLINE,
        cpu_total=8,
        memory_total=8192,
        cpu_used_percent=20.0,
        memory_used_mb=2048,
        vms=[]
    )

    vm_req = VMCreateRequest(name="test-vm", cpu=1, memory_mb=1024)
    selected = ResourceAwareScheduler.select_node(vm_req, [node_a, node_b])
    assert selected.node_id == "node-b"

def test_scheduler_insufficient_resources_raises_error():
    node_a = Node(
        id=1,
        node_id="node-a",
        hostname="srv-a",
        address="127.0.0.1",
        port=8001,
        status=NodeStatus.ONLINE,
        cpu_total=4,
        memory_total=2048,
        cpu_used_percent=90.0,
        memory_used_mb=1900,
        vms=[]
    )
    # Requesting 4GB RAM when only ~148MB is free
    vm_req = VMCreateRequest(name="huge-vm", cpu=2, memory_mb=4096)
    with pytest.raises(SchedulingError):
        ResourceAwareScheduler.select_node(vm_req, [node_a])
