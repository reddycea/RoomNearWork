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



def send_support_notification(ticket) -> None:
    """Notify the support inbox about a new ticket.

    In development, missing SMTP credentials are allowed; the event is logged so
    the workflow still works locally.
    """
    from flask import current_app
    support_email = current_app.config.get("SUPPORT_EMAIL")
    subject = f"RNW support #{ticket.id}: {ticket.subject}"
    body = (
        f"New RNW support ticket\n\n"
        f"Category: {ticket.category}\n"
        f"Priority: {ticket.priority}\n"
        f"Name: {ticket.name}\n"
        f"Email: {ticket.email}\n\n"
        f"Message:\n{ticket.message}\n"
    )
    try:
        send_email(subject, [support_email], body)
    except Exception:
        current_app.logger.exception("Support notification failed for ticket %s", ticket.id)
