from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

from ..extensions import db
from ..models import BillingInvoice, SubscriptionPlan, User, UserSubscription
from .subscription_service import subscribe_user


def create_invoice(user: User, plan: SubscriptionPlan, provider: str = "manual", reference: str | None = None) -> BillingInvoice:
    invoice = BillingInvoice(
        user_id=user.id,
        plan_id=plan.id,
        provider=provider,
        reference=reference or f"rnw_inv_{uuid4().hex}",
        amount=plan.price,
        currency=plan.currency,
        description=f"{plan.name} subscription - {plan.price_label()}",
        status="pending",
        due_date=datetime.utcnow() + timedelta(days=1),
    )
    db.session.add(invoice)
    return invoice


def activate_subscription_from_invoice(invoice: BillingInvoice, provider_reference: str | None = None) -> UserSubscription:
    if invoice.plan.role != invoice.user.role:
        raise ValueError("Invoice plan role does not match user role.")
    if not invoice.is_paid:
        invoice.mark_paid(provider_reference)
    subscription = subscribe_user(invoice.user, invoice.plan, provider=invoice.provider, reference=invoice.reference)
    invoice.subscription = subscription
    return subscription


def cancel_subscription(subscription: UserSubscription) -> None:
    subscription.cancel()


def extend_subscription(subscription: UserSubscription, months: int = 1) -> None:
    subscription.extend(months)
