from __future__ import annotations

from uuid import uuid4

from flask import current_app

from ..extensions import db
from ..models import Property, SubscriptionPlan, User, UserSubscription
from ..models.subscription import default_end_date

TENANT_MONTHLY_PRICE = 50.0
LANDLORD_MONTHLY_PRICE = 100.0
DEFAULT_CURRENCY = "ZAR"


def _configured_price(name: str, fallback: float) -> float:
    try:
        return float(current_app.config.get(name, fallback))
    except RuntimeError:
        return fallback


def _configured_int(name: str, fallback: int) -> int:
    try:
        return int(current_app.config.get(name, fallback))
    except RuntimeError:
        return fallback


def _configured_currency() -> str:
    try:
        return str(current_app.config.get("SUBSCRIPTION_CURRENCY", DEFAULT_CURRENCY)).upper()
    except RuntimeError:
        return DEFAULT_CURRENCY


def default_plans() -> list[dict]:
    """Return plan definitions using environment-configurable prices.

    Edit these values through `.env` instead of editing Python code:

    - TENANT_MONTHLY_PRICE=50
    - LANDLORD_MONTHLY_PRICE=100
    - LANDLORD_MAX_LISTINGS=25
    - SUBSCRIPTION_CURRENCY=ZAR
    """
    tenant_price = _configured_price("TENANT_MONTHLY_PRICE", TENANT_MONTHLY_PRICE)
    landlord_price = _configured_price("LANDLORD_MONTHLY_PRICE", LANDLORD_MONTHLY_PRICE)
    landlord_max_listings = _configured_int("LANDLORD_MAX_LISTINGS", 25)
    currency = _configured_currency()
    return [
        {
            "name": "Tenant Plus",
            "role": "tenant",
            "price": tenant_price,
            "currency": currency,
            "billing_period": "monthly",
            "max_listings": 0,
            "is_featured": False,
            "support_level": "Standard",
            "features": "Apply for rentals; Save unlimited properties; AI recommendations; Application history; Application status tracker",
        },
        {
            "name": "Landlord Pro",
            "role": "landlord",
            "price": landlord_price,
            "currency": currency,
            "billing_period": "monthly",
            "max_listings": landlord_max_listings,
            "is_featured": True,
            "support_level": "Priority",
            "features": f"Create up to {landlord_max_listings} active listings; Receive tenant applications; Featured visibility; Verification-ready landlord profile; Landlord analytics",
        },
    ]


# Backwards-compatible constant for tests/imports; ensure_default_plans() uses default_plans().
DEFAULT_PLANS = default_plans


def ensure_default_plans() -> None:
    """Create or update the official RNW monthly tenant/landlord plans."""
    for item in default_plans():
        plan = SubscriptionPlan.query.filter_by(name=item["name"]).first()
        if not plan:
            plan = SubscriptionPlan(name=item["name"])
            db.session.add(plan)
        for key, value in item.items():
            setattr(plan, key, value)
        plan.is_active = True


def get_available_plans(role: str | None = None) -> list[SubscriptionPlan]:
    query = SubscriptionPlan.query.filter_by(is_active=True)
    if role in {"tenant", "landlord"}:
        query = query.filter_by(role=role)
    return query.order_by(SubscriptionPlan.role.asc(), SubscriptionPlan.price.asc()).all()


def get_default_plan_for_role(role: str) -> SubscriptionPlan | None:
    if role not in {"tenant", "landlord"}:
        return None
    ensure_default_plans()
    return SubscriptionPlan.query.filter_by(role=role, is_active=True).order_by(SubscriptionPlan.price.asc()).first()


def subscribe_user(user: User, plan: SubscriptionPlan, provider: str = "manual", reference: str | None = None, months: int = 1) -> UserSubscription:
    """Activate a subscription and expire older active plans for the same role."""
    if plan.role != user.role:
        raise ValueError(f"{plan.name} is a {plan.role} plan and cannot be assigned to a {user.role} account.")

    for subscription in UserSubscription.query.filter_by(user_id=user.id, status="active").all():
        if subscription.plan and subscription.plan.role == plan.role:
            subscription.status = "expired"
            subscription.auto_renew = False

    subscription = UserSubscription(
        user_id=user.id,
        plan_id=plan.id,
        provider=provider,
        reference=reference or f"rnw_sub_{uuid4().hex}",
        amount=plan.price,
        currency=plan.currency,
        status="active",
        end_date=default_end_date(months),
        auto_renew=True,
    )
    db.session.add(subscription)
    return subscription


def landlord_active_listing_count(user: User) -> int:
    if user.role != "landlord":
        return 0
    return Property.query.filter(
        Property.landlord_id == user.id,
        Property.status.in_(["pending", "approved"]),
        Property.is_available.is_(True),
    ).count()


def landlord_listing_limit(user: User) -> int | None:
    if user.role == "admin":
        return None
    subscription = user.active_subscription
    if not subscription or not subscription.plan:
        return 0
    return subscription.plan.max_listings


def landlord_can_create_listing(user: User) -> tuple[bool, int | None, int]:
    if user.role == "admin":
        return True, None, 0
    limit = landlord_listing_limit(user)
    count = landlord_active_listing_count(user)
    return bool(limit is not None and count < limit), limit, count
