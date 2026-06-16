from __future__ import annotations

from datetime import datetime, timedelta

from ..extensions import db
from .base import TimestampMixin


class SubscriptionPlan(TimestampMixin, db.Model):
    __tablename__ = "subscription_plans"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    role = db.Column(db.String(20), nullable=False, default="landlord", index=True)  # tenant or landlord
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="ZAR")
    billing_period = db.Column(db.String(20), nullable=False, default="monthly")
    max_listings = db.Column(db.Integer, nullable=False, default=0)
    is_featured = db.Column(db.Boolean, default=False, nullable=False)
    support_level = db.Column(db.String(50), default="Basic")
    features = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def price_label(self) -> str:
        symbol = "R" if self.currency == "ZAR" else f"{self.currency} "
        amount = f"{self.price:.0f}" if float(self.price).is_integer() else f"{self.price:.2f}"
        suffix = "pm" if self.billing_period == "monthly" else f"/{self.billing_period}"
        return f"{symbol}{amount}{suffix}"

    def feature_list(self) -> list[str]:
        if not self.features:
            return []
        return [item.strip() for item in self.features.split(";") if item.strip()]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "price": self.price,
            "currency": self.currency,
            "billing_period": self.billing_period,
            "price_label": self.price_label(),
            "max_listings": self.max_listings,
            "is_featured": self.is_featured,
            "support_level": self.support_level,
            "features": self.feature_list(),
            "is_active": self.is_active,
        }


class UserSubscription(TimestampMixin, db.Model):
    __tablename__ = "user_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    provider = db.Column(db.String(30), nullable=False, default="manual")
    reference = db.Column(db.String(120), nullable=True, unique=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="ZAR")
    status = db.Column(db.String(20), nullable=False, default="active", index=True)  # active, cancelled, expired, past_due
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    auto_renew = db.Column(db.Boolean, default=True, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="subscriptions")
    plan = db.relationship("SubscriptionPlan")
    invoices = db.relationship("BillingInvoice", back_populates="subscription", cascade="all, delete-orphan")

    @property
    def is_current(self) -> bool:
        return self.status == "active" and (self.end_date is None or self.end_date >= datetime.utcnow())

    def cancel(self) -> None:
        self.status = "cancelled"
        self.auto_renew = False
        self.cancelled_at = datetime.utcnow()

    def extend(self, months: int = 1) -> None:
        base = self.end_date if self.end_date and self.end_date > datetime.utcnow() else datetime.utcnow()
        self.end_date = base + timedelta(days=30 * months)
        self.status = "active"
        self.auto_renew = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "plan": self.plan.to_dict() if self.plan else None,
            "status": self.status,
            "amount": self.amount,
            "currency": self.currency,
            "provider": self.provider,
            "reference": self.reference,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "auto_renew": self.auto_renew,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
        }


class BillingInvoice(TimestampMixin, db.Model):
    __tablename__ = "billing_invoices"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("user_subscriptions.id"), nullable=True)
    provider = db.Column(db.String(30), nullable=False, default="manual")
    reference = db.Column(db.String(120), nullable=False, unique=True, index=True)
    external_id = db.Column(db.String(120), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="ZAR")
    description = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)  # pending, paid, failed, cancelled, refunded
    checkout_url = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    failed_reason = db.Column(db.Text, nullable=True)

    user = db.relationship("User", back_populates="invoices")
    plan = db.relationship("SubscriptionPlan")
    subscription = db.relationship("UserSubscription", back_populates="invoices")

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"

    def mark_paid(self, external_id: str | None = None) -> None:
        self.status = "paid"
        self.paid_at = datetime.utcnow()
        if external_id:
            self.external_id = external_id

    def mark_failed(self, reason: str | None = None) -> None:
        self.status = "failed"
        self.failed_reason = reason

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reference": self.reference,
            "provider": self.provider,
            "amount": self.amount,
            "currency": self.currency,
            "description": self.description,
            "status": self.status,
            "checkout_url": self.checkout_url,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "plan": self.plan.to_dict() if self.plan else None,
        }


class LandlordSubscription(TimestampMixin, db.Model):
    """Legacy landlord-only subscription table kept for migration compatibility.

    New code should use UserSubscription so tenant and landlord subscriptions share
    the same billing flow.
    """

    __tablename__ = "landlord_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.id"), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    auto_renew = db.Column(db.Boolean, default=True, nullable=False)

    landlord = db.relationship("User", foreign_keys=[landlord_id])
    plan = db.relationship("SubscriptionPlan")


def default_end_date(months: int = 1) -> datetime:
    return datetime.utcnow() + timedelta(days=30 * months)
