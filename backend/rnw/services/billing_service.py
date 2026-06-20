from __future__ import annotations

import json
from datetime import datetime

from backend.rnw.extensions import db
from backend.rnw.models import Invoice, PaymentWebhookLog
from backend.rnw.services.payment_service import validate_payfast_itn
from backend.rnw.services.subscription_service import activate_subscription


def create_invoice(user_id: int, plan_id: int, amount_cents: int, currency: str = "ZAR", provider: str = "disabled") -> Invoice:
    invoice = Invoice(user_id=user_id, plan_id=plan_id, amount_cents=amount_cents, currency=currency, provider=provider, status="pending")
    db.session.add(invoice)
    db.session.flush()
    invoice.provider_reference = f"RNW-{invoice.id}"
    return invoice


def activate_invoice(invoice_id: int) -> Invoice:
    invoice = db.session.execute(db.select(Invoice).where(Invoice.id == invoice_id).with_for_update()).scalar_one()
    if invoice.status != "paid":
        invoice.mark_paid()
        activate_subscription(invoice.user_id, invoice.plan_id)
    return invoice


def process_payfast_webhook(data: dict) -> tuple[bool, str]:
    ok, message = validate_payfast_itn(data)
    log = PaymentWebhookLog(provider="payfast", payload=json.dumps(data, sort_keys=True), signature_valid=ok, message=message)
    db.session.add(log)
    if not ok:
        db.session.commit()
        return False, message
    reference = data.get("m_payment_id") or data.get("custom_str1") or data.get("item_name")
    invoice = db.session.execute(db.select(Invoice).where(Invoice.provider_reference == reference).with_for_update()).scalar_one_or_none()
    if not invoice:
        log.message = "Invoice not found"
        db.session.commit()
        return False, "Invoice not found"
    invoice.mark_paid()
    activate_subscription(invoice.user_id, invoice.plan_id)
    log.processed = True
    log.message = "Processed"
    db.session.commit()
    return True, "Processed"
