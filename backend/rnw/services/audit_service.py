from __future__ import annotations

from flask import request
from flask_login import current_user

from ..extensions import db
from ..models import AdminAuditLog


def log_admin_action(action: str, target_type: str | None = None, target_id: int | None = None, details: str | None = None) -> None:
    admin_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
    )
    db.session.add(log)
