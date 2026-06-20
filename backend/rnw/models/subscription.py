from __future__ import annotations

from datetime import datetime

from backend.rnw.extensions import db
from .base import TimestampMixin


class SubscriptionPlan(TimestampMixin, db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(30), nullable=False, index=True)
    price_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), default="ZAR", nullable=False)
    max_active_listings = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)


class UserSubscription(TimestampMixin, db.Model):
    __tablename__ = "user_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    role = db.Column(db.String(30), nullable=False, index=True)
    status = db.Column(db.String(40), default="active", nullable=False, index=True)
    current_period_end = db.Column(db.DateTime)

    user = db.relationship("User")
    plan = db.relationship("SubscriptionPlan")


class Invoice(TimestampMixin, db.Model):
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    amount_cents = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(10), default="ZAR", nullable=False)
    provider = db.Column(db.String(40), default="disabled", nullable=False)
    provider_reference = db.Column(db.String(160), unique=True, index=True)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    paid_at = db.Column(db.DateTime)

    user = db.relationship("User")
    plan = db.relationship("SubscriptionPlan")

    def mark_paid(self) -> None:
        if self.status == "paid":
            return
        self.status = "paid"
        self.paid_at = datetime.utcnow()


class PaymentWebhookLog(TimestampMixin, db.Model):
    __tablename__ = "payment_webhook_logs"

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(40), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    signature_valid = db.Column(db.Boolean, default=False, nullable=False)
    processed = db.Column(db.Boolean, default=False, nullable=False)
    message = db.Column(db.Text)
