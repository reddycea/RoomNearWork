from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from sqlalchemy import func

from ..extensions import db
from ..models import BillingInvoice, LandlordVerification, Property, RentalApplication, SubscriptionPlan, User, UserSubscription
from ..services.audit_service import log_admin_action
from ..services.billing_service import cancel_subscription, extend_subscription
from ..services.subscription_service import get_available_plans, subscribe_user
from ..utils.decorators import roles_required
from ..utils.security import private_relative_path

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@roles_required("admin")
def dashboard():
    revenue = db.session.query(func.coalesce(func.sum(BillingInvoice.amount), 0)).select_from(BillingInvoice).filter(BillingInvoice.status == "paid").scalar() or 0
    metrics = {
        "users": User.query.count(),
        "landlords": User.query.filter_by(role="landlord").count(),
        "tenants": User.query.filter_by(role="tenant").count(),
        "active_subscriptions": UserSubscription.query.filter_by(status="active").count(),
        "monthly_revenue_zar": round(float(revenue), 2),
        "pending_properties": Property.query.filter_by(status="pending").count(),
        "approved_properties": Property.query.filter_by(status="approved").count(),
        "pending_applications": RentalApplication.query.filter_by(status="pending").count(),
    }
    pending_properties = Property.query.filter_by(status="pending").order_by(Property.created_at.desc()).limit(10).all()
    pending_verifications = LandlordVerification.query.filter_by(status="pending").order_by(LandlordVerification.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", metrics=metrics, pending_properties=pending_properties, pending_verifications=pending_verifications)


@admin_bp.get("/users")
@roles_required("admin")
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=all_users)


@admin_bp.post("/users/<int:user_id>/<action>")
@roles_required("admin")
def user_action(user_id: int, action: str):
    user = db.session.get(User, user_id) or abort(404)
    if user.id == current_user.id:
        flash("You cannot change your own account status here.", "warning")
        return redirect(url_for("admin.users"))
    if action == "activate":
        user.is_active = True
    elif action == "suspend":
        user.is_active = False
    elif action == "verify-email":
        user.email_verified_at = datetime.utcnow()
    else:
        abort(400)
    log_admin_action(action, "user", user.id)
    db.session.commit()
    flash("User updated.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.get("/properties")
@roles_required("admin")
def properties():
    status = request.args.get("status")
    query = Property.query
    if status:
        query = query.filter_by(status=status)
    return render_template("admin/properties.html", properties=query.order_by(Property.created_at.desc()).all())


@admin_bp.post("/properties/<int:property_id>/<action>")
@roles_required("admin")
def property_action(property_id: int, action: str):
    prop = db.session.get(Property, property_id) or abort(404)
    if action not in {"approve", "reject"}:
        abort(400)
    prop.status = "approved" if action == "approve" else "rejected"
    log_admin_action(action, "property", prop.id, prop.title)
    db.session.commit()
    flash(f"Property {prop.status}.", "success")
    return redirect(url_for("admin.properties"))


@admin_bp.get("/verifications")
@roles_required("admin")
def verifications():
    items = LandlordVerification.query.order_by(LandlordVerification.created_at.desc()).all()
    return render_template("admin/verifications.html", verifications=items)


@admin_bp.post("/verifications/<int:verification_id>/<action>")
@roles_required("admin")
def verification_action(verification_id: int, action: str):
    verification = db.session.get(LandlordVerification, verification_id) or abort(404)
    if action == "verify":
        verification.status = "verified"
        verification.user.is_verified = True
        verification.verified_by = current_user.id
        verification.verified_at = datetime.utcnow()
    elif action == "reject":
        verification.status = "rejected"
        verification.rejection_reason = request.form.get("rejection_reason")
        verification.user.is_verified = False
    else:
        abort(400)
    log_admin_action(action, "landlord_verification", verification.id)
    db.session.commit()
    flash("Verification updated.", "success")
    return redirect(url_for("admin.verifications"))


@admin_bp.get("/private-files/<path:relative_path>")
@roles_required("admin")
def private_file(relative_path: str):
    if ".." in Path(relative_path).parts:
        abort(404)
    private_root = current_app.config["UPLOAD_FOLDER_PATH"] / "private"
    return send_from_directory(private_root, relative_path, as_attachment=True)


@admin_bp.get("/billing")
@roles_required("admin")
def billing():
    plans = get_available_plans()
    subscriptions = UserSubscription.query.order_by(UserSubscription.created_at.desc()).limit(100).all()
    invoices = BillingInvoice.query.order_by(BillingInvoice.created_at.desc()).limit(100).all()
    revenue = db.session.query(func.coalesce(func.sum(BillingInvoice.amount), 0)).select_from(BillingInvoice).filter(BillingInvoice.status == "paid").scalar() or 0
    metrics = {
        "paid_invoices": BillingInvoice.query.filter_by(status="paid").count(),
        "pending_invoices": BillingInvoice.query.filter_by(status="pending").count(),
        "active_subscriptions": UserSubscription.query.filter_by(status="active").count(),
        "revenue_zar": round(float(revenue), 2),
    }
    return render_template("admin/billing.html", plans=plans, subscriptions=subscriptions, invoices=invoices, metrics=metrics)


@admin_bp.post("/billing/users/<int:user_id>/activate")
@roles_required("admin")
def activate_user_subscription(user_id: int):
    user = db.session.get(User, user_id) or abort(404)
    plan = db.session.get(SubscriptionPlan, int(request.form.get("plan_id") or 0)) or abort(404)
    months = max(1, min(int(request.form.get("months") or 1), 24))
    if plan.role != user.role:
        flash("Selected plan does not match the user's role.", "danger")
        return redirect(url_for("admin.billing"))
    subscription = subscribe_user(user, plan, provider="admin", reference=f"admin_manual_{user.id}_{int(datetime.utcnow().timestamp())}", months=months)
    log_admin_action("activate_subscription", "subscription", user.id, plan.name)
    db.session.commit()
    flash(f"Manual subscription activated for {user.full_name}: {subscription.plan.name}.", "success")
    return redirect(url_for("admin.billing"))


@admin_bp.post("/billing/subscriptions/<int:subscription_id>/<action>")
@roles_required("admin")
def subscription_action(subscription_id: int, action: str):
    subscription = db.session.get(UserSubscription, subscription_id) or abort(404)
    if action == "cancel":
        cancel_subscription(subscription)
    elif action == "extend":
        months = max(1, min(int(request.form.get("months") or 1), 24))
        extend_subscription(subscription, months)
    elif action == "reactivate":
        subscription.status = "active"
        subscription.auto_renew = True
    else:
        abort(400)
    log_admin_action(action, "subscription", subscription.id)
    db.session.commit()
    flash("Subscription updated.", "success")
    return redirect(url_for("admin.billing"))


def private_file_link(private_url: str | None) -> str | None:
    relative = private_relative_path(private_url)
    return url_for("admin.private_file", relative_path=relative) if relative else None
