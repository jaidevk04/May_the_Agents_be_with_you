import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib
import os

def train_and_save_models():
    """
    Trains the KPI models based on synthetic data and saves them to disk.
    """
    DATA_PATH = 'synthetic_plant_data.csv'
    MODELS_DIR = 'models'

    if not os.path.exists(DATA_PATH):
        print(f"Error: Synthetic data file '{DATA_PATH}' not found.")
        print("Please run 'python scripts/generate_synthetic_data.py' first.")
        return

    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
        print(f"Created directory: {MODELS_DIR}")

    df = pd.read_csv(DATA_PATH)

    # --- LSF Model ---
    print("Training LSF model...")
    lsf_model = LinearRegression()
    lsf_features = df[['CaO_in', 'SiO2_in']]
    lsf_target = df['LSF_est']
    lsf_model.fit(lsf_features, lsf_target)
    joblib.dump(lsf_model, os.path.join(MODELS_DIR, 'lsf_model.joblib'))
    print("LSF model saved to models/lsf_model.joblib")

    # --- Blaine Model ---
    print("Training Blaine model...")
    blaine_model = LinearRegression()
    blaine_features = df[['Separator', 'Gypsum', 'Moisture']]
    blaine_target = df['Blaine_est']
    blaine_model.fit(blaine_features, blaine_target)
    joblib.dump(blaine_model, os.path.join(MODELS_DIR, 'blaine_model.joblib'))
    print("Blaine model saved to models/blaine_model.joblib")

if __name__ == "__main__":
    train_and_save_models()
