from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database - Railway provides DATABASE_URL automatically
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/sales_insights")
    
    # Redis - Railway provides REDIS_URL automatically
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    celery_broker_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # OpenAI - You must set this in Railway dashboard
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # LLM Configuration
    default_llm_model: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
    
    # Optional
    assemblyai_api_key: Optional[str] = os.getenv("ASSEMBLYAI_API_KEY", None)
    
    # Application
    max_transcript_length: int = int(os.getenv("MAX_TRANSCRIPT_LENGTH", "50000"))
    processing_timeout_seconds: int = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "120"))
    
    # Security - You must set SECRET_KEY in Railway dashboard (generate with: openssl rand -hex 32)
    secret_key: str = os.getenv("SECRET_KEY", "change-this-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Rate limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Pricing tiers
    professional_monthly_limit: int = int(os.getenv("PROFESSIONAL_MONTHLY_LIMIT", "100"))
    business_monthly_limit: int = int(os.getenv("BUSINESS_MONTHLY_LIMIT", "500"))
    
    # CORS - For production, restrict this
    cors_origins: list = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
