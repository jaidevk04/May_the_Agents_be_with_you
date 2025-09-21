from typing import Dict
from .kpi_model import compute_lsf, compute_blaine, compute_fcao
from .config import settings

def simulate_after(sample_now: Dict, actions):
    # clone and apply rough effects (same as PlantSim side-effects)
    SiO2 = sample_now["SiO2_in"]
    CaO  = sample_now["CaO_in"]
    Moist = sample_now["Moisture"]
    Sep = sample_now["Separator"]
    Gyp = sample_now["Gypsum"]

    for a in actions:
        if a.knob == "sand_pct":
            SiO2 += -0.4 * a.delta_pct
        elif a.knob == "limestone_pct":
            CaO  +=  0.4 * a.delta_pct
            SiO2 += -0.2 * a.delta_pct
        elif a.knob == "clay_pct":
            SiO2 += -0.1 * a.delta_pct
        elif a.knob == "separator_speed":
            Sep += a.delta_pct
        elif a.knob == "gypsum_pct":
            Gyp += a.delta_pct

    LSF = compute_lsf(CaO, SiO2)
    Blaine = compute_blaine(Sep, Gyp, Moist)
    fCaO = compute_fcao(LSF, settings.LSF_MIN, settings.LSF_MAX)
    return {"LSF_est": LSF, "Blaine_est": Blaine, "fCaO_est": fCaO}
