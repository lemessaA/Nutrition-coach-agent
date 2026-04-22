from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of `backend/`
_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _ROOT / ".env"

# Load so non-Pydantic code and libraries see the same values as `Settings`
load_dotenv(_ENV_FILE)


def _default_sqlite_url() -> str:
    p = (Path(__file__).resolve().parent / "nutrition_coach.db").resolve()
    return f"sqlite:///{p.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Set DATABASE_URL in .env for Postgres. Default is a local SQLite file in backend/.
    database_url: str = Field(default_factory=_default_sqlite_url)
    
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