import os
from datetime import timedelta


class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT — store token in httpOnly cookie instead of localStorage
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = False          # Set True in production (HTTPS)
    JWT_COOKIE_HTTPONLY = True          # JS cannot read the cookie
    JWT_COOKIE_SAMESITE = "Lax"        # CSRF protection
    JWT_COOKIE_CSRF_PROTECT = False    # Disable double-submit CSRF for simplicity
    JWT_ACCESS_COOKIE_PATH = "/api"    # Cookie sent only to /api/* routes
