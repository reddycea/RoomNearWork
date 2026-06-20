from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import func

from backend.rnw.extensions import db
from backend.rnw.models import Property, SubscriptionPlan, UserSubscription, User


def ensure_default_plans() -> None:
    currency = current_app.config.get("SUBSCRIPTION_CURRENCY", "ZAR")
    tenant_price = current_app.config.get("TENANT_MONTHLY_PRICE", 50) * 100
    landlord_price = current_app.config.get("LANDLORD_MONTHLY_PRICE", 100) * 100
    landlord_limit = current_app.config.get("LANDLORD_MAX_LISTINGS", 25)
    plans = [
        ("Tenant Plus", "tenant", tenant_price, None),
        ("Landlord Pro", "landlord", landlord_price, landlord_limit),
    ]
    for name, role, price, max_listings in plans:
        plan = SubscriptionPlan.query.filter_by(name=name).one_or_none()
        if not plan:
            plan = SubscriptionPlan(name=name, role=role)
            db.session.add(plan)
        plan.price_cents = price
        plan.currency = currency
        plan.max_active_listings = max_listings
        plan.is_active = True


def set_plan_prices(tenant_price: int, landlord_price: int, landlord_listings: int) -> None:
    ensure_default_plans()
    tenant = SubscriptionPlan.query.filter_by(name="Tenant Plus").one()
    landlord = SubscriptionPlan.query.filter_by(name="Landlord Pro").one()
    tenant.price_cents = tenant_price * 100
    landlord.price_cents = landlord_price * 100
    landlord.max_active_listings = landlord_listings


def active_subscription_for(user_id: int, role: str) -> UserSubscription | None:
    return UserSubscription.query.filter_by(user_id=user_id, role=role, status="active").order_by(UserSubscription.created_at.desc()).first()


def activate_subscription(user_id: int, plan_id: int) -> UserSubscription:
    plan = db.session.get(SubscriptionPlan, plan_id)
    existing = active_subscription_for(user_id, plan.role)
    if existing:
        existing.current_period_end = datetime.utcnow() + timedelta(days=30)
        return existing
    sub = UserSubscription(user_id=user_id, plan_id=plan.id, role=plan.role, status="active", current_period_end=datetime.utcnow() + timedelta(days=30))
    db.session.add(sub)
    return sub


def landlord_can_create_listing(user_id: int) -> bool:
    sub = active_subscription_for(user_id, "landlord")
    max_listings = sub.plan.max_active_listings if sub and sub.plan.max_active_listings else current_app.config.get("LANDLORD_MAX_LISTINGS", 25)
    active_count = db.session.scalar(
        db.select(func.count(Property.id)).where(Property.landlord_id == user_id, Property.is_active.is_(True), Property.status != "expired")
    )
    return (active_count or 0) < max_listings


def lock_user(user_id: int) -> User:
    return db.session.execute(db.select(User).where(User.id == user_id).with_for_update()).scalar_one()
