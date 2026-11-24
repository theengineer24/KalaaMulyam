from __future__ import annotations
import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class WageRow:
    state: str
    category: str
    zone: str
    rate_per_hour: float
    effective_from: date
    source_url: str


class WageTable:
    def __init__(self, rows: list[WageRow]):
        self._rows = rows

    @classmethod
    def from_csv(cls, path: str | Path) -> "WageTable":
        with open(path, newline="", encoding="utf-8") as f:
            rows = [
                WageRow(
                    state=r["state"].strip().lower(),
                    category=r["category"].strip().lower(),
                    zone=r["zone"].strip().lower(),
                    rate_per_hour=float(r["rate_per_hour"]),
                    effective_from=date.fromisoformat(r["effective_from"]),
                    source_url=r["source_url"].strip(),
                )
                for r in csv.DictReader(f)
            ]
        return cls(rows)

    def lookup(self, state: str, category: str, zone: str, on: date) -> WageRow:
        s, c, z = state.strip().lower(), category.strip().lower(), zone.strip().lower()
        candidates = [r for r in self._rows
                      if r.state == s and r.category == c and r.zone == z
                      and r.effective_from <= on]
        if not candidates:
            raise LookupError(f"no wage row for {s}/{c}/{z} on {on}")
        return max(candidates, key=lambda r: r.effective_from)
