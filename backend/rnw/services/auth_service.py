from __future__ import annotations

import hashlib
import secrets
import string
from datetime import datetime, timedelta

from flask import current_app

from ..extensions import db
from ..models import AuthToken, LoginAttempt, User
from .email_service import send_email


TOKEN_PURPOSE_EMAIL_VERIFY = "email_verify"
TOKEN_PURPOSE_PASSWORD_RESET = "password_reset"


def password_strength_errors(password: str) -> list[str]:
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(ch.isupper() for ch in password):
        errors.append("Password must include an uppercase letter.")
    if not any(ch.islower() for ch in password):
        errors.append("Password must include a lowercase letter.")
    if not any(ch.isdigit() for ch in password):
        errors.append("Password must include a number.")
    if not any(ch in string.punctuation for ch in password):
        errors.append("Password must include a symbol, for example ! or @.")
    return errors


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_auth_token(user: User, purpose: str, minutes: int = 60) -> str:
    raw = secrets.token_urlsafe(32)
    token = AuthToken(
        user_id=user.id,
        purpose=purpose,
        token_hash=_hash_token(raw),
        expires_at=datetime.utcnow() + timedelta(minutes=minutes),
    )
    db.session.add(token)
    return raw


def consume_auth_token(raw_token: str, purpose: str) -> User | None:
    if not raw_token:
        return None
    token = AuthToken.query.filter_by(token_hash=_hash_token(raw_token), purpose=purpose).first()
    if not token or not token.is_valid:
        return None
    token.consume()
    return token.user


def record_login_attempt(email: str, ip_address: str | None, success: bool) -> None:
    db.session.add(LoginAttempt(email=(email or "").lower(), ip_address=ip_address, success=success))


def is_login_locked(email: str, ip_address: str | None, limit: int = 5, window_minutes: int = 15) -> bool:
    since = datetime.utcnow() - timedelta(minutes=window_minutes)
    query = LoginAttempt.query.filter(
        LoginAttempt.email == (email or "").lower(),
        LoginAttempt.success.is_(False),
        LoginAttempt.attempted_at >= since,
    )
    if ip_address:
        query = query.filter(LoginAttempt.ip_address == ip_address)
    return query.count() >= limit


def send_verification_email(user: User) -> None:
    token = create_auth_token(user, TOKEN_PURPOSE_EMAIL_VERIFY, minutes=60 * 24)
    base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000").rstrip("/")
    link = f"{base_url}/auth/verify-email/{token}"
    body = (
        f"Hi {user.first_name},\n\n"
        "Please verify your RNW email address by opening this link:\n"
        f"{link}\n\n"
        "This link expires in 24 hours."
    )
    send_email("Verify your RNW email", [user.email], body)


def send_password_reset_email(user: User) -> None:
    token = create_auth_token(user, TOKEN_PURPOSE_PASSWORD_RESET, minutes=60)
    base_url = current_app.config.get("APP_BASE_URL", "http://localhost:5000").rstrip("/")
    link = f"{base_url}/auth/reset-password/{token}"
    body = (
        f"Hi {user.first_name},\n\n"
        "Reset your RNW password using this link:\n"
        f"{link}\n\n"
        "This link expires in 1 hour. Ignore this email if you did not request it."
    )
    send_email("Reset your RNW password", [user.email], body)
