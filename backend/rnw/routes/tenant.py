from flask import Blueprint, render_template
from flask_login import current_user, login_required

from backend.rnw.models import RentalApplication, SavedSearch
from backend.rnw.utils.decorators import tenant_required

tenant_bp = Blueprint("tenant", __name__, url_prefix="/tenant")


@tenant_bp.get("/dashboard")
@login_required
@tenant_required
def dashboard():
    applications = RentalApplication.query.filter_by(applicant_id=current_user.id).order_by(RentalApplication.created_at.desc()).limit(10).all()
    saved_searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(SavedSearch.created_at.desc()).limit(10).all()
    return render_template("tenant/dashboard.html", applications=applications, saved_searches=saved_searches)
