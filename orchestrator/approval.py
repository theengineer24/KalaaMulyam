import hashlib
import json
from dataclasses import dataclass, asdict

from orchestrator.audit import AuditLog


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Approval:
    task_id: str
    action: str         # "publish", "send_quote", "accept_order"
    payload_hash: str   # hash of the exact content that was read back
    channel: str        # "whatsapp", "ivr", "helper"
    evidence_ref: str   # audio clip id or keypress id


class ApprovalGate:
    def __init__(self, audit: AuditLog):
        self._approvals: dict[tuple[str, str], Approval] = {}
        self._audit = audit

    def record(self, approval: Approval) -> None:
        self._approvals[(approval.task_id, approval.action)] = approval
        self._audit.append({"type": "approval", **asdict(approval)})

    def require(self, task_id: str, action: str, content_hash: str) -> Approval:
        a = self._approvals.get((task_id, action))
        if a is None or a.payload_hash != content_hash:
            self._audit.append({"type": "blocked", "task_id": task_id, "action": action})
            raise PermissionError(f"no matching approval for {action} on {task_id}")
        return a
