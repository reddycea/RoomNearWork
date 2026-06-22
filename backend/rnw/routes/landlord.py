from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from backend.rnw.extensions import db
from backend.rnw.models import Property, RentalApplication
from backend.rnw.utils.decorators import landlord_required

landlord_bp = Blueprint("landlord", __name__, url_prefix="/landlord")


@landlord_bp.get("/dashboard")
@login_required
@landlord_required
def dashboard():
    properties = Property.query.filter_by(landlord_id=current_user.id).order_by(Property.created_at.desc()).all()
    applications = RentalApplication.query.join(Property).filter(Property.landlord_id == current_user.id).order_by(RentalApplication.created_at.desc()).limit(20).all()
    return render_template("landlord/dashboard.html", properties=properties, applications=applications)


@landlord_bp.post("/applications/<int:application_id>/<action>")
@login_required
@landlord_required
def application_action(application_id: int, action: str):
    if action not in {"approved", "rejected"}:
        abort(404)
    application = db.session.execute(db.select(RentalApplication).where(RentalApplication.id == application_id).with_for_update()).scalar_one_or_none()
    if not application or application.property.landlord_id != current_user.id:
        abort(404)
    application.status = action
    db.session.commit()
    flash(f"Application {action}.", "success")
    return redirect(url_for("landlord.dashboard"))
