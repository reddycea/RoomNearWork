from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.rnw.extensions import csrf, db
from backend.rnw.models import SubscriptionPlan, UserSubscription
from backend.rnw.services.billing_service import activate_invoice, create_invoice, process_payfast_webhook

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")


@billing_bp.get("")
@login_required
def index():
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    subscriptions = UserSubscription.query.filter_by(user_id=current_user.id).order_by(UserSubscription.created_at.desc()).all()
    return render_template("billing/index.html", plans=plans, subscriptions=subscriptions)


@billing_bp.post("/subscribe/<int:plan_id>")
@login_required
def subscribe(plan_id: int):
    plan = db.session.get(SubscriptionPlan, plan_id)
    invoice = create_invoice(current_user.id, plan.id, plan.price_cents, plan.currency, current_app.config.get("PAYMENT_PROVIDER", "disabled"))
    if current_app.config.get("PAYMENT_PROVIDER") == "disabled":
        db.session.flush()
        activate_invoice(invoice.id)
        db.session.commit()
        flash("Subscription activated for local development.", "success")
        return redirect(url_for("billing.index"))
    db.session.commit()
    flash("Invoice created. Connect PayFast checkout in production.", "info")
    return redirect(url_for("billing.index"))


@billing_bp.post("/webhooks/payfast")
@csrf.exempt
def payfast_webhook():
    ok, message = process_payfast_webhook(request.form.to_dict())
    return ("OK" if ok else message), (200 if ok else 400)
