from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List
import uuid
from datetime import datetime
import asyncio

from models import ControlAction, PlantData

router = APIRouter(prefix="/controls", tags=["Machine Control"])

# Simulated machine states
machine_states = {
    "MILL_01": {"speed_rpm": 17.5, "status": "running", "last_update": datetime.now()},
    "RAW_FEEDER_01": {"feed_rate_tph": 50, "limestone_pct": 80, "status": "running"},
    "SEPARATOR_01": {"speed_rpm": 150, "efficiency_pct": 85, "status": "running"},
    "VENTILATION_01": {"air_flow_m3_min": 200, "temperature_c": 90, "status": "running"},
    "DOSING_01": {"grinding_aid_pct": 0.05, "flow_rate_kg_h": 25, "status": "running"}
}

# Active control actions
active_actions: Dict[str, ControlAction] = {}

@router.get("/machines/status")
async def get_machine_status() -> Dict:
    """Get current status of all machines"""
    return {
        "machines": machine_states,
        "total_machines": len(machine_states),
        "active_actions": len(active_actions),
        "timestamp": datetime.now()
    }

@router.post("/execute")
async def execute_control_action(action: ControlAction, background_tasks: BackgroundTasks) -> Dict:
    """Execute a machine control action"""
    
    if not action.safety_confirmed:
        raise HTTPException(status_code=400, detail="Safety confirmation required")
    
    if action.machine_id not in machine_states:
        raise HTTPException(status_code=404, detail=f"Machine {action.machine_id} not found")
    
    # Generate action ID
    action.action_id = str(uuid.uuid4())
    
    # Add to active actions
    active_actions[action.action_id] = action
    
    # Execute action in background
    background_tasks.add_task(simulate_control_execution, action)
    
    return {
        "action_id": action.action_id,
        "status": "initiated",
        "message": f"Control action initiated for {action.machine_id}",
        "estimated_completion": "2-5 minutes",
        "timestamp": datetime.now()
    }

@router.get("/actions/{action_id}")
async def get_action_status(action_id: str) -> Dict:
    """Get status of specific control action"""
    
    if action_id not in active_actions:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action = active_actions[action_id]
    
    return {
        "action_id": action_id,
        "machine_id": action.machine_id,
        "parameter": action.parameter,
        "target_value": action.target_value,
        "status": "completed",  # Simulated
        "completion_time": datetime.now(),
        "result": "Parameter successfully adjusted"
    }

@router.post("/emergency-stop")
async def emergency_stop(machine_id: str) -> Dict:
    """Emergency stop for specific machine"""
    
    if machine_id not in machine_states:
        raise HTTPException(status_code=404, detail="Machine not found")
    
    # Update machine status
    machine_states[machine_id]["status"] = "emergency_stopped"
    machine_states[machine_id]["last_update"] = datetime.now()
    
    # Cancel active actions for this machine
    actions_cancelled = []
    for action_id, action in list(active_actions.items()):
        if action.machine_id == machine_id:
            actions_cancelled.append(action_id)
            del active_actions[action_id]
    
    return {
        "machine_id": machine_id,
        "status": "emergency_stopped",
        "actions_cancelled": len(actions_cancelled),
        "message": f"Emergency stop executed for {machine_id}",
        "timestamp": datetime.now()
    }

@router.post("/optimize-mill-speed")
async def optimize_mill_speed(plant_data: PlantData) -> Dict:
    """Auto-optimize mill speed based on current conditions"""
    
    current_speed = plant_data.mill_speed_rpm
    energy_per_ton = plant_data.power_consumption_kw / max(plant_data.cement_production_tph, 1)
    
    # Calculate optimal speed
    if energy_per_ton > 22:
        # Reduce speed for energy savings
        target_speed = max(16.5, current_speed - 0.8)
        reason = "High energy consumption - reducing speed"
    elif energy_per_ton < 16 and plant_data.cement_production_tph < 48:
        # Increase speed for production
        target_speed = min(18.5, current_speed + 0.5)
        reason = "Low production - increasing speed"
    elif plant_data.mill_temperature_c > 95:
        # Reduce speed for temperature control
        target_speed = max(16.5, current_speed - 0.3)
        reason = "High temperature - reducing speed"
    else:
        target_speed = current_speed
        reason = "Speed is optimal"
    
    if abs(target_speed - current_speed) > 0.1:
        # Create control action
        action = ControlAction(
            action_id=str(uuid.uuid4()),
            machine_id="MILL_01",
            parameter="speed_rpm",
            action_type="adjust",
            target_value=target_speed,
            safety_confirmed=True
        )
        
        # Execute immediately for auto-optimization
        active_actions[action.action_id] = action
        
        return {
            "optimization_performed": True,
            "current_speed": current_speed,
            "target_speed": target_speed,
            "adjustment": target_speed - current_speed,
            "reason": reason,
            "action_id": action.action_id,
            "estimated_energy_savings": f"{abs(target_speed - current_speed) * 2:.1f}%"
        }
    else:
        return {
            "optimization_performed": False,
            "current_speed": current_speed,
            "reason": reason,
            "message": "No adjustment needed"
        }

@router.post("/batch-optimize")
async def batch_optimize_parameters(plant_data: PlantData, background_tasks: BackgroundTasks) -> Dict:
    """Optimize multiple parameters simultaneously"""
    
    optimizations = []
    energy_per_ton = plant_data.power_consumption_kw / max(plant_data.cement_production_tph, 1)
    
    # Mill speed optimization
    current_speed = plant_data.mill_speed_rpm
    if energy_per_ton > 20:
        target_speed = max(16.5, current_speed - 0.5)
        optimizations.append({
            "machine_id": "MILL_01",
            "parameter": "speed_rpm",
            "current_value": current_speed,
            "target_value": target_speed,
            "priority": "high"
        })
    
    # Raw material optimization
    if plant_data.limestone_pct > 82 or plant_data.limestone_pct < 78:
        target_limestone = 80.0
        optimizations.append({
            "machine_id": "RAW_FEEDER_01",
            "parameter": "limestone_pct",
            "current_value": plant_data.limestone_pct,
            "target_value": target_limestone,
            "priority": "medium"
        })
    
    # Separator optimization
    if plant_data.blaine_fineness > 3600:
        current_sep_speed = plant_data.separator_speed_rpm or 150
        target_sep_speed = current_sep_speed * 1.05
        optimizations.append({
            "machine_id": "SEPARATOR_01", 
            "parameter": "speed_rpm",
            "current_value": current_sep_speed,
            "target_value": target_sep_speed,
            "priority": "medium"
        })
    
    # Temperature control
    if plant_data.mill_temperature_c > 95:
        optimizations.append({
            "machine_id": "VENTILATION_01",
            "parameter": "air_flow_m3_min",
            "current_value": 200,
            "target_value": 220,
            "priority": "high"
        })
    
    # Execute optimizations
    action_ids = []
    for opt in optimizations:
        action = ControlAction(
            action_id=str(uuid.uuid4()),
            machine_id=opt["machine_id"],
            parameter=opt["parameter"],
            action_type="adjust",
            target_value=opt["target_value"],
            safety_confirmed=True
        )
        active_actions[action.action_id] = action
        action_ids.append(action.action_id)
        
        # Simulate execution
        background_tasks.add_task(simulate_control_execution, action)
    
    return {
        "batch_optimization": True,
        "total_optimizations": len(optimizations),
        "action_ids": action_ids,
        "optimizations": optimizations,
        "estimated_completion": "3-8 minutes",
        "expected_energy_savings": f"{len(optimizations) * 1.5:.1f}%"
    }

async def simulate_control_execution(action: ControlAction):
    """Simulate control action execution"""
    await asyncio.sleep(2)  # Simulate execution time
    
    # Update machine state
    if action.machine_id in machine_states:
        if action.parameter in machine_states[action.machine_id]:
            machine_states[action.machine_id][action.parameter] = action.target_value
        machine_states[action.machine_id]["last_update"] = datetime.now()
    
    # Remove from active actions after completion
    await asyncio.sleep(3)
    if action.action_id in active_actions:
        del active_actions[action.action_id]