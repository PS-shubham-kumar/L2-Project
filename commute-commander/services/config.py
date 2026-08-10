import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "")
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY", "")
    OPENROUTESERVICE_API_KEY = os.getenv("OPENROUTESERVICE_API_KEY", "")
