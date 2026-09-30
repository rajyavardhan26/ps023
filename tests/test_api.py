import pytest
from fastapi.testclient import TestClient
from controller.app.main import app
from controller.app.database import engine, Base
from controller.app.config import settings

# Ensure test DB tables are initialized
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"

def test_get_metrics():
    res = client.get("/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "total_nodes" in data
    assert "total_vms" in data

def test_node_registration_and_heartbeat():
    headers = {"X-Node-Token": settings.NODE_AUTH_TOKEN}
    
    # 1. Register Node
    payload = {
        "node_id": "test-node-1",
        "hostname": "test-host",
        "address": "127.0.0.1",
        "port": 8999,
        "cpu_total": 8,
        "memory_total": 16384,
        "is_mock": True
    }
    res = client.post("/nodes/register", json=payload, headers=headers)
    assert res.status_code in [200, 201]
    node = res.json()
    assert node["node_id"] == "test-node-1"
    assert node["status"] == "ONLINE"

    # 2. Heartbeat
    hb_payload = {
        "node_id": "test-node-1",
        "cpu_used_percent": 15.5,
        "memory_used_mb": 2048,
        "vm_count": 0,
        "is_mock": True
    }
    hb_res = client.post("/nodes/heartbeat", json=hb_payload, headers=headers)
    assert hb_res.status_code == 200
    assert hb_res.json()["status"] == "acknowledged"

    # 3. Verify in nodes list
    list_res = client.get("/nodes")
    assert list_res.status_code == 200
    nodes = list_res.json()
    assert any(n["node_id"] == "test-node-1" for n in nodes)

def test_events_endpoint():
    res = client.get("/events")
    assert res.status_code == 200
    events = res.json()
    assert isinstance(events, list)
