from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from orchestrator.approval import Approval, ApprovalGate, payload_hash
from orchestrator.audit import AuditLog
from orchestrator.workflow import State, Task, needs_human
from services.claim_verifier import Claim, verify_claims
from services.pricing import PriceInput, fair_price
from services.wage_table import WageTable

app = FastAPI(title="MakerFirst prototype")
audit = AuditLog()
gate = ApprovalGate(audit)
wages = WageTable.from_csv("data/wage_table.csv")
tasks: dict[str, Task] = {}
published: dict[str, dict] = {}


class ClaimIn(BaseModel):
    text: str
    evidence_type: str
    evidence_ref: str


class DraftIn(BaseModel):
    task_id: str
    title: str
    state: str
    category: str
    zone: str
    materials_cost: float
    active_hours: float
    overheads: float
    comps: list[float]
    asr_confidence: float
    spans: dict[str, str]
    photo_ids: list[str]
    claims: list[ClaimIn]


class ApproveIn(BaseModel):
    task_id: str
    action: str = "publish"
    payload_hash: str
    channel: str
    evidence_ref: str


def _advance(task: Task, to: State) -> None:
    try:
        task.advance(to)
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.post("/draft")
def draft(body: DraftIn):
    task = tasks.setdefault(body.task_id, Task(body.task_id))
    _advance(task, State.DRAFT)

    supported, unsupported = verify_claims(
        [Claim(**c.model_dump()) for c in body.claims],
        body.spans, set(body.photo_ids))
    _advance(task, State.VERIFY)

    try:
        row = wages.lookup(body.state, body.category, body.zone, date.today())
    except LookupError as e:
        raise HTTPException(422, str(e))
    price = fair_price(PriceInput(body.materials_cost, body.active_hours,
                                  row.rate_per_hour, body.overheads,
                                  tuple(body.comps)))
    _advance(task, State.PRICE)

    reason = needs_human(body.asr_confidence, price)
    if reason:
        _advance(task, State.HANDOFF)
        audit.append({"type": "handoff", "task_id": body.task_id, "reason": reason})
        return {"status": "handoff", "reason": reason, "price": price}

    listing = {"title": body.title,
               "claims": [c.text for c in supported],
               "price": price,
               "wage_source": row.source_url,
               "wage_effective_from": row.effective_from.isoformat()}
    task.data["listing"] = listing
    _advance(task, State.APPROVE)
    return {"status": "awaiting_approval", "listing": listing,
            "payload_hash": payload_hash(listing),
            "unsupported_claims": [c.text for c in unsupported]}


@app.post("/approve")
def approve(body: ApproveIn):
    if body.task_id not in tasks:
        raise HTTPException(404, "unknown task")
    gate.record(Approval(**body.model_dump()))
    return {"recorded": True}


@app.post("/publish/{task_id}")
def publish(task_id: str):
    task = tasks.get(task_id)
    if task is None or task.state != State.APPROVE:
        raise HTTPException(409, "task is not awaiting approval")
    listing = task.data["listing"]
    try:
        gate.require(task_id, "publish", payload_hash(listing))
    except PermissionError as e:
        raise HTTPException(403, str(e))
    _advance(task, State.PUBLISHED)
    published[task_id] = listing
    audit.append({"type": "publish", "task_id": task_id})
    return {"status": "published", "listing": listing}


@app.get("/audit/verify")
def audit_verify():
    return {"ok": audit.verify(), "entries": len(audit.entries)}
