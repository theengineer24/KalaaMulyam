import hashlib
import json
import time

GENESIS = "0" * 64


def _digest(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


class AuditLog:
    def __init__(self):
        self._entries: list[dict] = []

    def append(self, event: dict) -> dict:
        prev = self._entries[-1]["hash"] if self._entries else GENESIS
        body = {"ts": time.time(), "event": event, "prev": prev}
        entry = {**body, "hash": _digest(body)}
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        prev = GENESIS
        for e in self._entries:
            body = {"ts": e["ts"], "event": e["event"], "prev": e["prev"]}
            if e["prev"] != prev or _digest(body) != e["hash"]:
                return False
            prev = e["hash"]
        return True

    @property
    def entries(self) -> list[dict]:
        return list(self._entries)
