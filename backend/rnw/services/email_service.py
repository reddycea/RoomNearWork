from __future__ import annotations

from threading import Thread

from flask import current_app
from flask_mail import Message

from ..extensions import mail


def send_email(subject: str, recipients: list[str], body: str, html: str | None = None, async_send: bool = True) -> None:
    if not recipients:
        return
    msg = Message(subject=subject, recipients=recipients, body=body, html=html)

    if async_send:
        app = current_app._get_current_object()
        Thread(target=_send_with_context, args=(app, msg), daemon=True).start()
    else:
        mail.send(msg)


def _send_with_context(app, msg: Message) -> None:
    with app.app_context():
        try:
            mail.send(msg)
        except Exception:
            app.logger.exception("Failed to send email: %s", msg.subject)
