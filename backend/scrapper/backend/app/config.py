import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
