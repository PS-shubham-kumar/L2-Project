import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve .env relative to this file — works regardless of CWD
# src/services/config.py → src/ → project root → .env
_ENV_PATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH)


class Config:
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "")
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
    OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")
