import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./nutrition_coach.db"
    
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
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External APIs
    usda_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"


settings = Settings()