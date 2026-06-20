from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.rnw.extensions import db
from backend.rnw.models import ListingReport, Property, PropertyAsset, SupportTicket, User
from backend.rnw.services.audit_service import log_action
from backend.rnw.utils.decorators import admin_required, two_factor_required
from backend.rnw.utils.security import clean_user_text

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@login_required
@admin_required
@two_factor_required
def dashboard():
    counts = {
        "users": User.query.count(),
        "pending_listings": Property.query.filter_by(status="under_review").count(),
        "pending_documents": PropertyAsset.query.filter(PropertyAsset.is_private.is_(True), PropertyAsset.review_status == "pending").count(),
        "reports": ListingReport.query.filter_by(status="open").count(),
        "tickets": SupportTicket.query.filter_by(status="open").count(),
    }
    return render_template("admin/dashboard.html", counts=counts)


@admin_bp.get("/verifications")
@login_required
@admin_required
@two_factor_required
def verifications():
    listings = Property.query.filter(Property.status.in_(["under_review", "rejected"])).order_by(Property.created_at.asc()).all()
    documents = PropertyAsset.query.filter(PropertyAsset.is_private.is_(True)).order_by(PropertyAsset.created_at.desc()).all()
    return render_template("admin/verifications.html", listings=listings, documents=documents)


@admin_bp.post("/properties/<int:property_id>/<action>")
@login_required
@admin_required
@two_factor_required
def moderate_property(property_id: int, action: str):
    if action not in {"approve", "reject"}:
        abort(404)
    prop = db.session.get(Property, property_id) or abort(404)
    note = clean_user_text(request.form.get("note"), 1000)
    if action == "approve":
        prop.status = "available"
        prop.is_active = True
        prop.listing_verified = prop.documents_approved()
        prop.verified_at = datetime.utcnow() if prop.listing_verified else None
        prop.verified_by_id = current_user.id if prop.listing_verified else None
        prop.status_reason = None
    else:
        prop.status = "rejected"
        prop.is_active = False
        prop.status_reason = note or "Rejected by admin."
    log_action(f"listing_{action}d", "Property", prop.id, {"note": note})
    db.session.commit()
    flash(f"Listing {action}d.", "success")
    return redirect(url_for("admin.verifications"))


@admin_bp.post("/assets/<int:asset_id>/<action>")
@login_required
@admin_required
@two_factor_required
def moderate_asset(asset_id: int, action: str):
    if action not in {"approve", "reject"}:
        abort(404)
    asset = db.session.get(PropertyAsset, asset_id) or abort(404)
    asset.review_status = "approved" if action == "approve" else "rejected"
    asset.review_note = clean_user_text(request.form.get("note"), 1000)
    asset.reviewed_by_id = current_user.id
    asset.reviewed_at = datetime.utcnow()
    log_action(f"document_{action}d", "PropertyAsset", asset.id, {"note": asset.review_note})
    db.session.commit()
    flash(f"Document {action}d.", "success")
    return redirect(url_for("admin.verifications"))
