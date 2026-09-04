import json
from pathlib import Path
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "AI-Powered Safety Intelligence & Early Warning System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PORT: int = 8000

    # JWT Authentication
    JWT_SECRET_KEY: str = "development-only-change-this-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # CORS configuration
    FRONTEND_URL: Union[str, None] = None
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v_str = v.strip()
            if v_str.startswith("[") and v_str.endswith("]"):
                try:
                    parsed = json.loads(v_str)
                    if isinstance(parsed, list):
                        return [str(i).strip() for i in parsed if str(i).strip()]
                except Exception:
                    pass
            return [i.strip() for i in v_str.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    @property
    def cors_origins(self) -> List[str]:
        origins = list(self.BACKEND_CORS_ORIGINS) if isinstance(self.BACKEND_CORS_ORIGINS, list) else []
        if self.FRONTEND_URL:
            clean_url = self.FRONTEND_URL.strip()
            clean_no_slash = clean_url.rstrip("/")
            if clean_no_slash and clean_no_slash not in origins:
                origins.append(clean_no_slash)
            if clean_url and clean_url not in origins:
                origins.append(clean_url)
        if self.ENVIRONMENT.lower() == "development":
            dev_origins = [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ]
            for dev_orig in dev_origins:
                if dev_orig not in origins:
                    origins.append(dev_orig)
        # Filter out "*" or empty strings to prevent CORS credential errors
        return [o for o in origins if o and o != "*"]

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.ENVIRONMENT.lower() == "production":
            if len(self.JWT_SECRET_KEY) < 32 or self.JWT_SECRET_KEY == "development-only-change-this-secret":
                raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters in production")
            if self.USE_SQLITE_DEV_FALLBACK:
                raise ValueError("USE_SQLITE_DEV_FALLBACK must be false in production")
            if not self.DATABASE_URL and self.POSTGRES_SERVER == "localhost":
                raise ValueError("Configure DATABASE_URL or POSTGRES_SERVER for production")
        return self

    # Database configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "safety_intelligence_db"
    DATABASE_URL: Union[str, None] = None
    USE_SQLITE_DEV_FALLBACK: bool = True
    SEED_DEMO_DATA: bool = True

    # Bulk Safety Report Import configuration
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_IMPORT_EXTENSIONS: List[str] = [".xlsx", ".csv", ".pdf"]
    ENABLE_OCR: bool = True
    TESSERACT_CMD: Union[str, None] = None

    @property
    def sync_database_url(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL.strip()
            # Standardize PostgreSQL URL dialect for SQLAlchemy + psycopg2
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg2://", 1)
            elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()

