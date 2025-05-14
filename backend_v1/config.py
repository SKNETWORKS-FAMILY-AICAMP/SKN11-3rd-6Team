import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Ready-To-Go Travel Assistant"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "../data/vectors")
    
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Google
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # LLM
    DEFAULT_LLM_MODEL: str = "gpt-4"
    MAX_CONTEXT_TOKENS: int = 3000
    TOP_K_RESULTS: int = 5
    
    # Document Processing
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    class Config:
        env_file = ".env"

settings = Settings()