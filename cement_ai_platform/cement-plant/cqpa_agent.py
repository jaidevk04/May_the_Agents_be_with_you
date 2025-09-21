import time
import joblib
import pandas as pd
import numpy as np
from data_tools import load_and_pivot_quality_data
import warnings
import requests
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from pydantic import BaseModel
import json
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
from simulation_state import simulation_status, SimulationEvent
load_dotenv()

class ClinkerQualityPredictionAgent:
    def __init__(self, model_path='models/freelime_model.pkl', 
                 scaler_path='models/freelime_scaler.pkl',
                 info_path='models/model_info.pkl',
                 threshold=2.5):
        
        print("Loading CQPA model...")
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        self.model_info = joblib.load(info_path)
        
        self.threshold = threshold
        self.feature_columns = self.model_info['feature_columns']
        self.target_column = self.model_info['target_column']
        
        print(f"Model loaded. Target: {self.target_column}")
        print(f"Features: {len(self.feature_columns)} columns")
        print(f"Alert threshold: {self.threshold}")
        
        # For tracking predictions
        self.prediction_history = []
        self.alert_count = 0

    def predict_freelime(self, row_data):
        """
        Make prediction for a single row of data
        """
        try:
            # Extract features in correct order
            features = []
            for col in self.feature_columns:
                if col in row_data:
                    features.append(row_data[col])
                else:
                    features.append(0)  # Default value for missing features
            
            # Scale and predict
            features_scaled = self.scaler.transform([features])
            prediction = self.model.predict(features_scaled)[0]
            
            return prediction
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return None

    def simulate_realtime_monitoring(self, test_quality_path, llm_callback):
        """
        Simulate real-time monitoring using test data
        """
        print("Starting real-time simulation...")
        
        # Load test data
        df_test = load_and_pivot_quality_data(test_quality_path)
        df_test = df_test.ffill().bfill()
        
        print(f"Loaded {len(df_test)} test samples")
        
        # Setup session and runner once
        session_service = InMemorySessionService()
        runner = Runner(agent=llm_agent, app_name="CQPA_APP", session_service=session_service)
        
        while True:
            for idx, (_, row) in enumerate(df_test.iterrows()):
                timestamp = row['timestamp']
                
                # Make prediction
                prediction = self.predict_freelime(row)
                
                if prediction is not None:
                    new_history_item = row.to_dict()
                    new_history_item['prediction'] = prediction
                    new_history_item['alert'] = prediction > self.threshold
                    self.prediction_history.append(new_history_item)
                    
                    print(f"[{timestamp}] Free Lime Prediction: {prediction:.4f}")
                    
                    event = SimulationEvent(timestamp=str(timestamp), prediction=prediction)
                    
                    # Check if alert threshold exceeded
                    if prediction > self.threshold:
                        self.alert_count += 1
                        alert_message = f"🚨 ALERT #{self.alert_count}: Free Lime {prediction:.4f} exceeds threshold {self.threshold}"
                        print(alert_message)
                        event.alert = alert_message
                        
                        # Get recent context as a list of dicts
                        recent_context = self.get_recent_context(10)
                        
                        # Trigger LLM callback
                        session_id = f"session_{timestamp.strftime('%Y%m%d%H%M%S')}"
                        llm_response = asyncio.run(llm_callback(runner, recent_context, prediction, session_id))
                        event.llm_response = llm_response
                    
                    simulation_status.events.append(event)
                    
                    # Simulate real-time delay
                    time.sleep(2)
        
        print(f"\nSimulation complete. Total alerts: {self.alert_count}")

    def get_recent_context(self, n=10):
        """
        Get recent prediction history for context
        """
        if len(self.prediction_history) < n:
            return self.prediction_history
        return self.prediction_history[-n:]

from typing import List, Dict, Any

def get_recent_metrics(context_rows: List[Dict[str, Any]]) -> dict:
    """
    Compute summary stats of recent process and FreeLime.

    Args:
        context_rows: A list of dictionaries containing recent prediction history.

    Returns:
        A dictionary with the average of key process parameters.
    """
    if not context_rows:
        return {}
    df = pd.DataFrame(context_rows)
    summary = {}
    # Add all quality and process columns to the summary
    for col in df.columns:
        if 'Quality' in col or 'Process' in col or col == 'prediction' or col == 'Output Parameter':
            summary[col + "_avg"] = float(df[col].tail(10).mean())
    return summary


recent_metrics_tool = FunctionTool(func=get_recent_metrics)


API_URL = "http://127.0.0.1:8000"

def get_plant_state() -> dict:
    """
    Retrieves the current state of the plant control parameters.

    Returns:
        A dictionary containing the current kiln_speed, fuel_rate, and raw_mix_composition.
    """
    try:
        response = requests.get(f"{API_URL}/plant_state")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def set_plant_controls(kiln_speed: float, fuel_rate: float, raw_mix_composition: str, cooler_speed: float, coal_feed_rate: float) -> dict:
    """
    Sets new values for the plant control parameters.

    Args:
        kiln_speed: The new speed for the kiln.
        fuel_rate: The new rate for the fuel.
        raw_mix_composition: The new raw mix composition.
        cooler_speed: The new speed for the cooler.
        coal_feed_rate: The new rate for the coal feed.

    Returns:
        A dictionary confirming the update and showing the new state.
    """
    try:
        payload = {
            "kiln_speed": kiln_speed,
            "fuel_rate": fuel_rate,
            "raw_mix_composition": raw_mix_composition,
            "cooler_speed": cooler_speed,
            "coal_feed_rate": coal_feed_rate
        }
        response = requests.post(f"{API_URL}/control", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

plant_state_tool = FunctionTool(func=get_plant_state)
set_controls_tool = FunctionTool(func=set_plant_controls)


class LLMInputSchema(BaseModel):
    timestamp: str
    predicted_free_lime: float
    recent_metrics: dict


class LLMSuggestionSchema(BaseModel):
    action: str
    suggested_setpoints: dict
    risk: str
    predicted_improvement: dict


llm_agent = LlmAgent(
    name="CQPA_Overlay_Agent",
    model="gemini-2.5-flash",
    description="Diagnose & suggest process changes when Free Lime crosses threshold",
    instruction="""
You are the CQPA Overlay Agent. Your goal is to maintain Free Lime levels below the threshold.
When Free Lime is high, your task is to diagnose the issue and take corrective action.

Follow these steps:
1. Use the 'get_recent_metrics' tool to get summary statistics of the process.
2. Use the 'get_plant_state' tool to understand the current control parameter setpoints.
3. Analyze the metrics and the current setpoints to diagnose the potential cause of the high Free Lime.
4. Based on your diagnosis, decide on new setpoints for kiln speed, fuel rate, raw mix, cooler speed, and coal feed rate.
5. Use the 'set_plant_controls' tool to apply the new setpoints.
6. After applying the changes, summarize the action taken, the reasoning, and the expected outcome.

Respond ONLY as JSON matching LLMSuggestionSchema. The 'suggested_setpoints' should reflect the values you passed to the 'set_plant_controls' tool.
""",
    tools=[recent_metrics_tool, plant_state_tool, set_controls_tool],
    input_schema=LLMInputSchema,
    output_schema=LLMSuggestionSchema,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True
)


async def llm_reasoner(runner, context_rows, predicted_free_lime, session_id):
    user_id = "user123"
    
    # Create a new session for each invocation
    await runner.session_service.create_session(app_name=runner.app_name, user_id=user_id, session_id=session_id)

    summary = get_recent_metrics(context_rows)
    
    # Convert to DataFrame to get the last timestamp
    context_df = pd.DataFrame(context_rows)
    
    input_data = {
        "timestamp": str(context_df.iloc[-1]["timestamp"]),
        "predicted_free_lime": float(predicted_free_lime),
        "recent_metrics": summary
    }
    
    # Create a message with the input data
    message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps(input_data))]
    )

    events = runner.run(user_id=user_id, session_id=session_id, new_message=message)
    
    for event in events:
        if event.is_final_response():
            response_text = event.content.parts[0].text
            print("LLM Overlay Suggestion:")
            try:
                # Try to parse the JSON response
                response_json = json.loads(response_text)
                print(json.dumps(response_json, indent=2))
                return response_json
            except json.JSONDecodeError:
                # If it's not JSON, print the raw text
                print(response_text)
                return {"raw_text": response_text}


if __name__ == "__main__":
    # Initialize CQPA
    try:
        agent = ClinkerQualityPredictionAgent(threshold=2.0)  # Lower threshold for demo
        
        # Start monitoring simulation with test data
        test_quality_path = 'archive/CAX_Test_Quality/CAX_Test_Quality.csv'
        agent.simulate_realtime_monitoring(test_quality_path, llm_reasoner)
        
    except FileNotFoundError as e:
        print(f"Error: Required files not found - {e}")
        print("Please run train_model.py first to create the model files")
    except Exception as e:
        print(f"Error: {e}")
