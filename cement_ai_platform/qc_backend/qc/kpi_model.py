import pandas as pd
import joblib
import os
from .config import settings

# --- Load Pre-trained Models ---
# This part runs once when the module is loaded to load the pre-trained models.

lsf_model = None
blaine_model = None

if os.path.exists(settings.LSF_MODEL_PATH):
    lsf_model = joblib.load(settings.LSF_MODEL_PATH)
    print(f"LSF model loaded from {settings.LSF_MODEL_PATH}")
else:
    print(f"WARNING: LSF model not found at {settings.LSF_MODEL_PATH}. Please run 'python scripts/train_models.py'.")

if os.path.exists(settings.BLAINE_MODEL_PATH):
    blaine_model = joblib.load(settings.BLAINE_MODEL_PATH)
    print(f"Blaine model loaded from {settings.BLAINE_MODEL_PATH}")
else:
    print(f"WARNING: Blaine model not found at {settings.BLAINE_MODEL_PATH}. Please run 'python scripts/train_models.py'.")

def compute_lsf(cao: float, sio2: float) -> float:
    if lsf_model:
        input_df = pd.DataFrame([[cao, sio2]], columns=['CaO_in', 'SiO2_in'])
        return float(lsf_model.predict(input_df)[0])
    else:
        # Fallback to a simple formula if model is not loaded
        return 100.0 + 2.2 * (cao - 43.0) - 1.8 * (sio2 - 14.0)

def compute_blaine(separator: float, gypsum_pct: float, moisture: float) -> float:
    if blaine_model:
        input_df = pd.DataFrame([[separator, gypsum_pct, moisture]], columns=['Separator', 'Gypsum', 'Moisture'])
        return float(blaine_model.predict(input_df)[0])
    else:
        # Fallback to a simple formula if model is not loaded
        return 340.0 + 2.0 * (separator - 120.0) + 8.0 * (gypsum_pct - 3.0) - 4.0 * (moisture - 1.5)

def compute_fcao(lsf: float, lsf_min: float, lsf_max: float) -> float:
    # Softer penalty: modest deviations give <1.0%; large deviations don't explode.
    if lsf < lsf_min:
        dev = (lsf_min - lsf)
    elif lsf > lsf_max:
        dev = (lsf - lsf_max)
    else:
        dev = 0.0
    return max(0.0, 0.25 * dev)

print("KPI models initialized (loading from disk if available).")
