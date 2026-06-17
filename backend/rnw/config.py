from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
INSTANCE_DIR = BASE_DIR / "instance"
DEFAULT_DB = f"sqlite:///{INSTANCE_DIR / 'rnw.sqlite3'}"


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _database_uri() -> str:
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Render sometimes gives postgres://, but SQLAlchemy needs postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)

        return database_url

    # Local development fallback only
    env_name = os.getenv("FLASK_CONFIG", os.getenv("FLASK_ENV", "development")).lower()

    if env_name in {"production", "prod"}:
        raise RuntimeError(
            "DATABASE_URL is required in production. "
            "Add DATABASE_URL in Render Environment Variables."
        )

    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DB


class BaseConfig:
    APP_NAME = os.getenv("APP_NAME", "RNW")
    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_TIME_LIMIT = 3600
    EMAIL_VERIFICATION_REQUIRED = _bool("EMAIL_VERIFICATION_REQUIRED", False)

    MAIL_SERVER = os.getenv("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "25"))
    MAIL_USE_TLS = _bool("MAIL_USE_TLS", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@rnw.local")

    CACHE_TYPE = os.getenv("CACHE_TYPE", "SimpleCache")
    CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT = 300

    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True

    UPLOAD_FOLDER_PATH = Path(os.getenv("UPLOAD_FOLDER", str(INSTANCE_DIR / "uploads")))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "16")) * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", str(INSTANCE_DIR / "logs" / "rnw.log"))

    PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "disabled")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    PAYFAST_MERCHANT_ID = os.getenv("PAYFAST_MERCHANT_ID")
    PAYFAST_MERCHANT_KEY = os.getenv("PAYFAST_MERCHANT_KEY")
    PAYFAST_PASSPHRASE = os.getenv("PAYFAST_PASSPHRASE")
    PAYFAST_SANDBOX = _bool("PAYFAST_SANDBOX", True)


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    RATELIMIT_ENABLED = False
    EMAIL_VERIFICATION_REQUIRED = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}
