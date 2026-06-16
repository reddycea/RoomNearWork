from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Property, RentalApplication, SavedProperty
from ..services.recommendation_service import recommend_properties
from ..utils.decorators import email_verified_required, roles_required, subscription_required
from ..utils.validators import parse_bool, parse_optional_float

tenant_bp = Blueprint("tenant", __name__, url_prefix="/tenant")


@tenant_bp.get("/dashboard")
@roles_required("tenant", "admin")
def dashboard():
    applications = RentalApplication.query.filter_by(applicant_id=current_user.id).order_by(RentalApplication.created_at.desc()).all()
    saved = SavedProperty.query.filter_by(user_id=current_user.id).order_by(SavedProperty.saved_at.desc()).limit(6).all()
    recommendations = recommend_properties(current_user, limit=6) if current_user.has_active_subscription() else []
    return render_template("tenant/dashboard.html", applications=applications, saved=saved, recommendations=recommendations)


@tenant_bp.post("/save/<int:property_id>")
@login_required
@email_verified_required
@subscription_required
def save_property(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    saved = SavedProperty(user_id=current_user.id, property_id=prop.id)
    db.session.add(saved)
    try:
        db.session.commit()
        flash("Property saved.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Property is already saved.", "info")
    return redirect(request.referrer or url_for("properties.detail", property_id=property_id))


@tenant_bp.get("/saved")
@roles_required("tenant", "admin")
def saved_properties():
    saved = SavedProperty.query.filter_by(user_id=current_user.id).order_by(SavedProperty.saved_at.desc()).all()
    return render_template("tenant/saved.html", saved=saved)


@tenant_bp.route("/apply/<int:property_id>", methods=["GET", "POST"])
@roles_required("tenant", "admin")
@email_verified_required
@subscription_required
def apply(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    existing = RentalApplication.query.filter_by(property_id=property_id, applicant_id=current_user.id).first()
    if existing:
        flash("You already applied for this property.", "info")
        return redirect(url_for("tenant.dashboard"))

    if request.method == "POST":
        form = request.form
        application = RentalApplication(
            property_id=property_id,
            applicant_id=current_user.id,
            message=form.get("message"),
            monthly_income=parse_optional_float(form.get("monthly_income")),
            employment_status=form.get("employment_status"),
            employer_name=form.get("employer_name"),
            years_employed=parse_optional_float(form.get("years_employed")),
            has_pets=parse_bool(form.get("has_pets")),
            number_of_occupants=int(form.get("number_of_occupants") or 1),
            lease_term=int(form.get("lease_term") or 12),
        )
        move_in_date = form.get("move_in_date")
        if move_in_date:
            application.move_in_date = datetime.strptime(move_in_date, "%Y-%m-%d").date()
        db.session.add(application)
        db.session.commit()
        flash("Application submitted.", "success")
        return redirect(url_for("tenant.dashboard"))

    return render_template("tenant/apply.html", property=prop)
