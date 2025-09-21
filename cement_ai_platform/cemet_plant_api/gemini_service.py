# gemini_service.py

import os
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
import logging

logger = logging.getLogger(__name__)

class GeminiOptimizationService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable required")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=self._get_system_instruction()
        )
        
        self.generation_config = GenerationConfig(
            temperature=0.1,
            top_p=0.9,
            max_output_tokens=4000
        )

    def _serialize_data_for_gemini(self, data: Dict) -> Dict:
        """Convert data to JSON serializable format"""
        serialized = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                # Convert datetime objects to ISO 8601 strings
                serialized[key] = value.isoformat()
            else:
                serialized[key] = value
        return serialized
    
    def _get_system_instruction(self) -> str:
        return """
        You are an expert cement plant optimization AI with deep knowledge in:
        
        - Cement manufacturing processes and energy optimization
        - Target energy efficiency: <18 kWh/ton 
        - Raw material optimization (limestone 78-82%)
        - Mill circuit efficiency and grinding optimization
        - Predictive maintenance using operational data
        
        RESPONSE FORMAT:
        - Use priority levels: 🔴 CRITICAL, 🟡 WARNING, 🟢 NORMAL, 🟢 OPTIMAL
        - Provide specific parameter targets and quantified savings
        - Focus on immediate actionable recommendations
        - Include safety considerations
        
        OPTIMIZATION PRIORITIES:
        1. Safety and equipment protection
        2. Energy efficiency (target <18 kWh/ton)
        3. Production optimization
        4. Raw material cost reduction
        5. Quality maintenance
        6. Preventive maintenance
        """
    
    async def analyze_plant_data(self, plant_data: Dict, optimization_focus: List[str]) -> Dict[str, Any]:
        """Comprehensive plant optimization analysis"""
        try:
            # Serialize data for JSON compatibility
            serialized_data = self._serialize_data_for_gemini(plant_data)
            
            energy_per_ton = serialized_data.get('power_consumption_kw', 0) / max(serialized_data.get('cement_production_tph', 1), 1)
            
            prompt = f"""
            CEMENT PLANT OPTIMIZATION ANALYSIS:
            
            Plant Data: {json.dumps(serialized_data, indent=2)}
            Current Energy Efficiency: {energy_per_ton:.2f} kWh/ton
            Target: <18.0 kWh/ton
            Focus Areas: {', '.join(optimization_focus)}
            
            ANALYSIS REQUIRED:
            
            1. IMMEDIATE STATUS:
               - Overall plant status and safety assessment
               - Energy efficiency vs target evaluation
               - Critical issues requiring immediate attention
            
            2. ENERGY OPTIMIZATION:
               - Power consumption analysis and optimization opportunities
               - Mill speed/loading optimization recommendations
               - Grinding efficiency improvements
               - Estimated energy savings potential
            
            3. OPERATIONAL RECOMMENDATIONS:
               - Mill speed adjustments (target: 16.5-18.5 RPM)
               - Raw material ratio optimization
               - Production rate improvements
               - Temperature and quality control
            
            4. MACHINE CONTROLS:
               - Specific parameter adjustments with target values
               - Control system recommendations
               - Implementation priorities
            
            5. PREDICTIVE MAINTENANCE:
               - Equipment health assessment from operational data
               - Maintenance scheduling recommendations
               - Performance trend analysis
            
            Provide specific, quantified recommendations with target values,
            estimated savings, implementation time, and safety considerations.
            """
            
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt,
                generation_config=self.generation_config
            )
            
            if not response.text:
                raise Exception("Empty response from Gemini")
            
            return self._parse_analysis_response(response.text, serialized_data, energy_per_ton)
            
        except Exception as e:
            logger.error(f"Gemini analysis error: {e}")
            energy_per_ton = plant_data.get('power_consumption_kw', 0) / max(plant_data.get('cement_production_tph', 1), 1)
            return {
                "error": str(e),
                "status": "🔴 CRITICAL",
                "message": "AI analysis service error",
                "energy_efficiency_kwh_per_ton": energy_per_ton,
                "recommendations": ["Manual analysis required due to service error"],
                "maintenance_alerts": [],
                "machine_controls": [],
                "predicted_savings": {}
            }
    
    def _parse_analysis_response(self, response_text: str, plant_data: Dict, energy_per_ton: float) -> Dict[str, Any]:
        """Parse response into structured data"""
        
        # Determine status
        if energy_per_ton > 25 or "critical" in response_text.lower():
            status = "🔴 CRITICAL"
        elif energy_per_ton > 20 or "warning" in response_text.lower():
            status = "🟡 WARNING"
        elif energy_per_ton < 18:
            status = "🟢 OPTIMAL"
        else:
            status = "🟢 NORMAL"
        
        # Extract recommendations
        recommendations = []
        maintenance_alerts = []
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(('•', '-', '1.', '2.', '3.', '*')) and len(line) > 20:
                if 'maintenance' in line.lower():
                    maintenance_alerts.append(line.lstrip('•-123456789.* '))
                else:
                    recommendations.append(line.lstrip('•-123456789.* '))
        
        # Generate machine controls
        machine_controls = self._generate_machine_controls(plant_data, energy_per_ton)
        
        # Calculate savings
        savings = self._calculate_savings(energy_per_ton, plant_data.get('cement_production_tph', 50))
        
        return {
            "analysis_text": response_text,
            "status": status,
            "energy_efficiency_kwh_per_ton": energy_per_ton,
            "recommendations": recommendations[:8],
            "maintenance_alerts": maintenance_alerts[:5],
            "machine_controls": machine_controls,
            "predicted_savings": savings
        }
    
    def _generate_machine_controls(self, plant_data: Dict, energy_per_ton: float) -> List[Dict]:
        """Generate machine control actions"""
        controls = []
        
        mill_speed = plant_data.get('mill_speed_rpm', 17.5)
        limestone = plant_data.get('limestone_pct', 80)
        temperature = plant_data.get('mill_temperature_c', 90)
        production = plant_data.get('cement_production_tph', 50)
        
        # Mill speed control
        if energy_per_ton > 20:
            target_speed = max(16.5, mill_speed - 0.5)
            controls.append({
                "machine_id": "MILL_01",
                "parameter": "speed_rpm",
                "current_value": mill_speed,
                "target_value": target_speed,
                "action": f"Reduce mill speed from {mill_speed:.1f} to {target_speed:.1f} RPM",
                "priority": "🔴 CRITICAL" if energy_per_ton > 25 else "🟡 WARNING",
                "estimated_savings": f"3-5% energy reduction"
            })
        
        # Raw material control
        if limestone > 82 or limestone < 78:
            target_limestone = 80.0
            controls.append({
                "machine_id": "RAW_FEEDER_01",
                "parameter": "limestone_pct",
                "current_value": limestone,
                "target_value": target_limestone,
                "action": f"Adjust limestone content to {target_limestone}%",
                "priority": "🟡 WARNING",
                "estimated_savings": "2-3% energy savings"
            })
        
        # Temperature control
        if temperature > 95:
            controls.append({
                "machine_id": "VENTILATION_01",
                "parameter": "air_flow",
                "current_value": 200.0,
                "target_value": 220.0,
                "action": "Increase mill ventilation",
                "priority": "🔴 CRITICAL" if temperature > 100 else "🟡 WARNING",
                "estimated_savings": "Prevent quality degradation"
            })
        
        # Production optimization
        if production < 48:
            controls.append({
                "machine_id": "FEEDER_01",
                "parameter": "feed_rate",
                "current_value": production,
                "target_value": min(52.0, production * 1.05),
                "action": "Increase feed rate for higher production",
                "priority": "🟡 WARNING",
                "estimated_savings": "3-5% production increase"
            })
        
        return controls[:5]
    
    def _calculate_savings(self, energy_per_ton: float, production_tph: float) -> Dict[str, float]:
        """Calculate potential savings"""
        
        if energy_per_ton > 18:
            target_energy = 18.0
            energy_savings = energy_per_ton - target_energy
        else:
            target_energy = energy_per_ton * 0.98
            energy_savings = energy_per_ton * 0.02
        
        daily_production = production_tph * 24
        daily_energy_savings = energy_savings * daily_production
        daily_cost_savings = daily_energy_savings * 0.08  # $0.08/kWh
        
        return {
            "energy_savings_kwh_per_ton": energy_savings,
            "daily_cost_savings_usd": daily_cost_savings,
            "annual_savings_usd": daily_cost_savings * 365,
            "production_increase_potential_pct": min(5.0, energy_savings * 2)
        }

    async def detect_anomalies(self, current_data: Dict, baseline_data: Dict) -> List[str]:
        """Detect anomalies by comparing current vs baseline"""
        try:
            # Serialize both datasets
            current_serialized = self._serialize_data_for_gemini(current_data)
            baseline_serialized = self._serialize_data_for_gemini(baseline_data)
            
            # Simple anomaly detection without Gemini call (to avoid serialization issues)
            anomalies = []
            
            current_energy = current_serialized.get('power_consumption_kw', 0) / max(current_serialized.get('cement_production_tph', 1), 1)
            baseline_energy = baseline_serialized.get('power_consumption_kw', 0) / max(baseline_serialized.get('cement_production_tph', 1), 1)
            
            if abs(current_energy - baseline_energy) > 2:
                anomalies.append(f"🟡 Energy efficiency deviation: {abs(current_energy - baseline_energy):.1f} kWh/ton")
            
            limestone_dev = abs(current_serialized.get('limestone_pct', 0) - baseline_serialized.get('limestone_pct', 80))
            if limestone_dev > 3:
                anomalies.append(f"🟡 Limestone composition deviation: {limestone_dev:.1f}%")
            
            temp_dev = abs(current_serialized.get('mill_temperature_c', 0) - baseline_serialized.get('mill_temperature_c', 90))
            if temp_dev > 8:
                anomalies.append(f"🔴 Temperature anomaly: {temp_dev:.1f}°C deviation")
            
            production_dev = abs(current_serialized.get('cement_production_tph', 0) - baseline_serialized.get('cement_production_tph', 50))
            if production_dev > 8:
                anomalies.append(f"🟡 Production rate deviation: {production_dev:.1f} tph")
            
            vibration_current = current_serialized.get('vibration_level', 2.5)
            vibration_baseline = baseline_serialized.get('vibration_level', 2.5)
            if vibration_current > vibration_baseline * 1.5:
                anomalies.append(f"🔴 High vibration detected: {vibration_current:.1f}")
            
            return anomalies
            
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return [f"🔴 Anomaly detection error: {str(e)}"]

    async def _call_gemini_api(self, prompt: str) -> str:
        """Helper to make an API call to Gemini and handle errors."""
        try:
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt,
                generation_config=self.generation_config
            )
            return response.text
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return f"Error: Failed to get analysis from AI service."