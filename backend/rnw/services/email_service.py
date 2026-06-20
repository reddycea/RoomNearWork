from __future__ import annotations

from flask import current_app
from flask_mail import Message

from backend.rnw.extensions import mail


def send_email(to: str, subject: str, body: str) -> None:
    if current_app.config.get("TESTING"):
        return
    msg = Message(subject=subject, recipients=[to], body=body)
    try:
        mail.send(msg)
    except Exception as exc:  # keep app responsive in local dev
        current_app.logger.warning("Email not sent: %s", exc)
