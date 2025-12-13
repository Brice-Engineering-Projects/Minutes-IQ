"""jea_meeting_web_scraper.config.settings

Centralized configuration loader for the entire FastAPI application.
Loads:
- Secrets and environment flags from `.env`
- Structured configuration from `config.yaml`
"""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings

# ------------------------------------------------------------
# Nested Configuration Models
# ------------------------------------------------------------


class AppSettings(BaseModel):
    name: str = "jea-meeting-web-scraper"
    debug: bool = False
    env: str = Field(
        default="development", description="development | staging | production"
    )
    log_level: str = "info"


class ScraperSettings(BaseModel):
    pdf_directory: str
    annotated_directory: str
    processed_directory: Optional[str] = "./data/processed"
    concurrency: int = 2
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (compatible; JEAScraper/1.0; +https://internal-app)"


class CookieSettings(BaseModel):
    secure: bool = True
    samesite: str = "strict"
    max_age_minutes: int = 30


class TaskSettings(BaseModel):
    allow_background_tasks: bool = True
    workers: int = 2


# ------------------------------------------------------------
# Download / Export Settings
# ------------------------------------------------------------


class DownloadSettings(BaseModel):
    export_directory: str = "./data/exports"
    zip_directory: str = "./data/zipped"
    zip_filename_pattern: str = "jea_results_{date}.zip"
    include_raw_pdfs: bool = True
    include_annotated_pdfs: bool = True


# ------------------------------------------------------------
# Feature Flags
# ------------------------------------------------------------


class FeatureSettings(BaseModel):
    enable_zip_downloads: bool = True
    enable_keyword_management: bool = True
    enable_client_selection: bool = True
    enable_profile_customization: bool = True


# ------------------------------------------------------------
# Turso Database Settings
# ------------------------------------------------------------


class DatabaseSettings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    provider: str = "turso"  # future-proofing: could be sqlite or postgres later
    db_url: Optional[str] = None  # TURSO_DATABASE_URL (env)
    auth_token: Optional[str] = None  # TURSO_AUTH_TOKEN (env)
    replica_url: Optional[str] = None  # TURSO_REPLICA_URL (optional)

    @field_validator("db_url")
    @classmethod
    def validate_db_url(cls, v):
        if v is None:
            raise ValueError("TURSO_DATABASE_URL must be set in .env")
        return v


# ------------------------------------------------------------
# Root Settings (YAML + ENV merged)
# ------------------------------------------------------------


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Secrets
    secret_key: str = "test_secret_key_for_development_min_32_chars"
    app_username: str = "testuser"
    app_password: str = "testpass"

    # Nested config (YAML-loaded)
    app: AppSettings = AppSettings()
    scraper: ScraperSettings
    cookies: CookieSettings = CookieSettings()
    tasks: TaskSettings = TaskSettings()
    downloads: DownloadSettings = DownloadSettings()
    features: FeatureSettings = FeatureSettings()

    # Database (env-loaded overrides YAML if present)
    database: DatabaseSettings = DatabaseSettings()

    @field_validator("secret_key")
    @classmethod
    def validate_secret(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        return v


# ------------------------------------------------------------
# Loader
# ------------------------------------------------------------


def load_settings() -> Settings:
    yaml_path = Path(__file__).parent / "config.yaml"

    yaml_data = {}
    if yaml_path.exists():
        with yaml_path.open("r") as f:
            yaml_data = yaml.safe_load(f) or {}

    return Settings(**yaml_data)


settings = load_settings()
