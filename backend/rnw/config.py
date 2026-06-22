from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = Path(os.getenv("UPLOAD_FOLDER_PATH", str(BASE_DIR / "uploads")))


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-before-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-jwt-before-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", f"sqlite:///{INSTANCE_DIR / 'rnw_dev.sqlite3'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    PREFERRED_URL_SCHEME = "https" if APP_BASE_URL.startswith("https") else "http"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600

    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "1025"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@roomnearwork.local")

    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "redis://localhost:6379/1")

    # Google Maps Platform: Geocoding API + Routes API Compute Route Matrix.
    # If blank, RNW falls back to local demo coordinates so development still works.
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
    GOOGLE_MAPS_BROWSER_KEY = os.getenv("GOOGLE_MAPS_BROWSER_KEY", "")
    GOOGLE_MAPS_REGION = os.getenv("GOOGLE_MAPS_REGION", "ZA")
    GOOGLE_MAPS_LANGUAGE = os.getenv("GOOGLE_MAPS_LANGUAGE", "en-ZA")
    GOOGLE_ROUTE_MATRIX_ENABLED = env_bool("GOOGLE_ROUTE_MATRIX_ENABLED", True)
    DEFAULT_SEARCH_RADIUS_KM = float(os.getenv("DEFAULT_SEARCH_RADIUS_KM", "20"))
    DEFAULT_MAX_TRAVEL_MINUTES = int(os.getenv("DEFAULT_MAX_TRAVEL_MINUTES", "45"))

    PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "disabled")
    PAYFAST_SANDBOX = env_bool("PAYFAST_SANDBOX", True)
    PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID", "")
    PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY", "")
    PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE", "")

    TENANT_MONTHLY_PRICE = int(os.getenv("TENANT_MONTHLY_PRICE", "50"))
    LANDLORD_MONTHLY_PRICE = int(os.getenv("LANDLORD_MONTHLY_PRICE", "100"))
    LANDLORD_MAX_LISTINGS = int(os.getenv("LANDLORD_MAX_LISTINGS", "25"))
    SUBSCRIPTION_CURRENCY = os.getenv("SUBSCRIPTION_CURRENCY", "ZAR")

    EMAIL_VERIFICATION_REQUIRED = env_bool("EMAIL_VERIFICATION_REQUIRED", False)
    ADMIN_2FA_REQUIRED = env_bool("ADMIN_2FA_REQUIRED", False)
    LISTING_EXPIRES_DAYS = int(os.getenv("LISTING_EXPIRES_DAYS", "30"))
    SAVED_SEARCH_ALERTS_ENABLED = env_bool("SAVED_SEARCH_ALERTS_ENABLED", True)
    RUN_JOBS_INLINE = env_bool("RUN_JOBS_INLINE", True)

    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "12")) * 1024 * 1024
    UPLOAD_FOLDER_PATH = Path(os.getenv("UPLOAD_FOLDER_PATH", str(UPLOAD_DIR)))
    LOG_FILE = os.getenv("LOG_FILE", str(INSTANCE_DIR / "rnw.log"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    PROXY_FIX_ENABLED = env_bool("PROXY_FIX_ENABLED", False)
    PROXY_FIX_X_FOR = int(os.getenv("PROXY_FIX_X_FOR", "1"))
    PROXY_FIX_X_PROTO = int(os.getenv("PROXY_FIX_X_PROTO", "1"))
    PROXY_FIX_X_HOST = int(os.getenv("PROXY_FIX_X_HOST", "1"))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    LOG_FILE = None


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "default": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
