from flask import Blueprint, render_template
from flask_login import current_user, login_required

from backend.rnw.models import RentalApplication, SavedSearch
from backend.rnw.services.subscription_service import (
    active_subscription_for,
    tenant_application_usage,
)
from backend.rnw.utils.decorators import tenant_required


tenant_bp = Blueprint("tenant", __name__, url_prefix="/tenant")


@tenant_bp.get("/dashboard")
@login_required
@tenant_required
def dashboard():
    applications = (
        RentalApplication.query
        .filter_by(applicant_id=current_user.id)
        .order_by(RentalApplication.created_at.desc())
        .limit(10)
        .all()
    )

    saved_searches = (
        SavedSearch.query
        .filter_by(user_id=current_user.id)
        .order_by(SavedSearch.created_at.desc())
        .limit(10)
        .all()
    )

    tenant_subscription = active_subscription_for(current_user.id, "tenant")

    applications_used = 0
    applications_limit = 10

    if tenant_subscription:
        applications_limit = tenant_subscription.plan.max_rental_applications or 10
        applications_used = tenant_application_usage(
            current_user.id,
            tenant_subscription.id,
        )

    return render_template(
        "tenant/dashboard.html",
        applications=applications,
        saved_searches=saved_searches,
        tenant_subscription=tenant_subscription,
        applications_used=applications_used,
        applications_limit=applications_limit,
    )
