from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database — can be set as a full URL or as individual components
    # Individual components take priority when DB_PASSWORD is provided
    # (avoids @ in password breaking URL parsing)
    database_url: str = "postgresql+asyncpg://appuser:changeme@localhost/appointment_agent"
    db_host: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: Optional[str] = None

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

    def get_database_url(self):
        """Return a SQLAlchemy URL object or string for the database connection.

        When DB_* components are provided, returns a URL object so that
        SQLAlchemy passes the password directly to asyncpg without string
        serialisation (str(URL) hides the password as *** in SQLAlchemy 2.x).
        """
        if self.db_host and self.db_user and self.db_password and self.db_name:
            from sqlalchemy.engine.url import URL
            return URL.create(
                drivername="postgresql+asyncpg",
                username=self.db_user,
                password=self.db_password,  # passed as-is; no percent-encoding issues
                host=self.db_host,
                database=self.db_name,
            )
        return self.database_url


settings = Settings()
