from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from ..extensions import db
from ..models import LandlordVerification, Property, RentalApplication
from ..services.email_service import send_email
from ..services.subscription_service import landlord_can_create_listing
from ..utils.decorators import email_verified_required, roles_required
from ..utils.security import save_private_document

landlord_bp = Blueprint("landlord", __name__, url_prefix="/landlord")


@landlord_bp.get("/dashboard")
@roles_required("landlord", "admin")
def dashboard():
    properties = Property.query.filter_by(landlord_id=current_user.id).order_by(Property.created_at.desc()).all()
    applications = (
        RentalApplication.query.join(Property)
        .filter(Property.landlord_id == current_user.id)
        .order_by(RentalApplication.created_at.desc())
        .limit(10)
        .all()
    )
    can_create, listing_limit, listing_count = landlord_can_create_listing(current_user)
    stats = {
        "listing_count": listing_count,
        "listing_limit": listing_limit,
        "can_create_listing": can_create,
        "pending_applications": sum(1 for item in applications if item.status == "pending"),
        "views": sum((prop.view_count or 0) for prop in properties),
    }
    return render_template("landlord/dashboard.html", properties=properties, applications=applications, stats=stats)


@landlord_bp.get("/applications")
@roles_required("landlord", "admin")
def applications():
    apps = (
        RentalApplication.query.join(Property)
        .filter(Property.landlord_id == current_user.id)
        .order_by(RentalApplication.created_at.desc())
        .all()
    )
    return render_template("landlord/applications.html", applications=apps)


@landlord_bp.post("/applications/<int:application_id>/<action>")
@roles_required("landlord", "admin")
def process_application(application_id: int, action: str):
    application = db.session.get(RentalApplication, application_id) or abort(404)
    if application.property.landlord_id != current_user.id and current_user.role != "admin":
        abort(403)
    if action == "approve":
        application.approve()
        subject = "RNW application approved"
        body = f"Your application for {application.property.title} was approved."
    elif action == "reject":
        application.reject()
        subject = "RNW application update"
        body = f"Your application for {application.property.title} was not approved."
    else:
        abort(400)
    db.session.commit()
    send_email(subject, [application.applicant.email], body)
    flash(f"Application {application.status}.", "success")
    return redirect(url_for("landlord.applications"))


@landlord_bp.route("/verification", methods=["GET", "POST"])
@roles_required("landlord", "admin")
@email_verified_required
def verification():
    existing = LandlordVerification.query.filter_by(user_id=current_user.id).first()
    if request.method == "POST":
        id_doc = request.files.get("id_document")
        proof = request.files.get("proof_of_address")
        if not id_doc or not proof:
            flash("ID document and proof of address are required.", "danger")
            return render_template("landlord/verification.html", verification=existing), 400
        verification = existing or LandlordVerification(user_id=current_user.id, id_document_url="", proof_of_address_url="")
        verification.id_document_url = save_private_document(id_doc, "verification")
        verification.proof_of_address_url = save_private_document(proof, "verification")
        if request.files.get("tax_clearance"):
            verification.tax_clearance_url = save_private_document(request.files["tax_clearance"], "verification")
        if request.files.get("business_registration"):
            verification.business_registration_url = save_private_document(request.files["business_registration"], "verification")
        verification.status = "pending"
        verification.verified_at = None
        db.session.add(verification)
        db.session.commit()
        flash("Verification submitted for review. Documents are stored privately for admin review.", "success")
        return redirect(url_for("landlord.dashboard"))
    return render_template("landlord/verification.html", verification=existing)
