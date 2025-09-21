from .utils import RollingStats, utcnow
from .config import settings

# Simple mapping of causes → KPI direction
CAUSE_TO_KPI = {
    "SiO2_in_high": {"LSF":"down", "Blaine":"neutral", "fCaO":"up"},
    "CaO_in_low":   {"LSF":"down", "Blaine":"neutral", "fCaO":"up"},
    "Separator_low":{"LSF":"neutral","Blaine":"down",   "fCaO":"neutral"},
    "LSF_band_breach": {"LSF":"neutral","Blaine":"neutral","fCaO":"up"}, # Placeholder, adjusted in logic
    "Blaine_band_breach": {"LSF":"neutral","Blaine":"down","fCaO":"neutral"}, # Placeholder, adjusted in logic
}

Z_THRESH = 1.3

class DriftDetector:
    def __init__(self, win=600):
        self.rs = RollingStats(win, min_samples=10)

    def push(self, sample):
        for k in ["SiO2_in","CaO_in","Moisture","Separator","Gypsum","LSF_est","Blaine_est","fCaO_est"]:
            self.rs.push(k, sample[k])

    def maybe_issue(self):
        s_sio2 = self.rs.stats("SiO2_in")
        s_cao  = self.rs.stats("CaO_in")
        s_sep  = self.rs.stats("Separator")
        s_lsf  = self.rs.stats("LSF_est")
        s_bln  = self.rs.stats("Blaine_est")
        s_fcao = self.rs.stats("fCaO_est")

        drivers = []
        issue_text = None
        kpi_impact = {"LSF":"neutral","Blaine":"neutral","fCaO":"neutral"}

        # 1) z-score based (needs ~10 samples)
        if s_sio2 and s_sio2["z"] > Z_THRESH and s_sio2["last"] > s_sio2["mean"]:
            issue_text = "SiO₂ spike detected; expect LSF down and f-CaO up"
            drivers.append("SiO2_in_high")
            kpi_impact.update(CAUSE_TO_KPI["SiO2_in_high"])

        if s_cao and s_cao["z"] > Z_THRESH and s_cao["last"] < s_cao["mean"]:
            if not issue_text: issue_text = "CaO low drift detected; expect LSF down and f-CaO up"
            drivers.append("CaO_in_low")
            kpi_impact.update(CAUSE_TO_KPI["CaO_in_low"])

        if s_sep and s_sep["z"] > Z_THRESH and s_sep["last"] < s_sep["mean"]:
            if not issue_text: issue_text = "Separator speed low; expect Blaine down"
            drivers.append("Separator_low")
            kpi_impact.update(CAUSE_TO_KPI["Separator_low"])

        # 2) target-band breach fallback (works even with few samples)
        if s_lsf and (s_lsf["last"] < settings.LSF_MIN or s_lsf["last"] > settings.LSF_MAX):
            dirn = "low" if s_lsf["last"] < settings.LSF_MIN else "high"
            if not issue_text: issue_text = f"LSF {dirn} vs target band; adjust rawmix proportions"
            drivers.append("LSF_band_breach")
            impact_lsf = {"LSF":"neutral","Blaine":"neutral","fCaO":"up" if dirn=="low" else "neutral"}
            kpi_impact.update(impact_lsf)

        if s_bln and (s_bln["last"] < settings.BLAINE_MIN or s_bln["last"] > settings.BLAINE_MAX):
            dirn = "low" if s_bln["last"] < settings.BLAINE_MIN else "high"
            if not issue_text: issue_text = f"Blaine {dirn} vs target band; tune separator/gypsum"
            drivers.append("Blaine_band_breach")
            impact_blaine = {"LSF":"neutral","Blaine":"down" if dirn=="low" else "up","fCaO":"neutral"}
            kpi_impact.update(impact_blaine)

        # 3) fCaO high threshold (direct quality indicator)
        if s_fcao and s_fcao["last"] > settings.FCAO_MAX * 0.8: # 80% of max as a warning
            if not issue_text: issue_text = f"fCaO is high ({s_fcao['last']:.2f} > {settings.FCAO_MAX*0.8:.2f}); indicates LSF deviation"
            drivers.append("fCaO_high")
            kpi_impact.update({"fCaO":"up", "LSF":"neutral"}) # fCaO high implies LSF is off target

        if issue_text and drivers:
            return {"ts": utcnow(), "text": issue_text, "drivers": list(set(drivers)), "kpi_impact": kpi_impact}

        return None
