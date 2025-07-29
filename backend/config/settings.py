from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App
    app_name: str = "AI Operations Agent"
    debug: bool = True
    environment: str = "development"
    
    # Database
    database_url: str = "sqlite:///./ai_operations.db"
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_name: Optional[str] = None
    
    # LLM Configuration
    llm_provider: str = "groq"  # "openai" or "groq"
    openai_api_key: Optional[str] = None
    groq_api_key: str
    groq_model: str = "llama-3.1-70b-versatile"  # Fast and capable model
    
    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str = "company-operations"
    
    # SendGrid
    sendgrid_api_key: str
    sendgrid_from_email: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Google Calendar (optional)
    google_calendar_credentials_file: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()