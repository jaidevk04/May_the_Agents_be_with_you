from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DB_PATH: str = Field(default="qc.db")
    LSF_MODEL_PATH: str = Field(default="models/lsf_model.joblib")
    BLAINE_MODEL_PATH: str = Field(default="models/blaine_model.joblib")
    TICK_SECONDS: float = 0.2 # Changed default to match .env.example
    WINDOW_SECONDS: int = 1800

    # targets
    LSF_MIN: float = 98.0
    LSF_MAX: float = 102.0
    BLAINE_MIN: float = 320.0
    BLAINE_MAX: float = 360.0
    FCAO_MAX: float = 1.0

    # ramp/guardrails
    RAMP_LIMIT_PCT: float = 0.5
    SEP_RAMP_LIMIT: float = 3.0
    GYPSUM_RAMP_LIMIT: float = 0.3

    # default knobs (raw mix composition + mill)
    limestone_pct: float = 83.0
    sand_pct: float = 4.0
    clay_pct: float = 13.0
    separator_speed: float = 120.0
    gypsum_pct: float = 3.0

    model_config = ConfigDict(env_file=".env") # Updated for Pydantic v2

settings = Settings()
