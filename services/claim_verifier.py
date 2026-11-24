import re
from dataclasses import dataclass

_WORD = re.compile(r"\w+", re.UNICODE)


@dataclass(frozen=True)
class Claim:
    text: str
    evidence_type: str   # "voice" or "photo"
    evidence_ref: str    # transcript span id or photo id


def _terms(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text) if len(w) > 3}


def verify_claims(claims: list[Claim], spans: dict[str, str],
                  photo_ids: set[str]) -> tuple[list[Claim], list[Claim]]:
    supported, unsupported = [], []
    for c in claims:
        if c.evidence_type == "photo":
            ok = c.evidence_ref in photo_ids
        elif c.evidence_type == "voice":
            span = spans.get(c.evidence_ref)
            ok = span is not None and bool(_terms(c.text) & _terms(span))
        else:
            ok = False
        (supported if ok else unsupported).append(c)
    return supported, unsupported
