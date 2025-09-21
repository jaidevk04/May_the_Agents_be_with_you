from typing import List, Tuple
from .schemas import PlanAction
from .config import settings

RAW_KNOBS = {"limestone_pct","sand_pct","clay_pct"}

def clamp_actions(actions: List[PlanAction]) -> Tuple[List[PlanAction], str]:
    notes = []
    out = []
    # enforce ramp limits
    for a in actions:
        if a.knob in RAW_KNOBS:
            lim = settings.RAMP_LIMIT_PCT
            if a.delta_pct > lim: a.delta_pct = lim; notes.append(f"{a.knob} clamped to +{lim}%")
            if a.delta_pct < -lim: a.delta_pct = -lim; notes.append(f"{a.knob} clamped to -{lim}%")
        elif a.knob == "separator_speed":
            lim = settings.SEP_RAMP_LIMIT
            if a.delta_pct > lim: a.delta_pct = lim; notes.append("separator clamped")
            if a.delta_pct < -lim: a.delta_pct = -lim; notes.append("separator clamped")
        elif a.knob == "gypsum_pct":
            lim = settings.GYPSUM_RAMP_LIMIT
            if a.delta_pct > lim: a.delta_pct = lim; notes.append("gypsum clamped")
            if a.delta_pct < -lim: a.delta_pct = -lim; notes.append("gypsum clamped")
        out.append(a)

    # keep limestone+sand+clay ≈ 100 by correcting clay
    total_delta = sum(a.delta_pct for a in out if a.knob in RAW_KNOBS)
    # If sum drifts, compensate on clay if not already present
    has_clay = any(a.knob=="clay_pct" for a in out)
    if abs(total_delta) > 1e-6 and not has_clay:
        out.append(PlanAction(
        knob="clay_pct",
        delta_pct=-total_delta,
        reason="Auto-balance to keep limestone+sand+clay ≈ 100%"
    ))
    return out, "; ".join(notes) if notes else ""
