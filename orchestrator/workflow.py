from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    INTAKE = "intake"
    DRAFT = "draft"
    VERIFY = "verify"
    PRICE = "price"
    APPROVE = "approve"
    PUBLISHED = "published"
    HANDOFF = "handoff"
    REJECTED = "rejected"


TRANSITIONS = {
    State.INTAKE: {State.DRAFT, State.HANDOFF},
    State.DRAFT: {State.VERIFY, State.HANDOFF},
    State.VERIFY: {State.PRICE, State.DRAFT, State.HANDOFF},
    State.PRICE: {State.APPROVE, State.HANDOFF},
    State.APPROVE: {State.PUBLISHED, State.DRAFT, State.REJECTED, State.HANDOFF},
}


@dataclass
class Task:
    task_id: str
    state: State = State.INTAKE
    data: dict = field(default_factory=dict)

    def advance(self, to: State) -> None:
        if to not in TRANSITIONS.get(self.state, set()):
            raise ValueError(f"invalid transition {self.state.value} -> {to.value}")
        self.state = to


ASR_MIN_CONFIDENCE = 0.6   # placeholder, tune on real recordings
BULK_QTY = 20              # placeholder


def needs_human(asr_confidence: float, price: dict, order_qty: int | None = None) -> str | None:
    if asr_confidence < ASR_MIN_CONFIDENCE:
        return "low_speech_confidence"
    if price.get("outcome") == "below_floor":
        return "below_floor"
    if order_qty is not None and order_qty >= BULK_QTY:
        return "bulk_order"
    return None
