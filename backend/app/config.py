from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://appuser:changeme@localhost/appointment_agent"
    secret_key: str = "change-me-in-production"
    encryption_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 30  # 30 days

    # Default LLM config seeded on first run
    github_token: Optional[str] = None
    first_user: str = "admin"
    first_password: str = "changeme"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
