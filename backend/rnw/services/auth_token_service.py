from __future__ import annotations

from datetime import datetime

from flask import url_for

from backend.rnw.extensions import db
from backend.rnw.models import EmailVerificationToken, PasswordResetToken, User
from backend.rnw.models.marketplace import hash_token
from backend.rnw.services.email_service import send_email


def send_verification_email(user: User) -> str:
    token, raw = EmailVerificationToken.issue(user.id)
    db.session.add(token)
    verify_url = url_for("auth.verify_email", token=raw, _external=True)
    body = (
        "Verify your email by opening this link:\n\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours."
    )
    send_email(user.email, "Verify your Room Near Work email", body)
    return verify_url


def verify_email_token(raw_token: str) -> User | None:
    token = EmailVerificationToken.query.filter_by(token_hash=hash_token(raw_token)).one_or_none()
    if not token or not token.is_valid():
        return None
    user = token.user
    user.email_verified = True
    user.email_verified_at = datetime.utcnow()
    token.used_at = datetime.utcnow()
    return user


def send_password_reset_email(user: User) -> str:
    token, raw = PasswordResetToken.issue(user.id)
    db.session.add(token)
    reset_url = url_for("auth.reset_password", token=raw, _external=True)
    body = (
        "Reset your password by opening this link:\n\n"
        f"{reset_url}\n\n"
        "This link expires in 60 minutes."
    )
    send_email(user.email, "Reset your Room Near Work password", body)
    return reset_url


def reset_password_with_token(raw_token: str, new_password: str) -> User | None:
    token = PasswordResetToken.query.filter_by(token_hash=hash_token(raw_token)).one_or_none()
    if not token or not token.is_valid():
        return None
    user = token.user
    user.set_password(new_password)
    token.used_at = datetime.utcnow()
    user.failed_login_count = 0
    user.locked_until = None
    return user
