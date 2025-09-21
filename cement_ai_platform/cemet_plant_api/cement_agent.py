# cement_agent.py

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any
from models import PlantData, OptimizationResult, OptimizationPriority
from gemini_service import GeminiOptimizationService
from data_generator import CementDataGenerator

class CementOptimizationAgent:
    """AI-powered cement plant optimization agent using Gemini for intelligent analysis"""
    
    def __init__(self):
        self.gemini_service = GeminiOptimizationService()
        self.data_generator = CementDataGenerator()
        self.monitoring_active = False
        self.analysis_history: List[Dict] = []
        self.performance_trends = {
            "energy_efficiency": [],
            "production_rate": [],
            "anomaly_count": []
        }
    
    
    async def analyze_plant_data(self, plant_data: PlantData) -> Dict[str, Any]:
        """Main method to analyze plant data using Gemini AI for intelligent recommendations"""
        
        try:
            energy_efficiency = plant_data.power_consumption_kw / plant_data.cement_production_tph if plant_data.cement_production_tph > 0 else 0
            baseline_data = self.data_generator.get_baseline()
            
            plant_data_dict = self.gemini_service._serialize_data_for_gemini(plant_data.model_dump())
            baseline_dict = self.gemini_service._serialize_data_for_gemini(baseline_data.model_dump())
            plant_data_dict['energy_consumption_kwh_per_ton'] = energy_efficiency

            # Run all the async helper methods concurrently
            results = await asyncio.gather(
                self._get_gemini_raw_material_analysis(plant_data_dict, baseline_dict),
                self._get_gemini_grinding_analysis(plant_data_dict, baseline_dict),
                self._get_gemini_energy_analysis(plant_data_dict, baseline_dict),
                self._get_gemini_maintenance_analysis(plant_data_dict, baseline_dict),
                self.gemini_service.detect_anomalies(plant_data_dict, baseline_dict)
            )
            
            # Unpack the results from the `asyncio.gather` tuple
            raw_material_optimizations, grinding_optimizations, energy_optimizations, maintenance_insights, anomalies = results
            
            # --- CORRECTION STARTS HERE ---
            # These methods are synchronous, so they should not be awaited.
            priority_actions = self._get_priority_actions(energy_efficiency, plant_data.mill_speed_rpm, plant_data.limestone_pct)
            potential_savings = self.gemini_service._calculate_savings(energy_efficiency, plant_data.cement_production_tph)
            # --- CORRECTION ENDS HERE ---
            
            # ... (rest of the method remains the same)
            self.analysis_history.append({
                "timestamp": datetime.now(),
                "energy_efficiency": energy_efficiency,
                "anomalies_count": len(anomalies)
            })
            self.performance_trends["energy_efficiency"].append(energy_efficiency)
            self.performance_trends["production_rate"].append(plant_data.cement_production_tph)
            self.performance_trends["anomaly_count"].append(len(anomalies))
            
            return {
                "analysis_timestamp": datetime.now().isoformat(),
                "plant_status": "Optimal" if energy_efficiency <= 18 else "Sub-optimal",
                "energy_efficiency_kwh_per_ton": energy_efficiency,
                "current_performance": {
                    "cement_production_tph": plant_data.cement_production_tph,
                    "power_consumption_kw": plant_data.power_consumption_kw,
                    "mill_temperature_c": plant_data.mill_temperature_c,
                    "mill_speed_rpm": plant_data.mill_speed_rpm,
                    "limestone_pct": plant_data.limestone_pct,
                    "clay_pct": plant_data.clay_pct,
                    "iron_ore_pct": plant_data.iron_ore_pct,
                    "gypsum_pct": plant_data.gypsum_pct,
                },
                "raw_material_optimizations": raw_material_optimizations,
                "grinding_optimizations": grinding_optimizations,
                "energy_optimizations": energy_optimizations,
                "maintenance_recommendations": maintenance_insights,
                "anomalies_detected": anomalies,
                "priority_actions": priority_actions,
                "potential_savings": potential_savings
            }
            
        except Exception as e:
            return {
                "error": f"AI agent analysis failed: {str(e)}",
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "ANALYSIS_FAILED"
            }
            
    # --- Helper methods to call Gemini and parse results ---
    
    async def _get_gemini_raw_material_analysis(self, plant_data: Dict, baseline_data: Dict) -> Dict:
        # Data is already serialized
        prompt = f"Analyze the raw material mix for a cement plant. Current data: {json.dumps(plant_data)}. Baseline data: {json.dumps(baseline_data)}. Focus on limestone content (target 78-82%), and provide a status and recommendations. Be concise and provide point wisequantifiable insights."
        response = await self.gemini_service._call_gemini_api(prompt)
        return {"summary": response, "status": "Optimized" if 78 <= plant_data.get('limestone_pct', 0) <= 82 else "Requires adjustment"}

    async def _get_gemini_grinding_analysis(self, plant_data: Dict, baseline_data: Dict) -> Dict:
        # Data is already serialized
        prompt = f"Analyze the grinding process data for a cement plant. Current data: {json.dumps(plant_data)}. Baseline data: {json.dumps(baseline_data)}. Focus on mill speed (target 16.5-18.5 RPM) and energy efficiency. Provide point wise recommendations(not too long)."
        response = await self.gemini_service._call_gemini_api(prompt)
        return {"summary": response, "status": "Optimal" if 16.5 <= plant_data.get('mill_speed_rpm', 0) <= 18.5 else "Requires adjustment"}
        
    async def _get_gemini_energy_analysis(self, plant_data: Dict, baseline_data: Dict) -> Dict:
        # Data is already serialized
        prompt = f"Analyze energy efficiency for a cement plant. Current data: {json.dumps(plant_data)}. Baseline data: {json.dumps(baseline_data)}. Target is <18 kWh/ton. Provide concise points of the energy status and optimization tips."
        response = await self.gemini_service._call_gemini_api(prompt)
        return {"summary": response, "status": "Optimal" if plant_data.get('energy_consumption_kwh_per_ton', 0) <= 18 else "Sub-optimal"}

    async def _get_gemini_maintenance_analysis(self, plant_data: Dict, baseline_data: Dict) -> Dict:
        # Data is already serialized
        prompt = f"Analyze the operational data for predictive maintenance insights. Current data: {json.dumps(plant_data)}. Baseline data: {json.dumps(baseline_data)}. Focus on vibration levels and mill temperature. Provide points and any alerts."
        response = await self.gemini_service._call_gemini_api(prompt)
        return {"summary": response, "status": "Normal" if plant_data.get('vibration_level', 0) < 3.0 and plant_data.get('mill_temperature_c', 0) < 95 else "Alerts detected"}

    def _get_priority_actions(self, energy_efficiency: float, mill_speed_rpm: float, limestone_pct: float) -> List[str]:
        """Provides rule-based priority actions based on key metrics"""
        actions = []
        if energy_efficiency > 20:
            actions.append("Adjust mill speed to reduce high power consumption.")
        if mill_speed_rpm > 18.5:
            actions.append("Reduce mill speed to optimize grinding and lower energy use.")
        if limestone_pct > 82 or limestone_pct < 78:
            actions.append("Adjust limestone feeder rate to correct raw material composition.")
        
        if not actions:
            actions.append("No critical actions needed. Plant operations are stable.")
            
        return actions

    # --- Other methods remain the same ---

    def get_performance_summary(self) -> Dict[str, Any]:
        """Provides a summary of the agent's historical performance"""
        avg_efficiency = sum(self.performance_trends["energy_efficiency"]) / len(self.performance_trends["energy_efficiency"]) if self.performance_trends["energy_efficiency"] else 0
        avg_production = sum(self.performance_trends["production_rate"]) / len(self.performance_trends["production_rate"]) if self.performance_trends["production_rate"] else 0
        total_anomalies = sum(self.performance_trends["anomaly_count"])

        return {
            "total_analysis_cycles": len(self.analysis_history),
            "average_energy_efficiency_kwh_per_ton": round(avg_efficiency, 2),
            "average_production_tph": round(avg_production, 2),
            "total_anomalies_detected": total_anomalies,
            "trends": self.performance_trends
        }