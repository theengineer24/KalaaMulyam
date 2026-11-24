from dataclasses import dataclass
from statistics import quantiles


@dataclass(frozen=True)
class PriceInput:
    materials: float          # rupees, wastage included
    active_hours: float       # hands-on hours only
    wage_per_hour: float      # from the wage table
    overheads: float          # tools, fuel, packing
    comps: tuple[float, ...]  # comparable selling prices, rupees


def fair_price(p: PriceInput) -> dict:
    if p.active_hours <= 0:
        raise ValueError("active_hours must be positive")
    floor = p.materials + p.active_hours * p.wage_per_hour + p.overheads
    n = len(p.comps)
    if n < 3:
        return {"outcome": "thin_data", "floor": round(floor),
                "suggested": round(floor * 1.15), "confidence": "low"}
    q1, q2, q3 = quantiles(p.comps, n=4, method="inclusive")
    if q3 < floor:
        effective = (q2 - p.materials - p.overheads) / p.active_hours
        return {"outcome": "below_floor", "floor": round(floor),
                "market": (round(q1), round(q3)),
                "effective_wage_at_market": round(effective)}
    suggested = min(max(q2, floor), q3)
    return {"outcome": "above_floor" if q1 >= floor else "overlap",
            "floor": round(floor), "market": (round(q1), round(q3)),
            "suggested": round(suggested),
            "confidence": "high" if n >= 15 else "medium" if n >= 5 else "low"}
