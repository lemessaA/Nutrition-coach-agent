import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote_plus, urlunparse

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of `backend/`
_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT / ".env"

# Load so non-Pydantic code and libraries see the same values as `Settings`
load_dotenv(_ENV_FILE)
# Also load ``backend/.env`` when present (repo root is canonical; this fills gaps for local dev).
load_dotenv(Path(__file__).resolve().parent / ".env", override=False)


def _default_sqlite_url() -> str:
    p = (Path(__file__).resolve().parent / "nutrition_coach.db").resolve()
    return f"sqlite:///{p.as_posix()}"


def _normalize_postgres_url(url: str) -> str:
    """SQLAlchemy expects ``postgresql://``; some hosts emit ``postgres://``."""
    u = url.strip()
    if u.startswith("postgres://"):
        u = "postgresql://" + u[len("postgres://") :]
    return u


def _env_flag(name: str) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _resolve_database_url() -> str:
    """
    Order: ``USE_SQLITE`` → SQLite; ``DATABASE_URL``; ``POSTGRES_*`` composite URL;
    else SQLite in ``backend/``.

    If you have ``POSTGRES_*`` in ``.env`` but no server on that host (e.g. Postgres
    not started locally), set ``USE_SQLITE=1`` or comment those vars, or use Docker
    to run Postgres.
    """
    if _env_flag("USE_SQLITE"):
        return _default_sqlite_url()
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if raw:
        if raw.startswith("sqlite"):
            return raw
        return _normalize_postgres_url(raw)
    user = (os.environ.get("POSTGRES_USER") or "").strip()
    password = os.environ.get("POSTGRES_PASSWORD")
    host = (os.environ.get("POSTGRES_HOST") or "localhost").strip() or "localhost"
    port = (os.environ.get("POSTGRES_PORT") or "5432").strip() or "5432"
    db = (os.environ.get("POSTGRES_DB") or "").strip()
    if user and password is not None and db:
        auth = f"{user}:{quote_plus(str(password))}"
        netloc = f"{auth}@{host}:{port}"
        return urlunparse(("postgresql", netloc, f"/{db}", "", "", ""))
    return _default_sqlite_url()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Set DATABASE_URL, or set POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB (and
    # optionally POSTGRES_HOST, POSTGRES_PORT). Default is a local SQLite file in backend/.
    database_url: str = Field(default_factory=_resolve_database_url)

    # LLM Configuration
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    llm_provider: str = "groq"  # openai, groq
    llm_model: str = "llama-3.1-8b-instant"

    # Vector Database
    vector_db_type: str = "faiss"  # faiss, chroma
    vector_db_path: str = "./data/vector_db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True
    # Comma-separated browser origins allowed to call the API (CORS).
    # Example: "http://localhost:3000,http://127.0.0.1:3000,https://your-app.vercel.app"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Security (set SECRET_KEY in .env in production)
    secret_key: str = "dev-insecure-set-secret-key-in-env"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # External food / nutrition provider APIs
    usda_api_key: Optional[str] = None
    nutritionix_app_id: Optional[str] = None
    nutritionix_api_key: Optional[str] = None
    edamam_app_id: Optional[str] = None
    edamam_api_key: Optional[str] = None
    spoonacular_api_key: Optional[str] = None
    openfoodfacts_enabled: bool = True


settings = Settings()
