from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class Sample(BaseModel):
    ts: datetime
    SiO2_in: float
    CaO_in: float
    Moisture: float
    Separator: float
    Gypsum: float
    LSF_est: float
    Blaine_est: float
    fCaO_est: float
    energy_consumption: float

class Knobs(BaseModel):
    limestone_pct: float
    sand_pct: float
    clay_pct: float
    separator_speed: float
    gypsum_pct: float

class Issue(BaseModel):
    ts: datetime
    text: str
    drivers: List[str] = []

class PlanAction(BaseModel):
    knob: str
    delta_pct: float = 0.0
    reason: str

class Plan(BaseModel):
    issue: str
    kpi_impact: Dict[str, str]
    actions: List[PlanAction]
    notes: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class PlanResult(BaseModel):
    plan: Plan
    adjusted_actions: List[PlanAction]
    safety_notes: Optional[str] = None
    simulated_after: Optional[Dict[str, float]] = None

class DisturbanceRequest(BaseModel):
    type: str = Field(..., examples=["siO2_spike","cao_drop","sep_low"])
    magnitude: float = 1.0
    duration_s: int = 30

class ConfigGet(BaseModel):
    targets: Dict[str, float]
    limits: Dict[str, float]
    knobs: Knobs

class ConfigPatch(BaseModel):
    targets: Optional[Dict[str, float]] = None
    limits: Optional[Dict[str, float]] = None
    knobs: Optional[Knobs] = None

class AuditEntry(BaseModel):
    ts: datetime
    kind: str
    detail: Dict[str, Any]
