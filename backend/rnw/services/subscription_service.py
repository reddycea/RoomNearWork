from __future__ import annotations

from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import func, or_

from backend.rnw.extensions import db
from backend.rnw.models import (
    Property,
    RentalApplication,
    SubscriptionPlan,
    User,
    UserSubscription,
)


def ensure_default_plans() -> None:
    currency = current_app.config.get("SUBSCRIPTION_CURRENCY", "ZAR")

    tenant_price = current_app.config.get("TENANT_MONTHLY_PRICE", 50) * 100
    landlord_price = current_app.config.get("LANDLORD_MONTHLY_PRICE", 100) * 100

    tenant_application_limit = current_app.config.get(
        "TENANT_MAX_RENTAL_APPLICATIONS",
        10,
    )

    landlord_limit = current_app.config.get("LANDLORD_MAX_LISTINGS", 25)

    plans = [
        (
            "Tenant Plus",
            "tenant",
            tenant_price,
            None,
            tenant_application_limit,
        ),
        (
            "Landlord Pro",
            "landlord",
            landlord_price,
            landlord_limit,
            0,
        ),
    ]

    for name, role, price, max_listings, max_applications in plans:
        plan = SubscriptionPlan.query.filter_by(name=name).one_or_none()

        if not plan:
            plan = SubscriptionPlan(name=name, role=role)
            db.session.add(plan)

        plan.price_cents = price
        plan.currency = currency
        plan.max_active_listings = max_listings
        plan.max_rental_applications = max_applications
        plan.is_active = True


def set_plan_prices(
    tenant_price: int,
    landlord_price: int,
    landlord_listings: int,
) -> None:
    ensure_default_plans()

    tenant = SubscriptionPlan.query.filter_by(name="Tenant Plus").one()
    landlord = SubscriptionPlan.query.filter_by(name="Landlord Pro").one()

    tenant.price_cents = tenant_price * 100
    tenant.max_rental_applications = current_app.config.get(
        "TENANT_MAX_RENTAL_APPLICATIONS",
        10,
    )

    landlord.price_cents = landlord_price * 100
    landlord.max_active_listings = landlord_listings
    landlord.max_rental_applications = 0


def active_subscription_for(user_id: int, role: str) -> UserSubscription | None:
    now = datetime.utcnow()

    return (
        UserSubscription.query
        .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
        .filter(
            UserSubscription.user_id == user_id,
            UserSubscription.role == role,
            UserSubscription.status == "active",
            SubscriptionPlan.role == role,
            or_(
                UserSubscription.current_period_end.is_(None),
                UserSubscription.current_period_end >= now,
            ),
        )
        .order_by(UserSubscription.created_at.desc())
        .first()
    )


def activate_subscription(user_id: int, plan_id: int) -> UserSubscription:
    plan = db.session.get(SubscriptionPlan, plan_id)

    existing = active_subscription_for(user_id, plan.role)

    if existing:
        existing.current_period_end = datetime.utcnow() + timedelta(days=30)
        return existing

    sub = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        role=plan.role,
        status="active",
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )

    db.session.add(sub)

    return sub


def tenant_application_usage(
    user_id: int,
    tenant_subscription_id: int,
) -> int:
    used = db.session.scalar(
        db.select(func.count(RentalApplication.id)).where(
            RentalApplication.applicant_id == user_id,
            RentalApplication.tenant_subscription_id == tenant_subscription_id,
            RentalApplication.status != "withdrawn",
        )
    )

    return used or 0


def tenant_can_apply_for_rental(
    user_id: int,
) -> tuple[bool, str, UserSubscription | None, int, int]:
    tenant_subscription = active_subscription_for(user_id, "tenant")

    if not tenant_subscription:
        return (
            False,
            "Please pay tenant subscription before applying for rentals.",
            None,
            0,
            0,
        )

    max_applications = tenant_subscription.plan.max_rental_applications or 10

    used_applications = tenant_application_usage(
        user_id,
        tenant_subscription.id,
    )

    if used_applications >= max_applications:
        return (
            False,
            f"You have reached your {max_applications} rental application limit.",
            tenant_subscription,
            used_applications,
            max_applications,
        )

    return (
        True,
        "",
        tenant_subscription,
        used_applications,
        max_applications,
    )


def landlord_has_active_subscription(user_id: int) -> bool:
    return active_subscription_for(user_id, "landlord") is not None


def landlord_can_create_listing(user_id: int) -> bool:
    sub = active_subscription_for(user_id, "landlord")

    max_listings = (
        sub.plan.max_active_listings
        if sub and sub.plan.max_active_listings
        else current_app.config.get("LANDLORD_MAX_LISTINGS", 25)
    )

    active_count = db.session.scalar(
        db.select(func.count(Property.id)).where(
            Property.landlord_id == user_id,
            Property.is_active.is_(True),
            Property.status != "expired",
        )
    )

    return (active_count or 0) < max_listings


def lock_user(user_id: int) -> User:
    return (
        db.session.execute(
            db.select(User)
            .where(User.id == user_id)
            .with_for_update()
        )
        .scalar_one()
    )
