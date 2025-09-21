import asyncio, random
from typing import Dict
from .config import settings
from .kpi_model import compute_lsf, compute_blaine, compute_fcao
from .utils import utcnow
from .storage import add_sample, SampleORM, log_audit

class PlantSim:
    def __init__(self):
        # baseline raw inputs (arbitrary but stable)
        self.SiO2_in = 14.0
        self.CaO_in = 43.0
        self.Moisture = 1.5
        # controllable knobs (exposed to planner)
        self.limestone_pct = settings.limestone_pct
        self.sand_pct = settings.sand_pct
        self.clay_pct = settings.clay_pct
        self.separator_speed = settings.separator_speed
        self.gypsum_pct = settings.gypsum_pct
        # active disturbances
        self._disturb_timeleft = 0
        self._disturb = {"dSiO2": 0.0, "dCaO": 0.0, "dSep": 0.0}

    def apply_actions(self, actions):
        # apply small, safe steps (the safety module clamps these)
        for a in actions:
            if a.knob == "sand_pct":
                self.sand_pct += a.delta_pct
                # input side-effect
                self.SiO2_in += -0.4 * a.delta_pct  # reduce sand lowers SiO₂
            elif a.knob == "limestone_pct":
                self.limestone_pct += a.delta_pct
                self.CaO_in += 0.4 * a.delta_pct
                self.SiO2_in += -0.2 * a.delta_pct
            elif a.knob == "clay_pct":
                self.clay_pct += a.delta_pct
                self.SiO2_in += -0.1 * a.delta_pct
            elif a.knob == "separator_speed":
                self.separator_speed += a.delta_pct  # here delta_pct is used as absolute delta rpm
            elif a.knob == "gypsum_pct":
                self.gypsum_pct += a.delta_pct

            # keep rawmix sum ~ 100 by small proportional correction
        total = self.limestone_pct + self.sand_pct + self.clay_pct
        if abs(total - 100.0) > 0.01:
            # nudge clay to compensate
            self.clay_pct += (100.0 - total)

    def inject_disturbance(self, typ: str, mag: float, dur: int):
        if typ == "siO2_spike":
            self._disturb["dSiO2"] = +mag
        elif typ == "cao_drop":
            self._disturb["dCaO"] = -mag
        elif typ == "sep_low":
            self._disturb["dSep"] = -mag
        self._disturb_timeleft = max(self._disturb_timeleft, dur)

    def tick(self) -> Dict:
        # random noise
        self.SiO2_in += random.uniform(-0.05, 0.05)
        self.CaO_in += random.uniform(-0.05, 0.05)
        self.Moisture += random.uniform(-0.02, 0.02)
        self.separator_speed += random.uniform(-0.2, 0.2)
        self.gypsum_pct += random.uniform(-0.01, 0.01)

        # apply disturbance transiently
        if self._disturb_timeleft > 0:
            self.SiO2_in += self._disturb["dSiO2"]
            self.CaO_in += self._disturb["dCaO"]
            self.separator_speed += self._disturb["dSep"]
            self._disturb_timeleft -= 1
            if self._disturb_timeleft == 0:
                self._disturb = {"dSiO2": 0.0, "dCaO": 0.0, "dSep": 0.0}

        # soft clamps to keep ranges realistic
        self.SiO2_in = max(10.0, min(18.0, self.SiO2_in))
        self.CaO_in  = max(40.0, min(46.0, self.CaO_in))
        self.Moisture = max(0.5, min(3.0, self.Moisture))
        self.separator_speed = max(110.0, min(130.0, self.separator_speed))
        self.gypsum_pct = max(2.0, min(4.0, self.gypsum_pct))

        LSF = compute_lsf(self.CaO_in, self.SiO2_in)
        Blaine = compute_blaine(self.separator_speed, self.gypsum_pct, self.Moisture)
        fCaO = compute_fcao(LSF, settings.LSF_MIN, settings.LSF_MAX)

        # Calculate energy consumption (simple model)
        energy_consumption = (self.separator_speed * 0.1) + (self.gypsum_pct * 5) + (abs(self.SiO2_in - 14.0) * 2)

        return {
            "ts": utcnow(),
            "SiO2_in": self.SiO2_in,
            "CaO_in": self.CaO_in,
            "Moisture": self.Moisture,
            "Separator": self.separator_speed,
            "Gypsum": self.gypsum_pct,
            "LSF_est": LSF,
            "Blaine_est": Blaine,
            "fCaO_est": fCaO,
            "energy_consumption": energy_consumption,
        }

async def run_sim(engine, plant: PlantSim):
    while True:
        d = plant.tick()
        add_sample(engine, SampleORM(**d))
        await asyncio.sleep(settings.TICK_SECONDS)
