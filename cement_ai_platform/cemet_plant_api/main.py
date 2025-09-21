# main.py

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Import routers and services from the correct file names
from optimization import router as optimization_router
from machine_control_api import router as control_router
from data_generator import CementDataGenerator
from cement_agent import CementOptimizationAgent
from models import PlantData, DataGenerationRequest, OptimizationResult

# Global instances
data_generator = CementDataGenerator()
# Initialize the agent
optimization_agent = CementOptimizationAgent() 

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Cement Plant Optimization API Starting...")
    print("🤖 AI-Powered Real-Time Optimization System")
    print("=" * 50)
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Cement Plant API...")

# Create FastAPI app
app = FastAPI(
    title="Cement Plant Optimization API",
    description="AI-Powered Cement Plant Optimization with Gemini Integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(optimization_router)
app.include_router(control_router)

# Data generation endpoints
@app.post("/data/generate", response_model=PlantData, tags=["Data Generation"])
async def generate_plant_data(scenario: str = "normal"):
    """Generate single plant data point"""
    
    if scenario not in data_generator.scenarios:
        raise HTTPException(400, f"Invalid scenario. Options: {list(data_generator.scenarios.keys())}")
    
    return data_generator.generate_single_point(scenario)

@app.post("/data/stream", tags=["Data Generation"])
async def generate_data_stream(request: DataGenerationRequest):
    """Generate stream of plant data"""
    
    if request.duration_minutes * 60 // request.interval_seconds > 500:
        raise HTTPException(400, "Too many data points requested")
    
    data_stream = data_generator.generate_stream(
        request.duration_minutes,
        request.interval_seconds, 
        request.scenario
    )
    
    return {
        "total_points": len(data_stream),
        "duration_minutes": request.duration_minutes,
        "interval_seconds": request.interval_seconds,
        "scenario": request.scenario,
        "data": data_stream
    }

@app.get("/data/baseline", response_model=PlantData, tags=["Data Generation"])
async def get_baseline_data():
    """Get optimal baseline plant conditions"""
    return data_generator.get_baseline()

@app.get("/data/scenarios", tags=["Data Generation"])
async def get_scenarios():
    """Get available data generation scenarios"""
    return {
        "scenarios": data_generator.scenarios,
        "descriptions": {
            "normal": "Standard operating conditions",
            "high_load": "Peak production with higher energy use",
            "maintenance": "Reduced efficiency during maintenance",
            "startup": "Plant startup with high variability"
        }
    }

# Simplified Agent endpoints
@app.post("/agent/optimize", tags=["AI Agent"])
async def run_optimization():
    """Run single optimization cycle and return results"""
    
    try:
        # Generate current plant data
        current_data = data_generator.generate_single_point("normal")
        
        # Run optimization analysis
        result = await optimization_agent.analyze_plant_data(current_data)
        
        return {
            "timestamp": current_data.timestamp,
            "plant_data": current_data.model_dump_json(by_alias=True, indent=2),
            "agent_analysis": {
                "optimization_results": result,
                "energy_efficiency": current_data.energy_consumption_kwh_per_ton,
                "recommendations_count": len(result.get("recommendations", [])),
                "agent_confidence": "High",
                "analysis_type": "Real-time Plant Optimization"
            },
            "agent_performance": optimization_agent.get_performance_summary(),
            "generated_by": "AI Cement Plant Optimization Agent"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Agent optimization failed: {str(e)}")

@app.get("/agent/status", tags=["AI Agent"])
async def get_agent_status():
    """Get agent performance summary and historical data"""
    
    performance = optimization_agent.get_performance_summary()
    
    return {
        "agent_status": "AI Cement Optimization Agent - Online",
        "agent_message": "🤖 Agent ready for plant optimization analysis",
        "analysis_source": "Cement Optimization Agent powered by Google Gemini",
        "agent_capabilities": [
            "Real-time plant data analysis",
            "Energy efficiency optimization", 
            "Predictive maintenance insights",
            "Multi-scenario batch processing",
            "Safety parameter monitoring"
        ],
        "performance_data": performance,
        "generated_by": "AI Cement Plant Optimization Agent"
    }

@app.post("/agent/optimize-custom", tags=["AI Agent"])
async def run_custom_optimization(plant_data: PlantData):
    """Run optimization on custom plant data"""
    
    try:
        result = await optimization_agent.analyze_plant_data(plant_data)
        
        return {
            "agent_status": "AI Cement Optimization Agent - Custom Analysis",
            "agent_message": "🤖 Custom plant data analyzed by Gemini AI Agent",
            "status": "success",
            "timestamp": plant_data.timestamp,
            "analysis_source": "Cement Optimization Agent powered by Google Gemini",
            "plant_data": plant_data.model_dump_json(by_alias=True, indent=2),
            "agent_analysis": {
                "optimization_results": result,
                "recommendations_count": len(result.get("recommendations", [])),
                "agent_confidence": "High",
                "analysis_type": "Custom Plant Data Analysis"
            },
            "generated_by": "AI Cement Plant Optimization Agent"
        }
        
    except Exception as e:
        raise HTTPException(500, f"Agent custom optimization failed: {str(e)}")

@app.post("/agent/batch-optimize", tags=["AI Agent"])
async def run_batch_optimization(scenarios: list[str] = ["normal", "high_load", "maintenance"]):
    """Run optimization on multiple scenarios"""
    
    results = []
    
    for scenario in scenarios:
        if scenario not in data_generator.scenarios:
            continue
            
        try:
            # Generate data for scenario
            plant_data = data_generator.generate_single_point(scenario)
            
            # Run optimization
            optimization_result = await optimization_agent.analyze_plant_data(plant_data)
            
            results.append({
                "scenario": scenario,
                "agent_analysis": f"🤖 Scenario '{scenario}' analyzed by AI Agent",
                "plant_data": plant_data.model_dump_json(by_alias=True, indent=2),
                "optimization_results": optimization_result,
                "agent_confidence": "High"
            })
            
        except Exception as e:
            results.append({
                "scenario": scenario,
                "agent_message": f"❌ Agent failed to analyze scenario '{scenario}'",
                "error": str(e)
            })
    
    return {
        "agent_status": "AI Cement Optimization Agent - Batch Analysis Complete",
        "agent_message": f"🤖 {len(scenarios)} scenarios analyzed by Gemini AI Agent",
        "status": "success",
        "analysis_source": "Cement Optimization Agent powered by Google Gemini",
        "total_scenarios": len(scenarios),
        "successful_optimizations": len([r for r in results if "error" not in r]),
        "batch_results": results,
        "generated_by": "AI Cement Plant Optimization Agent"
    }

# System status
@app.get("/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "gemini_service": "connected",
        "timestamp": "2025-01-XX"  # Will use actual timestamp
    }

# Root endpoint with documentation
@app.get("/", response_class=HTMLResponse)
async def root():
    """API documentation and usage guide"""
    
    return """
    <html>
        <head>
            <title>Cement Plant Optimization API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .endpoint { background: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .method { color: #007acc; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>🏭 Cement Plant Optimization API</h1>
            <p>AI-Powered Real-Time Cement Plant Optimization with Gemini Integration</p>
            
            <h2>🚀 Quick Start</h2>
            <div class="endpoint">
                <span class="method">POST</span> /data/generate - Generate plant data
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /optimization/analyze - Analyze plant operations
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /optimization/quick-analysis - Quick energy analysis
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /controls/optimize-mill-speed - Auto-optimize mill
            </div>
            <div class="endpoint">
                <span class="method">POST</span> /agent/optimize - Run optimization and get results
            </div>
            
            <h2>📚 Documentation</h2>
            <p><a href="/docs">Interactive API Documentation (Swagger UI)</a></p>
            <p><a href="/redoc">Alternative Documentation (ReDoc)</a></p>
            
            <h2>🔧 Features</h2>
            <ul>
                <li>Real-time plant data generation with realistic scenarios</li>
                <li>AI-powered optimization analysis using Google Gemini</li>
                <li>Machine control automation with safety checks</li>
                <li>Single-call optimization with immediate results</li>
                <li>Energy efficiency optimization (target &lt;18 kWh/ton)</li>
                <li>Predictive maintenance insights</li>
            </ul>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )