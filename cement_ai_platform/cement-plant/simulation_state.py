from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SimulationEvent(BaseModel):
    timestamp: str
    prediction: float
    alert: Optional[str] = None
    llm_response: Optional[Dict[str, Any]] = None

class SimulationStatus(BaseModel):
    is_running: bool = False
    events: List[SimulationEvent] = []
    error: Optional[str] = None

# Global state
simulation_status = SimulationStatus()

def reset_simulation_status():
    global simulation_status
    simulation_status = SimulationStatus()
