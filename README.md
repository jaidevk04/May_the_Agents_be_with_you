# CementAI Operations Hub - Autonomous Cement Plant Control

This project is a proof-of-concept for a Generative AI-driven platform for autonomous cement plant operations, designed to optimize energy use, quality, and sustainability. It was developed for the "Optimizing Cement Operations with Generative AI" hackathon.

The platform features a multi-agent backend system and a sleek, real-time frontend dashboard, simulating the monitoring and control of three critical stages of the cement manufacturing process.

![Dashboard Screenshot](cementflow-ai-main/src/assets/cement-plant-hero.jpg)

## Architecture Overview

The system is built on a microservices architecture, with a central frontend application communicating with three specialized backend services. Each backend service is powered by its own AI agent, responsible for a specific domain of the plant.

-   **Frontend**: A React-based dashboard (`cementflow-ai-main`) that provides a centralized view and control interface for the entire plant.
-   **Backend**: A collection of Python FastAPI services (`cement_ai_platform`) that simulate the plant processes and run the AI agents.

## Project Components

The project is divided into four main components:

### 1. Frontend Dashboard (`cementflow-ai-main`)

A modern, data-rich web application that serves as the central hub for monitoring and controlling the plant. It features:
-   A real-time overview of key plant KPIs.
-   Dedicated pages for each process area.
-   Live charts, alert feeds, and interactive controls.
-   A futuristic, industrial dark-mode theme.

### 2. Raw Materials & Grinding Agent (`cement_ai_platform/cemet_plant_api`)

-   **Use Case**: Optimize Raw Materials & Grinding
-   **Functionality**: Provides on-demand, strategic analysis of the raw material mix and grinding efficiency using the Gemini API to generate comprehensive optimization and maintenance recommendations.

### 3. Clinkerization Control Agent (`cement_ai_platform/cement-plant`)

-   **Use Case**: Balance Clinkerization Parameters
-   **Functionality**: Runs a real-time simulation of the clinkerization process. It uses a local ML model to predict clinker quality and an LLM agent to autonomously apply corrective actions to the plant controls when quality deviates.

### 4. Quality Control Agent (`cement_ai_platform/qc_backend`)

-   **Use Case**: Ensure Quality Consistency
-   **Functionality**: Implements a proactive, closed-loop quality control system. It uses statistical methods to detect process drift and an LLM planner to propose, simulate, and apply corrective action plans, ensuring final product quality.

## Technology Stack

-   **Frontend**: React, TypeScript, Vite, Tailwind CSS, Recharts
-   **Backend**: Python, FastAPI, Uvicorn
-   **AI**: Google Gemini
-   **Machine Learning**: Scikit-learn, Joblib

## How to Run the Project

### Prerequisites

-   Python 3.10+
-   Node.js and npm

### 1. Setup Backend Services

Each backend service needs to be set up and run in its own terminal.

**For each service (`cement-plant`, `cemet_plant_api`, `qc_backend`):**

```bash
# Navigate to the service directory
cd cement_ai_platform/[service-name]

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set API Key (for qc_backend and cement-plant)
# Copy .env.example to .env if it exists, and add your Gemini API key
# Example for qc_backend:
# cp .env.example .env
# nano .env 
```

### 2. Run Backend Services

Open three separate terminals and run the following commands:

**Terminal 1: Start Clinkerization Service**
```bash
cd cement_ai_platform/cement-plant
source .venv/bin/activate
python api.py
```

**Terminal 2: Start Raw Materials Service**
```bash
cd cement_ai_platform/cemet_plant_api
source .venv/bin/activate
PORT=8001 python main.py
```

**Terminal 3: Start Quality Control Service**
```bash
cd cement_ai_platform/qc_backend
source .venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 8002
```

### 3. Run Frontend Application

Open a fourth terminal to run the frontend.

```bash
# Navigate to the frontend directory
cd cementflow-ai-main

# Install dependencies
npm install

# Start the development server
npm run dev
```

### 4. Access the Live Demo

Once all services are running, open your browser and navigate to:

**http://localhost:8080**

You should see the CementAI Operations Hub dashboard, displaying live data from the three running backend services. You can navigate between the different pages to interact with each of the AI agents.
