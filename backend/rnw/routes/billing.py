from __future__ import annotations

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_login import current_user, login_required

from ..extensions import csrf, db
from ..models import BillingInvoice, SubscriptionPlan, User, UserSubscription
from ..services.billing_service import activate_subscription_from_invoice, cancel_subscription, create_invoice
from ..services.payment_service import PaymentService
from ..services.subscription_service import ensure_default_plans, get_available_plans

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.get("/plans")
@login_required
def plans():
    ensure_default_plans()
    role_filter = current_user.role if current_user.role in {"tenant", "landlord"} else None
    available_plans = get_available_plans(role_filter)
    return render_template("billing/plans.html", plans=available_plans, active_subscription=current_user.active_subscription)


@billing_bp.get("/dashboard")
@login_required
def dashboard():
    subscriptions = UserSubscription.query.filter_by(user_id=current_user.id).order_by(UserSubscription.created_at.desc()).all()
    invoices = BillingInvoice.query.filter_by(user_id=current_user.id).order_by(BillingInvoice.created_at.desc()).limit(25).all()
    return render_template("billing/dashboard.html", subscriptions=subscriptions, invoices=invoices, active_subscription=current_user.active_subscription)


@billing_bp.post("/subscribe/<int:plan_id>")
@login_required
def subscribe(plan_id: int):
    plan = db.session.get(SubscriptionPlan, plan_id) or abort(404)
    if current_user.role not in {"tenant", "landlord"}:
        flash("Only tenant and landlord accounts need subscriptions.", "info")
        return redirect(url_for("main.index"))
    if plan.role != current_user.role:
        abort(403)

    invoice = create_invoice(current_user, plan)
    checkout = PaymentService().create_subscription_checkout(current_user, plan, invoice)

    if checkout.provider == "disabled":
        activate_subscription_from_invoice(invoice, checkout.reference)
        db.session.commit()
        flash(f"{plan.name} activated at {plan.price_label()}. Sandbox billing is enabled for development.", "success")
        return redirect(url_for("billing.dashboard"))

    db.session.commit()
    return redirect(checkout.checkout_url)


@billing_bp.post("/subscriptions/<int:subscription_id>/cancel")
@login_required
def cancel(subscription_id: int):
    subscription = db.session.get(UserSubscription, subscription_id) or abort(404)
    if subscription.user_id != current_user.id and current_user.role != "admin":
        abort(403)
    cancel_subscription(subscription)
    db.session.commit()
    flash("Subscription cancelled. Access continues only until the paid period ends if your payment provider supports grace periods.", "info")
    return redirect(url_for("billing.dashboard"))


@billing_bp.get("/disabled")
@login_required
def disabled():
    flash("Payment provider is disabled. Set PAYMENT_PROVIDER=payfast before production billing.", "info")
    return redirect(url_for("billing.plans"))


@billing_bp.post("/webhooks/payfast")
@csrf.exempt
def payfast_webhook():
    payload = request.form.to_dict()
    reference = payload.get("m_payment_id")
    invoice = BillingInvoice.query.filter_by(reference=reference).first() if reference else None
    if not invoice:
        return "Invoice not found", 404

    payment_service = PaymentService()
    if not payment_service.validate_payfast_payload(payload):
        invoice.mark_failed("Invalid PayFast signature")
        db.session.commit()
        return "Invalid signature", 400

    status = payload.get("payment_status", "").upper()
    if status == "COMPLETE":
        activate_subscription_from_invoice(invoice, payload.get("pf_payment_id"))
    else:
        invoice.mark_failed(f"PayFast status: {status or 'unknown'}")
    db.session.commit()
    return "OK", 200


@billing_bp.get("/api/plans")
def api_plans():
    ensure_default_plans()
    role = request.args.get("role")
    plans = get_available_plans(role if role in {"tenant", "landlord"} else None)
    return jsonify({"data": [plan.to_dict() for plan in plans]})


@billing_bp.get("/api/subscription")
@jwt_required()
def api_subscription():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return jsonify({"message": "User not found"}), 404
    invoices = BillingInvoice.query.filter_by(user_id=user.id).order_by(BillingInvoice.created_at.desc()).limit(10).all()
    return jsonify({
        "active_subscription": user.active_subscription.to_dict() if user.active_subscription else None,
        "invoices": [invoice.to_dict() for invoice in invoices],
    })


@billing_bp.post("/api/subscribe")
@csrf.exempt
@jwt_required()
def api_subscribe():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return jsonify({"message": "User not found"}), 404
    if user.role not in {"tenant", "landlord"}:
        return jsonify({"message": "Only tenant and landlord accounts need subscriptions."}), 400

    data = request.get_json(silent=True) or {}
    plan = db.session.get(SubscriptionPlan, int(data.get("plan_id") or 0))
    if not plan or not plan.is_active:
        return jsonify({"message": "Subscription plan not found"}), 404
    if plan.role != user.role:
        return jsonify({"message": f"This plan is only for {plan.role} accounts."}), 403

    invoice = create_invoice(user, plan)
    checkout = PaymentService().create_subscription_checkout(user, plan, invoice)
    if checkout.provider == "disabled":
        subscription = activate_subscription_from_invoice(invoice, checkout.reference)
        db.session.commit()
        return jsonify({"message": "Subscription activated in sandbox mode.", "subscription": subscription.to_dict(), "invoice": invoice.to_dict()}), 201

    db.session.commit()
    return jsonify({"checkout_url": checkout.checkout_url, "reference": checkout.reference, "provider": checkout.provider, "invoice": invoice.to_dict()}), 202
