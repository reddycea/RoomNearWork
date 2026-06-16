from __future__ import annotations

import hashlib
from dataclasses import dataclass
from urllib.parse import urlencode

from flask import current_app, url_for

from ..models import BillingInvoice, SubscriptionPlan, User


@dataclass
class CheckoutSession:
    provider: str
    checkout_url: str
    reference: str


class PaymentService:
    """Payment abstraction layer.

    Supported now:
    - disabled: immediate sandbox activation for local development
    - payfast: redirect URL and webhook-ready reference flow for South African ZAR subscriptions

    RNW default subscriptions:
    - Tenant Plus: R50/month
    - Landlord Pro: R100/month
    """

    def create_subscription_checkout(self, user: User, plan: SubscriptionPlan, invoice: BillingInvoice) -> CheckoutSession:
        provider = current_app.config.get("PAYMENT_PROVIDER", "disabled").lower()
        invoice.provider = provider
        if provider == "disabled":
            invoice.checkout_url = url_for("billing.disabled", _external=False)
            return CheckoutSession(provider="disabled", checkout_url=invoice.checkout_url, reference=invoice.reference)
        if provider == "payfast":
            invoice.checkout_url = self._payfast_checkout_url(user, plan, invoice)
            return CheckoutSession(provider="payfast", checkout_url=invoice.checkout_url, reference=invoice.reference)
        raise NotImplementedError(f"Payment provider '{provider}' is not configured yet")

    def _payfast_checkout_url(self, user: User, plan: SubscriptionPlan, invoice: BillingInvoice) -> str:
        merchant_id = current_app.config.get("PAYFAST_MERCHANT_ID")
        merchant_key = current_app.config.get("PAYFAST_MERCHANT_KEY")
        if not merchant_id or not merchant_key:
            raise RuntimeError("PAYFAST_MERCHANT_ID and PAYFAST_MERCHANT_KEY must be configured for PayFast billing.")

        base = "https://sandbox.payfast.co.za/eng/process" if current_app.config.get("PAYFAST_SANDBOX", True) else "https://www.payfast.co.za/eng/process"
        data = {
            "merchant_id": merchant_id,
            "merchant_key": merchant_key,
            "return_url": url_for("billing.dashboard", _external=True),
            "cancel_url": url_for("billing.plans", _external=True),
            "notify_url": url_for("billing.payfast_webhook", _external=True),
            "name_first": user.first_name,
            "name_last": user.last_name,
            "email_address": user.email,
            "m_payment_id": invoice.reference,
            "amount": f"{invoice.amount:.2f}",
            "item_name": plan.name,
            "item_description": invoice.description,
            # PayFast subscription parameters. Frequency 3 = monthly; cycles 0 = indefinite.
            "subscription_type": "1",
            "billing_date": invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else "",
            "recurring_amount": f"{invoice.amount:.2f}",
            "frequency": "3",
            "cycles": "0",
        }
        passphrase = current_app.config.get("PAYFAST_PASSPHRASE")
        signature = self._payfast_signature(data, passphrase)
        data["signature"] = signature
        return f"{base}?{urlencode(data)}"

    @staticmethod
    def _payfast_signature(data: dict, passphrase: str | None = None) -> str:
        filtered = {k: v for k, v in data.items() if v not in (None, "") and k != "signature"}
        query = urlencode(sorted(filtered.items()))
        if passphrase:
            query = f"{query}&passphrase={passphrase}"
        return hashlib.md5(query.encode("utf-8")).hexdigest()

    def validate_payfast_payload(self, payload: dict) -> bool:
        signature = payload.get("signature")
        if not signature:
            return False
        return signature == self._payfast_signature(payload, current_app.config.get("PAYFAST_PASSPHRASE"))
