"""jea_meeting_web_scraper.config.settings

Centralized configuration loader for the entire FastAPI application.
Loads:
- Secrets and environment flags from `.env`
- Structured configuration from `config.yaml`
"""

from pathlib import Path
from typing import Optional
import yaml
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


# ------------------------------------------------------------
# Nested Configuration Models
# ------------------------------------------------------------


class AppSettings(BaseModel):
    name: str = "jea-meeting-web-scraper"
    debug: bool = False
    env: str = Field(default="development", description="dev, testing, production")
    log_level: str = Field(default="info")


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
# Database Settings
# ------------------------------------------------------------


class DatabaseSettings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "testdb"
    db_user: str = "testuser"
    db_password: str = "testpass"

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# ------------------------------------------------------------
# Root Settings (environment + YAML merge)
# ------------------------------------------------------------


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from env/yaml
    )
    
    # Secrets
    secret_key: str = "test_secret_key_for_development_min_32_chars"
    app_username: str = "testuser"
    app_password: str = "testpass"

    # Nested config loaded from YAML
    app: AppSettings = AppSettings()
    scraper: ScraperSettings = ScraperSettings(
        pdf_directory="./data/raw_pdfs",
        annotated_directory="./data/annotated_pdfs"
    )
    cookies: CookieSettings = CookieSettings()
    tasks: TaskSettings = TaskSettings()

    # Database
    database: DatabaseSettings = DatabaseSettings()

    # Validators
    @field_validator("secret_key")
    @classmethod
    def validate_secret(cls, v: str):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        return v


# ------------------------------------------------------------
# Loader
# ------------------------------------------------------------


def load_settings() -> Settings:
    yaml_path = Path(__file__).parent / "config.yaml"

    # Load YAML if exists, otherwise use defaults
    yaml_data = {}
    if yaml_path.exists():
        with yaml_path.open("r") as f:
            yaml_data = yaml.safe_load(f) or {}

    # Create Settings obj by merging YAML + `.env`
    return Settings(**yaml_data)


settings = load_settings()
