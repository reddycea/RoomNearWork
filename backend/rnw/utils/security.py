from __future__ import annotations

import hmac
import re
from datetime import datetime, timedelta

import bleach
from flask import request

PASSWORD_RE = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")


def password_is_strong(password: str) -> bool:
    return bool(PASSWORD_RE.match(password or ""))


def clean_user_text(value: str | None, max_len: int = 3000) -> str:
    cleaned = bleach.clean(value or "", tags=[], attributes={}, strip=True).strip()
    return cleaned[:max_len]


def client_ip() -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def locked_until_after_fail(failed_count: int):
    if failed_count >= 5:
        return datetime.utcnow() + timedelta(minutes=15)
    return None


def safe_compare(left: str | None, right: str | None) -> bool:
    return hmac.compare_digest(left or "", right or "")
