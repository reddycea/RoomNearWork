from __future__ import annotations

import json

from flask import request
from flask_login import current_user

from backend.rnw.extensions import db
from backend.rnw.models import UserAuditLog


def log_action(action: str, target_type: str | None = None, target_id: str | int | None = None, metadata: dict | None = None) -> None:
    actor_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
    entry = UserAuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr) if request else None,
        user_agent=(request.user_agent.string[:255] if request and request.user_agent else None),
        metadata_json=json.dumps(metadata or {}, sort_keys=True),
    )
    db.session.add(entry)
