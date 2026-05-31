from pydantic_settings import BaseSettings
import os
import secrets


class Settings(BaseSettings):
    # Provided by the platform (Render Postgres). Local dev falls back to SQLite
    # via backend/database.py if DATABASE_URL is unset.
    DATABASE_URL: str = "sqlite:///pa_fabs.db"

    # SECRET_KEY must come from the environment in any deployed env. We generate
    # an ephemeral one only as a local-dev fallback (tokens won't survive a
    # restart, which is fine for dev and safe by default).
    SECRET_KEY: str = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Comma-separated list of allowed CORS origins (the deployed frontend URL).
    # "*" is allowed for local dev only.
    ALLOWED_ORIGINS: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        raw = self.ALLOWED_ORIGINS.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
