from typing import Callable
from pydantic import BaseModel, Field, ValidationError


class Extracted(BaseModel):
    materials_cost: float | None = Field(default=None, ge=0)
    active_hours: float | None = Field(default=None, gt=0)
    overheads: float | None = Field(default=None, ge=0)
    technique: str = ""
    story: str = ""


REQUIRED = ("materials_cost", "active_hours", "overheads")

PROMPT = (
    "Extract fields from this artisan's transcript. Return ONLY JSON with keys: "
    "materials_cost (rupees), active_hours (hands-on hours only, not drying or "
    "waiting), overheads (rupees), technique, story. Use null for anything not "
    "stated. Never guess.\nTranscript:\n{t}"
)


def _strip_fences(raw: str) -> str:
    return raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def extract_fields(transcript: str, llm_call: Callable[[str], str]) -> tuple[Extracted, list[str]]:
    raw = _strip_fences(llm_call(PROMPT.format(t=transcript)))
    try:
        data = Extracted.model_validate_json(raw)
    except ValidationError:
        return Extracted(), list(REQUIRED)
    missing = [f for f in REQUIRED if getattr(data, f) is None]
    return data, missing
