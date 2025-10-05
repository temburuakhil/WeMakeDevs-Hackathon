import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Multimodal RAG System"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API Keys
    cerebras_api_key: Optional[str] = None
    
    # File Storage
    upload_dir: Path = Path("uploads")
    data_dir: Path = Path("data")
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Vector Database
    vector_db_path: str = "./data/chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Audio Processing
    whisper_model: str = "base"
    
    # Image Processing
    clip_model: str = "ViT-B/32"
    
    # RAG Configuration
    llama_model: str = "meta-llama/Llama-2-7b-chat-hf"
    max_context_length: int = 4096
    max_retrieved_docs: int = 5
    
    # Citation Configuration
    citation_format: str = "numbered"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(exist_ok=True)
settings.data_dir.mkdir(exist_ok=True)