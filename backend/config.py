"""
Configuration settings for the Automated Insight Engine
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Get the directory where config.py is located
BASE_DIR = Path(__file__).resolve().parent


class Settings:
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/insights.db")
    
    # Folders - use absolute paths
    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    OUTPUT_FOLDER: str = os.getenv("OUTPUT_FOLDER", str(BASE_DIR / "reports"))
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()
