"""
Application Configuration
Loads environment variables and provides app-wide settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    HOW IT WORKS (for beginners):
    - Pydantic reads values from .env file or actual environment variables
    - If a value is missing and has no default, the app won't start (good! catches config errors early)
    - @lru_cache means the settings object is created once and reused (performance optimization)
    """

    # ── App Settings ──────────────────────────────────────────
    APP_NAME: str = "Smart Baby Band API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Firebase ──────────────────────────────────────────────
    # Path to your Firebase service account JSON key file
    FIREBASE_SERVICE_ACCOUNT_PATH: str = "firebase-service-account.json"
    FIREBASE_RTDB_URL: str = "https://smart-baby-band-default-rtdb.firebaseio.com"

    # ── CORS (Cross-Origin Resource Sharing) ──────────────────
    # Which domains are allowed to call your API
    # "*" means everyone (fine for development, restrict in production)
    CORS_ORIGINS: list[str] = ["*"]

    # ── Server ────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── ML Model ──────────────────────────────────────────────
    CRY_MODEL_PATH: str = "ml_models/cry_detection_model.tflite"
    KERAS_MODEL_PATH: str = "../ml_model/cry_classification/models/best_model.keras"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """
    Returns the cached Settings instance.
    Usage: settings = get_settings()
    """
    return Settings()
