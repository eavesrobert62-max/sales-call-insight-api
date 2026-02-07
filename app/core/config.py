from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    
    # OpenAI
    openai_api_key: str
    default_llm_model: str = "gpt-4o-mini"
    
    # Optional
    assemblyai_api_key: Optional[str] = None
    
    # Application
    max_transcript_length: int = 50000
    processing_timeout_seconds: int = 120
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    
    # Pricing tiers
    professional_monthly_limit: int = 100
    business_monthly_limit: int = 500
    
    class Config:
        env_file = ".env"


settings = Settings()
