import pytest
from orchestrator.approval import Approval, ApprovalGate, payload_hash
from orchestrator.audit import AuditLog


def test_tampering_is_detected():
    log = AuditLog()
    log.append({"type": "a"})
    log.append({"type": "b"})
    assert log.verify()
    log._entries[0]["event"]["type"] = "x"
    assert not log.verify()


def test_publish_blocked_without_matching_approval():
    gate = ApprovalGate(AuditLog())
    listing = {"price": 790}
    with pytest.raises(PermissionError):
        gate.require("t1", "publish", payload_hash(listing))
    gate.record(Approval("t1", "publish", payload_hash(listing), "whatsapp", "clip-1"))
    gate.require("t1", "publish", payload_hash(listing))
    with pytest.raises(PermissionError):
        gate.require("t1", "publish", payload_hash({"price": 700}))
