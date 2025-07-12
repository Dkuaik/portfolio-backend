from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Project info
    PROJECT_NAME: str = "Portfolio Backend API"
    VERSION: str = "1.0.0"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # CORS
    # ALLOWED_HOSTS: List[str] = []
    ALLOWED_ORIGINS: str = "*"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert comma-separated origins string to list"""
        if not self.ALLOWED_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # Security
    SECRET_KEY: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = None
    
    # OpenRouter settings
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash-lite-preview-06-17"
    OPENROUTER_MAX_TOKENS: int = 1000
    OPENROUTER_TEMPERATURE: float = 0.7
    
    # S3 settings
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "portfolio"
    PORTFOLIO_BUCKET_NAME: Optional[str] = None
    BUCKET_NAME: Optional[str] = None
    
    # Vector store settings
    VECTOR_STORE_DIR: str = "vectorstores/portfolio_index"
    HASH_FILE: str = "vectorstores/portfolio_hashes.json"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Search settings
    MAX_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7
    
    class Config:
        # Priority order: .env (local) -> .env.prod.dokploy (production)
        env_file = [".env"]
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # Allow extra fields

# Create settings instance
settings = Settings()
