from pydantic import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Application Configuration
    APP_NAME: str = "AutoMailHelpdesk"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str
    
    # Database Configuration
    DATABASE_URL: str
    REDIS_URL: str
    
    # Gmail API Configuration
    GMAIL_CLIENT_ID: str
    GMAIL_CLIENT_SECRET: str
    GMAIL_REFRESH_TOKEN: str
    GMAIL_ACCESS_TOKEN: str
    
    # Odoo Configuration
    ODOO_URL: str
    ODOO_DATABASE: str
    ODOO_USERNAME: str
    ODOO_PASSWORD: str
    
    # Google AI Configuration
    GOOGLE_API_KEY: str
    GOOGLE_PROJECT_ID: str
    
    # Langchain Configuration
    LANGCHAIN_TRACING_V2: bool = True
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str = "AutoMailHelpdesk"
    
    # ChromaDB Configuration
    CHROMADB_HOST: str = "localhost"
    CHROMADB_PORT: int = 8000
    CHROMADB_COLLECTION_NAME: str = "helpdesk_knowledge"
    
    # Monitoring Configuration
    SENTRY_DSN: Optional[str] = None
    DATADOG_API_KEY: Optional[str] = None
    
    # Slack Configuration
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_CHANNEL: str = "#support"
    
    # Processing Configuration
    EMAIL_POLL_INTERVAL: int = 300  # seconds
    MAX_RETRIES: int = 3
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    
    # Security
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    GMAIL_API_RATE_LIMIT: int = 250  # requests per 100 seconds
    GEMINI_API_RATE_LIMIT: int = 60  # requests per minute
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

