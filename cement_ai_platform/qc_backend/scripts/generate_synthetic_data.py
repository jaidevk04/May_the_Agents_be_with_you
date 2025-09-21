import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_synthetic_data(num_samples=1000):
    np.random.seed(42) # for reproducibility

    # Baselines (similar to kpi_model.py)
    CAO0 = 43.0
    SIO20 = 14.0
    SEP0 = 120.0
    GYP0 = 3.0
    MOIST0 = 1.5

    # Generate inputs with some realistic variation
    SiO2_in = np.random.normal(SIO20, 0.5, num_samples)
    CaO_in = np.random.normal(CAO0, 0.8, num_samples)
    Moisture = np.random.normal(MOIST0, 0.2, num_samples)
    Separator = np.random.normal(SEP0, 5.0, num_samples)
    Gypsum = np.random.normal(GYP0, 0.5, num_samples)

    # Ensure inputs stay within reasonable bounds
    SiO2_in = np.clip(SiO2_in, 12.0, 16.0)
    CaO_in = np.clip(CaO_in, 40.0, 46.0)
    Moisture = np.clip(Moisture, 1.0, 2.5)
    Separator = np.clip(Separator, 110.0, 130.0)
    Gypsum = np.clip(Gypsum, 2.0, 4.0)

    # Generate KPIs based on slightly more complex (but still linear) relationships
    # Add some noise to make it more realistic for training
    LSF_est = 100.0 + 2.5 * (CaO_in - CAO0) - 2.0 * (SiO2_in - SIO20) + np.random.normal(0, 0.5, num_samples)
    Blaine_est = 340.0 + 2.5 * (Separator - SEP0) + 10.0 * (Gypsum - GYP0) - 5.0 * (Moisture - MOIST0) + np.random.normal(0, 2.0, num_samples)

    # fCaO is typically a penalty for LSF deviation, so let's simulate that
    LSF_MIN = 98.0
    LSF_MAX = 102.0
    fCaO_est = np.zeros(num_samples)
    for i in range(num_samples):
        if LSF_est[i] < LSF_MIN:
            fCaO_est[i] = 0.3 * (LSF_MIN - LSF_est[i]) + np.random.normal(0, 0.1)
        elif LSF_est[i] > LSF_MAX:
            fCaO_est[i] = 0.3 * (LSF_est[i] - LSF_MAX) + np.random.normal(0, 0.1)
        fCaO_est[i] = max(0.0, fCaO_est[i]) # fCaO cannot be negative

    # Generate timestamps
    start_time = datetime.utcnow() - timedelta(seconds=num_samples)
    ts = [start_time + timedelta(seconds=i) for i in range(num_samples)]

    data = pd.DataFrame({
        'ts': ts,
        'SiO2_in': SiO2_in,
        'CaO_in': CaO_in,
        'Moisture': Moisture,
        'Separator': Separator,
        'Gypsum': Gypsum,
        'LSF_est': LSF_est,
        'Blaine_est': Blaine_est,
        'fCaO_est': fCaO_est
    })
    return data

if __name__ == "__main__":
    synthetic_data = generate_synthetic_data(num_samples=5000)
    synthetic_data.to_csv('synthetic_plant_data.csv', index=False)
    print("Generated synthetic_plant_data.csv with 5000 samples.")
