from __future__ import annotations

from datetime import datetime

from backend.rnw.extensions import db
from backend.rnw.models import User
from backend.rnw.utils.security import client_ip, locked_until_after_fail


def record_failed_login(user: User | None) -> None:
    if not user:
        return
    user.failed_login_count += 1
    user.locked_until = locked_until_after_fail(user.failed_login_count)
    db.session.commit()


def record_successful_login(user: User) -> None:
    user.mark_login_success(client_ip())
    db.session.commit()


def is_locked(user: User) -> bool:
    return bool(user.locked_until and user.locked_until > datetime.utcnow())
