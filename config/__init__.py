import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")
    GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY")

    # Database configuration (PostgreSQL)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "postgres")
    DB_SCHEMA = os.getenv("DB_SCHEMA", "pixelweather")

    # Firebase
    FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "data/serviceAccountKey.json")

    # JWT Configuration
    JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", "7"))

    # Server configuration
    PORT = int(os.getenv("PORT", "5000"))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Application constants
    USERNAME_LENGTH = int(os.getenv("USERNAME_LENGTH", "50"))
    POST_ALERT_EXPIRY_WINDOW = int(os.getenv("POST_ALERT_EXPIRY_WINDOW", "30"))
    NOTIFICATION_ALERT_THRESHOLD = int(os.getenv("NOTIFICATION_ALERT_THRESHOLD", "3"))
