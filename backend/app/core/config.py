from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str

    # Google Cloud Storage
    gcs_bucket_name: Optional[str] = None  # not required when use_local_storage=true

    # Local storage (dev only) — set USE_LOCAL_STORAGE=true to skip GCS entirely
    use_local_storage: bool = False

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # Cookie — set COOKIE_SECURE=true in production (HTTPS only)
    cookie_secure: bool = False

    # CORS
    cors_origin: str

    # Admin
    admin_api_key: Optional[str] = None  # if unset, POST /templates is disabled

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
