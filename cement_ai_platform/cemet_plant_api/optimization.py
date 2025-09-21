from fastapi import APIRouter, HTTPException
from typing import Dict, List
import uuid
from datetime import datetime
import asyncio

from models import OptimizationRequest, OptimizationResult, PlantData, MachineControl, OptimizationPriority
from gemini_service import GeminiOptimizationService

router = APIRouter(prefix="/optimization", tags=["Plant Optimization"])

# Global service instance
gemini_service = GeminiOptimizationService()

@router.post("/analyze", response_model=OptimizationResult)
async def analyze_plant_operations(request: OptimizationRequest) -> OptimizationResult:
    """Comprehensive plant optimization analysis"""
    
    analysis_id = str(uuid.uuid4())
    
    try:
        # Convert to dict for processing
        plant_data_dict = request.plant_data.model_dump()
        
        # Get analysis from Gemini
        analysis_result = await gemini_service.analyze_plant_data(
            plant_data=plant_data_dict,
            optimization_focus=request.optimization_focus
        )
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # Detect anomalies if baseline provided
        anomalies = []
        if request.baseline_data:
            baseline_dict = request.baseline_data.model_dump()
            anomalies = await gemini_service.detect_anomalies(plant_data_dict, baseline_dict)
        
        # Convert machine controls to proper format
        machine_controls = []
        if request.include_machine_controls:
            for control in analysis_result.get("machine_controls", []):
                machine_controls.append(MachineControl(
                    machine_id=control["machine_id"],
                    parameter=control["parameter"],
                    current_value=control["current_value"],
                    target_value=control["target_value"],
                    action=control["action"],
                    priority=OptimizationPriority(control["priority"]),
                    estimated_savings=control.get("estimated_savings")
                ))
        
        return OptimizationResult(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            plant_data=request.plant_data,
            energy_efficiency_kwh_per_ton=analysis_result["energy_efficiency_kwh_per_ton"],
            status=OptimizationPriority(analysis_result["status"]),
            anomalies=anomalies,
            recommendations=analysis_result.get("recommendations", []),
            machine_controls=machine_controls,
            predicted_savings=analysis_result.get("predicted_savings"),
            maintenance_alerts=analysis_result.get("maintenance_alerts", [])
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/quick-analysis", response_model=Dict)
async def quick_energy_analysis(plant_data: PlantData) -> Dict:
    """Quick energy efficiency analysis"""
    
    try:
        energy_per_ton = plant_data.power_consumption_kw / max(plant_data.cement_production_tph, 1)
        
        if energy_per_ton > 25:
            status = "🔴 CRITICAL"
            message = "Extremely high energy consumption - immediate action required"
        elif energy_per_ton > 20:
            status = "🟡 WARNING" 
            message = "Energy consumption above optimal - optimization needed"
        elif energy_per_ton < 18:
            status = "🟢 OPTIMAL"
            message = "Excellent energy efficiency"
        else:
            status = "🟢 NORMAL"
            message = "Energy efficiency within acceptable range"
        
        # Quick recommendations
        quick_actions = []
        if plant_data.mill_speed_rpm > 18.5:
            quick_actions.append("Reduce mill speed by 0.5 RPM")
        if plant_data.limestone_pct > 82:
            quick_actions.append("Reduce limestone content to 80%")
        if plant_data.mill_temperature_c > 95:
            quick_actions.append("Increase mill ventilation")
        
        return {
            "energy_efficiency_kwh_per_ton": energy_per_ton,
            "status": status,
            "message": message,
            "quick_actions": quick_actions,
            "target_energy": 18.0,
            "potential_savings_pct": max(0, (energy_per_ton - 18.0) / energy_per_ton * 100)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick analysis failed: {str(e)}")

@router.get("/energy-benchmark")
async def get_energy_benchmark() -> Dict:
    """Get energy efficiency benchmarks"""
    
    return {
        "benchmarks": {
            "world_class": {"value": 15.0, "description": "Top 5% global performance"},
            "excellent": {"value": 18.0, "description": "Industry best practice"},
            "good": {"value": 22.0, "description": "Above average performance"},
            "average": {"value": 25.0, "description": "Industry average"},
            "poor": {"value": 30.0, "description": "Below average - needs improvement"}
        },
        "optimization_targets": {
            "immediate": "Reduce energy consumption to <20 kWh/ton",
            "short_term": "Achieve <18 kWh/ton through process optimization",
            "long_term": "Target <16 kWh/ton with advanced control systems"
        },
        "typical_savings": {
            "mill_speed_optimization": "3-5%",
            "raw_material_optimization": "2-4%",
            "grinding_aid_usage": "4-8%",
            "separator_efficiency": "2-3%",
            "advanced_control": "5-10%"
        }
    }