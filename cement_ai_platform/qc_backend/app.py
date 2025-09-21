import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel
from qc.config import settings
from qc.storage import init_engine, recent_samples, log_audit, get_audits, SampleORM
from qc.simulator import PlantSim, run_sim
from qc.detector import DriftDetector
from qc.schemas import Sample, Plan, PlanResult, DisturbanceRequest, Knobs, ConfigGet, ConfigPatch, PlanAction
from qc.planner_gemini import propose_plan
from qc.safety import clamp_actions
from qc.actions import simulate_after

app = FastAPI(title="QC Mini-Copilot Backend")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

engine = init_engine(settings.DB_PATH)
plant = PlantSim()
detector = DriftDetector(win=int(settings.WINDOW_SECONDS))

@app.on_event("startup")
async def startup():
    asyncio.create_task(run_sim(engine, plant))

@app.get("/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

@app.get("/state/current", response_model=Sample)
def state_current():
    rows = recent_samples(engine, seconds=10)
    if not rows: raise HTTPException(503, "no data yet")
    r = rows[-1]
    detector.push(r.__dict__)
    return Sample(**r.__dict__)

@app.get("/state/series")
def state_series(last_seconds: int = 600):
    rows = recent_samples(engine, seconds=last_seconds)
    return [r.__dict__ for r in rows]

@app.get("/config", response_model=ConfigGet)
def get_config():
    return {
        "targets": {"LSF_MIN": settings.LSF_MIN, "LSF_MAX": settings.LSF_MAX,
                    "BLAINE_MIN": settings.BLAINE_MIN, "BLAINE_MAX": settings.BLAINE_MAX,
                    "FCAO_MAX": settings.FCAO_MAX},
        "limits": {"RAMP_LIMIT_PCT": settings.RAMP_LIMIT_PCT,
                   "SEP_RAMP_LIMIT": settings.SEP_RAMP_LIMIT,
                   "GYPSUM_RAMP_LIMIT": settings.GYPSUM_RAMP_LIMIT},
        "knobs": Knobs(limestone_pct=plant.limestone_pct, sand_pct=plant.sand_pct, clay_pct=plant.clay_pct,
                       separator_speed=plant.separator_speed, gypsum_pct=plant.gypsum_pct)
    }

@app.post("/disturb")
def disturb(d: DisturbanceRequest):
    plant.inject_disturbance(d.type, d.magnitude, d.duration_s)
    log_audit(engine, "disturbance", d.dict())
    return {"ok": True}

@app.post("/plan/propose", response_model=Plan)
def propose(force: bool = Query(default=False)):
    rows = recent_samples(engine, seconds=120)
    if len(rows) < 5:
        raise HTTPException(503, "not enough data yet")

    # keep detector warm with recent rows
    for r in rows:
        detector.push(r.__dict__)

    issue = detector.maybe_issue()
    if not issue and not force:
        raise HTTPException(400, "no issue detected; try /disturb or use /plan/propose?force=1")

    if not issue:
        # fallback: build a generic issue based on current reading vs targets
        r = rows[-1]
        text = "Proactive correction request (force): nudge rawmix/mill to center targets"
        kpi_hint = {"LSF":"neutral","Blaine":"neutral","fCaO":"neutral"}
        issue = {"text": text, "kpi_impact": kpi_hint, "drivers":["force"]}

    window_stats = {
        "SiO2": {"last": rows[-1].SiO2_in},
        "CaO":  {"last": rows[-1].CaO_in},
        "Sep":  {"last": rows[-1].Separator},
        "Moist":{"last": rows[-1].Moisture},
        "Gypsum":{"last": rows[-1].Gypsum},
        "LSF":  {"last": rows[-1].LSF_est},
        "Blaine":{"last": rows[-1].Blaine_est},
        "fCaO": {"last": rows[-1].fCaO_est},
        "kpi_impact_hint": issue["kpi_impact"]
    }
    knobs = {"limestone_pct": plant.limestone_pct, "sand_pct": plant.sand_pct,
             "clay_pct": plant.clay_pct, "separator_speed": plant.separator_speed,
             "gypsum_pct": plant.gypsum_pct}
    plan = propose_plan(window_stats, issue["text"], knobs)
    log_audit(engine, "plan_proposed", {"issue": issue, "plan": plan.dict(), "force": bool(not detector.maybe_issue())})
    return plan

@app.post("/plan/simulate", response_model=PlanResult)
def simulate(plan: Plan):
    actions, clamp_note = clamp_actions(plan.actions)
    rows = recent_samples(engine, seconds=10)
    if not rows: raise HTTPException(503, "no data yet")
    sample_now = rows[-1].__dict__
    after = simulate_after(sample_now, actions)
    log_audit(engine, "plan_simulated", {"plan": plan.dict(), "after": after, "clamp": clamp_note})
    return {"plan": plan, "adjusted_actions": actions, "safety_notes": clamp_note, "simulated_after": after}

@app.post("/plan/apply", response_model=PlanResult)
def apply(plan: Plan):
    # Capture "before" state
    rows_before = recent_samples(engine, seconds=10)
    if not rows_before:
        raise HTTPException(503, "no data yet to capture 'before' state")
    before_state = rows_before[-1].__dict__

    actions, clamp_note = clamp_actions(plan.actions)
    plant.apply_actions(actions)

    # Capture "after" state (after a short delay to allow simulator to tick)
    import time
    time.sleep(settings.TICK_SECONDS * 2) # Wait for a couple of ticks
    rows_after = recent_samples(engine, seconds=10)
    if not rows_after:
        raise HTTPException(503, "no data yet to capture 'after' state")
    after_state = rows_after[-1].__dict__

    # Filter for float/int values for the response model to avoid validation errors
    simulated_after_response = {k: v for k, v in after_state.items() if isinstance(v, (int, float))}

    # Filter for float/int values for the response model to avoid validation errors
    simulated_after_response = {k: v for k, v in after_state.items() if isinstance(v, (int, float))}

    # Filter for float/int values for the response model to avoid validation errors
    simulated_after_response = {k: v for k, v in after_state.items() if isinstance(v, (int, float))}

    log_audit(engine, "plan_applied", {
        "plan": plan.dict(),
        "applied_actions": [a.dict() for a in actions],
        "clamp": clamp_note,
        "state_before": {k: v for k, v in before_state.items() if k in ['LSF_est', 'Blaine_est', 'fCaO_est'] and isinstance(v, (int, float))},
        "state_after": {k: v for k, v in after_state.items() if k in ['LSF_est', 'Blaine_est', 'fCaO_est'] and isinstance(v, (int, float))}
    })
    return {"plan": plan, "adjusted_actions": actions, "safety_notes": clamp_note, "simulated_after": simulated_after_response}

@app.get("/audit")
def audit(limit: int = 50):
    rows = get_audits(engine, limit=limit)
    return [{"ts": r.ts, "kind": r.kind, "detail": r.detail_json} for r in rows]
