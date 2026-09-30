import pytest
from controller.app.models import VMStatus

def test_valid_vm_statuses():
    statuses = [s.value for s in VMStatus]
    assert "CREATING" in statuses
    assert "RUNNING" in statuses
    assert "STOPPED" in statuses
    assert "ERROR" in statuses
    assert "DELETING" in statuses
    assert "UNKNOWN" in statuses

def test_status_equality():
    status = VMStatus("RUNNING")
    assert status == VMStatus.RUNNING
    assert status != VMStatus.STOPPED
