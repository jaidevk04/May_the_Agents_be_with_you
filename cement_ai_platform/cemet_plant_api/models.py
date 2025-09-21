from pydantic import BaseModel, Field, computed_field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class OptimizationPriority(str, Enum):
    CRITICAL = "🔴 CRITICAL"
    WARNING = "🟡 WARNING" 
    NORMAL = "🟢 NORMAL"
    OPTIMAL = "🟢 OPTIMAL"

class PlantData(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    limestone_pct: float = Field(ge=0, le=100)
    clay_pct: float = Field(ge=0, le=100)
    iron_ore_pct: float = Field(ge=0, le=100)
    gypsum_pct: float = Field(ge=0, le=100)
    mill_speed_rpm: float = Field(ge=0)
    power_consumption_kw: float = Field(ge=0)
    cement_production_tph: float = Field(ge=0)
    blaine_fineness: float = Field(ge=0)
    mill_temperature_c: float
    vibration_level: Optional[float] = None
    separator_speed_rpm: Optional[float] = None

    @computed_field
    def energy_consumption_kwh_per_ton(self) -> float:
        # Prevent division by zero
        if self.cement_production_tph == 0:
            return 0.0
        return self.power_consumption_kw / self.cement_production_tph

class MachineControl(BaseModel):
    machine_id: str
    parameter: str
    current_value: float
    target_value: float
    action: str
    priority: OptimizationPriority
    estimated_savings: Optional[str] = None

class OptimizationResult(BaseModel):
    analysis_id: str
    timestamp: datetime
    plant_data: PlantData
    energy_efficiency_kwh_per_ton: float
    status: OptimizationPriority
    anomalies: List[str] = []
    recommendations: List[str] = []
    machine_controls: List[MachineControl] = []
    predicted_savings: Optional[Dict[str, float]] = None
    maintenance_alerts: List[str] = []

class OptimizationRequest(BaseModel):
    plant_data: PlantData
    baseline_data: Optional[PlantData] = None
    optimization_focus: List[str] = ["energy", "production", "quality"]
    include_machine_controls: bool = True

class DataGenerationRequest(BaseModel):
    duration_minutes: int = Field(ge=1, le=1440)
    interval_seconds: int = Field(ge=5, le=300)
    scenario: str = Field(default="normal")
    inject_anomalies: bool = Field(default=True)

class ControlAction(BaseModel):
    action_id: str
    machine_id: str
    parameter: str
    action_type: str
    target_value: Optional[float] = None
    safety_confirmed: bool = False