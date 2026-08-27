"""
Application Configuration and Settings.
Supports environment variables and .env file overrides.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Financial Fraud Detection Platform"
    API_V1_STR: str = "/api/v1"
    
    # Database: SQLite by default (works out-of-the-box), easily switchable to MySQL
    # MySQL format: mysql+pymysql://<user>:<password>@<host>:<port>/<dbname>
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fraud_detection.db")

    # Artifact paths
    MODEL_PATH: str = os.getenv("MODEL_PATH", "ml/artifacts/best_model.joblib")
    METRICS_PATH: str = os.getenv("METRICS_PATH", "ml/artifacts/metrics.json")
    DATA_PATH: str = os.getenv("DATA_PATH", "data/raw/transactions.csv")

    # Risk Scoring Thresholds
    FLAG_THRESHOLD: float = float(os.getenv("FLAG_THRESHOLD", "0.30"))
    BLOCK_THRESHOLD: float = float(os.getenv("BLOCK_THRESHOLD", "0.75"))

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
