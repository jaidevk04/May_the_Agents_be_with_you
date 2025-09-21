# Cement Plant Proactive Quality Control System

This project implements a proactive quality control (QC) system for a simulated cement plant. It uses a combination of statistical process control (SPC) for drift detection and a Large Language Model (LLM) to propose, simulate, and apply corrective action plans to maintain key quality indicators (KPIs) within their target ranges.

## Project Overview

The system is built around a FastAPI server that runs a continuous simulation of a cement plant's quality parameters. The core of the system is a closed-loop process:

1.  **Simulate**: Continuously generate realistic plant data.
2.  **Detect**: Analyze the stream of data in real-time to detect statistical drifts or breaches of quality targets.
3.  **Plan**: If an issue is detected, use a Generative AI agent to create a corrective action plan.
4.  **Verify**: Allow the operator to simulate the effect of the proposed plan before implementation.
5.  **Act**: Apply the validated plan to the plant controls.

This creates a "human-in-the-loop" autonomous control system, where the AI proposes solutions and the human operator provides the final approval.

## Theoretical Background

### Why Proactive Quality Control?

In cement manufacturing, maintaining consistent quality is paramount. The key quality KPIs, such as the **Lime Saturation Factor (LSF)** and **Blaine fineness**, are influenced by a complex interplay of variables in the raw mix and grinding process.

-   **Process Drift**: Over time, small variations in raw material composition, equipment wear, or environmental conditions can cause the process to "drift" away from its optimal setpoints. If left uncorrected, this drift can lead to a decline in product quality.
-   **Lag in Feedback**: Traditional quality control often relies on manual sampling and lab testing, which introduces delays. A proactive system that can detect the beginning of a deviation *before* it results in out-of-spec product is highly valuable. It reduces waste, improves efficiency, and ensures a more consistent final product.

### How the AI-Powered QC System Works

This project demonstrates a modern approach to quality control by combining two powerful techniques:

1.  **Statistical Drift Detection**: Instead of just alarming when a KPI goes outside its hard limits, the `DriftDetector` uses rolling statistics (like mean and z-score) to identify when a parameter is exhibiting abnormal behavior. It can flag a rising trend or a statistically significant shift even while the value is still technically "in-spec," providing an early warning.

2.  **LLM-Powered Planning**: Once a potential issue is detected, the system needs to decide on the best corrective action. This is a complex task with multiple variables. The LLM planner (`planner_gemini.py`) acts as an expert process engineer. It is given a detailed prompt containing:
    -   The specific issue that was detected.
    -   The recent history of all relevant process data.
    -   The current control settings ("knobs").
    -   The desired quality targets and operational safety constraints.

    The LLM uses this context to reason about the problem and generate a safe, incremental, and effective plan to nudge the process back to its optimal state. This plan is returned in a structured JSON format, allowing it to be automatically simulated and applied.

This combination creates a sophisticated system that is not just reactive, but **proactive**, aiming to maintain stability and prevent quality issues before they happen.

## Key Components

1.  **Plant Simulator (`qc/simulator.py`)**
    -   The `PlantSim` class runs a continuous simulation, generating new data points for quality parameters like `LSF_est`, `Blaine_est`, and `fCaO_est` at regular intervals.
    -   It can have **disturbances** injected via the API (e.g., a sudden change in raw material quality) to test the resilience and responsiveness of the control system.

2.  **Drift Detector (`qc/detector.py`)**
    -   The `DriftDetector` class consumes the data stream from the simulator.
    -   It maintains a rolling window of recent statistics for key parameters.
    -   The `maybe_issue` method uses a combination of z-score analysis and target-band checks to determine if the process is drifting. If it is, it formulates a detailed description of the issue to be passed to the planner.

3.  **AI Planner (`qc/planner_gemini.py`)**
    -   This module is responsible for generating corrective action plans.
    -   The `propose_plan` function constructs a detailed prompt and sends it to the Gemini API.
    -   It includes robust error handling to manage potential API or parsing failures.
    -   It parses the AI's JSON response into a structured `Plan` object.

4.  **Action and Safety Modules (`qc/actions.py`, `qc/safety.py`)**
    -   `actions.py`: Contains logic to simulate the future state of the plant based on a proposed plan (`simulate_after`).
    -   `safety.py`: The `clamp_actions` function acts as a safety layer, ensuring that any plan proposed by the AI does not violate predefined operational constraints (e.g., changing a raw mix percentage by too much in one step).

5.  **API Server (`app.py`)**
    -   A FastAPI server that exposes the QC system's functionality. Key endpoints include:
        -   `GET /state/series`: Provides time-series data for the frontend chart.
        -   `POST /disturb`: Allows for injecting disturbances into the simulation for demo purposes.
        -   `POST /plan/propose`: Triggers the AI planner to generate a corrective plan.
        -   `POST /plan/simulate`: Simulates the effect of a proposed plan.
        -   `POST /plan/apply`: Applies the proposed plan to the plant simulator's controls.

## How to Run the Project

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set API Key**:
    -   Copy the `.env.example` file to a new file named `.env`.
    -   Add your Google Gemini API key to the `GEMINI_API_KEY` variable in the `.env` file.

3.  **Run the Server**:
    ```bash
    uvicorn app:app --host 0.0.0.0 --port 8002
    ```
    This will start the API server and the background simulation on `http://localhost:8002`.

## Conclusion

This project provides a comprehensive framework for a proactive, AI-assisted quality control system. By combining real-time data analysis, statistical drift detection, and the advanced reasoning capabilities of LLMs, it demonstrates a powerful tool for maintaining process stability and ensuring consistent product quality in a complex manufacturing environment.
