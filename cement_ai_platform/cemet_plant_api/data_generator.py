import numpy as np
import random
from datetime import datetime, timedelta
from typing import List
from models import PlantData

class CementDataGenerator:
    def __init__(self):
        self.base_conditions = {
            'limestone_pct': 80.0,
            'clay_pct': 13.0,
            'iron_ore_pct': 4.0,
            'gypsum_pct': 3.0,
            'mill_speed_rpm': 17.5,
            'power_consumption_kw': 850,
            'cement_production_tph': 50.0,
            'blaine_fineness': 3500,
            'mill_temperature_c': 90,
            'vibration_level': 2.5,
            'separator_speed_rpm': 150
        }
        
        self.scenarios = {
            "normal": {"variation": 1.0, "anomaly_rate": 0.05},
            "high_load": {"variation": 1.3, "anomaly_rate": 0.10, "production_boost": 1.15},
            "maintenance": {"variation": 0.8, "anomaly_rate": 0.20, "efficiency_drop": 0.85},
            "startup": {"variation": 1.8, "anomaly_rate": 0.30, "instability": True}
        }
    
    def generate_single_point(self, scenario: str = "normal") -> PlantData:
        """Generate single realistic data point"""
        
        scenario_config = self.scenarios.get(scenario, self.scenarios["normal"])
        variation = scenario_config["variation"]
        
        # Raw materials with natural variation
        limestone = self.base_conditions['limestone_pct'] + np.random.normal(0, 1.5 * variation)
        clay = self.base_conditions['clay_pct'] + np.random.normal(0, 0.8 * variation)
        iron_ore = self.base_conditions['iron_ore_pct'] + np.random.normal(0, 0.4 * variation)
        gypsum = self.base_conditions['gypsum_pct'] + np.random.normal(0, 0.3 * variation)
        
        # Normalize to 100%
        total = limestone + clay + iron_ore + gypsum
        limestone = (limestone / total) * 100
        clay = (clay / total) * 100
        iron_ore = (iron_ore / total) * 100
        gypsum = (gypsum / total) * 100
        
        # Mill operations
        mill_speed = self.base_conditions['mill_speed_rpm'] + np.random.normal(0, 0.4 * variation)
        
        # Production with scenario effects
        production_factor = scenario_config.get("production_boost", 1.0)
        efficiency_factor = scenario_config.get("efficiency_drop", 1.0)
        
        if scenario_config.get("instability"):
            mill_speed += np.random.normal(0, 1.0)
            
        base_production = self.base_conditions['cement_production_tph'] * production_factor
        production = base_production + np.random.normal(0, 2.0 * variation)
        
        # Power consumption (realistic relationship)
        speed_factor = mill_speed / self.base_conditions['mill_speed_rpm']
        load_factor = production / base_production
        base_power = self.base_conditions['power_consumption_kw'] / efficiency_factor
        power = base_power * (speed_factor ** 1.5) * (load_factor ** 0.8)
        power += np.random.normal(0, 30 * variation)
        
        # Quality parameters
        blaine = self.base_conditions['blaine_fineness'] + np.random.normal(0, 150 * variation)
        temperature = self.base_conditions['mill_temperature_c'] + np.random.normal(0, 4 * variation)
        vibration = self.base_conditions['vibration_level'] + np.random.normal(0, 0.3 * variation)
        separator_speed = self.base_conditions['separator_speed_rpm'] + np.random.normal(0, 5 * variation)
        
        # Inject anomalies
        if random.random() < scenario_config["anomaly_rate"]:
            anomaly_type = random.choice(["power_spike", "material_variation", "equipment_issue"])
            
            if anomaly_type == "power_spike":
                power *= random.uniform(1.15, 1.30)
            elif anomaly_type == "material_variation":
                limestone += random.uniform(-6, 6)
            elif anomaly_type == "equipment_issue":
                vibration *= random.uniform(1.5, 2.5)
                power *= random.uniform(1.10, 1.25)
        
        return PlantData(
            timestamp=datetime.now(),
            limestone_pct=round(max(0, min(100, limestone)), 2),
            clay_pct=round(max(0, min(100, clay)), 2),
            iron_ore_pct=round(max(0, min(100, iron_ore)), 2),
            gypsum_pct=round(max(0, min(100, gypsum)), 2),
            mill_speed_rpm=round(max(0, mill_speed), 1),
            power_consumption_kw=round(max(0, power), 0),
            cement_production_tph=round(max(0, production), 1),
            blaine_fineness=round(max(0, blaine), 0),
            mill_temperature_c=round(temperature, 1),
            vibration_level=round(max(0, vibration), 2),
            separator_speed_rpm=round(max(0, separator_speed), 0)
        )
    
    def generate_stream(self, duration_minutes: int, interval_seconds: int, scenario: str = "normal") -> List[PlantData]:
        """Generate stream of data points"""
        
        points_count = (duration_minutes * 60) // interval_seconds
        data_stream = []
        
        for i in range(int(points_count)):
            data_point = self.generate_single_point(scenario)
            # Adjust timestamp for proper sequence
            data_point.timestamp = datetime.now() + timedelta(seconds=i * interval_seconds)
            data_stream.append(data_point)
        
        return data_stream
    
    def get_baseline(self) -> PlantData:
        """Get optimal baseline conditions"""
        return PlantData(**self.base_conditions)