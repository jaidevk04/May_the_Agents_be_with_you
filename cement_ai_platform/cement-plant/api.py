from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
from cqpa_agent import ClinkerQualityPredictionAgent, llm_reasoner
from simulation_state import simulation_status, reset_simulation_status

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ControlParams(BaseModel):
    kiln_speed: float
    fuel_rate: float
    raw_mix_composition: str
    cooler_speed: float
    coal_feed_rate: float

# In-memory state for the plant
plant_state = {
    "kiln_speed": 5.0,
    "fuel_rate": 100.0,
    "raw_mix_composition": "Standard",
    "cooler_speed": 3.0,
    "coal_feed_rate": 20.0
}

def run_simulation_in_background():
    try:
        agent = ClinkerQualityPredictionAgent(threshold=1.8)
        test_path = 'archive/CAX_Test_Quality/CAX_Test_Quality.csv'
        agent.simulate_realtime_monitoring(test_path, llm_reasoner)
    except Exception as e:
        simulation_status.is_running = False
        simulation_status.error = str(e)

@app.post("/start-simulation")
def start_simulation(background_tasks: BackgroundTasks):
    if simulation_status.is_running:
        return {"message": "Simulation is already running"}
    
    reset_simulation_status()
    simulation_status.is_running = True
    
    # Run the simulation in a background thread
    thread = threading.Thread(target=run_simulation_in_background)
    thread.start()
    
    return {"message": "Simulation started successfully"}

@app.get("/simulation-status")
def get_simulation_status():
    return simulation_status

@app.get("/plant_state")
def get_plant_state():
    return plant_state

@app.post("/control")
def set_control_params(params: ControlParams):
    plant_state["kiln_speed"] = params.kiln_speed
    plant_state["fuel_rate"] = params.fuel_rate
    plant_state["raw_mix_composition"] = params.raw_mix_composition
    plant_state["cooler_speed"] = params.cooler_speed
    plant_state["coal_feed_rate"] = params.coal_feed_rate
    return {"message": "Plant control parameters updated successfully", "new_state": plant_state}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
