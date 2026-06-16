from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import ListingReport, Property, PropertyReview, RentalApplication, SupportTicket
from ..services.email_service import send_support_notification
from ..utils.decorators import email_verified_required, roles_required
from ..utils.validators import parse_optional_int

trust_bp = Blueprint("trust", __name__)

REPORT_REASONS = [
    "Fake or misleading listing",
    "Suspicious landlord",
    "Wrong location or price",
    "Unsafe property",
    "Discrimination or harassment",
    "Other",
]

SUPPORT_CATEGORIES = ["general", "billing", "account", "landlord verification", "safety", "technical"]


@trust_bp.route("/support", methods=["GET", "POST"])
def support():
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip() or (current_user.full_name if current_user.is_authenticated else "RNW user")
        email = form.get("email", "").strip() or (current_user.email if current_user.is_authenticated else "")
        subject = form.get("subject", "").strip()
        message = form.get("message", "").strip()
        category = form.get("category", "general").strip().lower()
        if not email or not subject or not message:
            flash("Please provide your email, subject, and message.", "danger")
            return render_template("support/new.html", categories=SUPPORT_CATEGORIES)
        if category not in SUPPORT_CATEGORIES:
            category = "general"
        ticket = SupportTicket(
            user_id=current_user.id if current_user.is_authenticated else None,
            name=name[:120],
            email=email[:120],
            category=category,
            subject=subject[:160],
            message=message,
            priority="high" if category in {"billing", "safety"} else "normal",
        )
        db.session.add(ticket)
        db.session.commit()
        send_support_notification(ticket)
        flash(f"Support ticket #{ticket.id} created. We will respond by email.", "success")
        return redirect(url_for("trust.support_status", ticket_id=ticket.id))
    return render_template("support/new.html", categories=SUPPORT_CATEGORIES)


@trust_bp.get("/support/<int:ticket_id>")
def support_status(ticket_id: int):
    ticket = db.session.get(SupportTicket, ticket_id) or abort(404)
    if ticket.user_id and (not current_user.is_authenticated or current_user.id not in {ticket.user_id} and current_user.role != "admin"):
        abort(403)
    return render_template("support/status.html", ticket=ticket)


@trust_bp.route("/properties/<int:property_id>/report", methods=["GET", "POST"])
def report_listing(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if request.method == "POST":
        form = request.form
        report = ListingReport(
            property_id=prop.id,
            reporter_id=current_user.id if current_user.is_authenticated else None,
            reporter_name=form.get("reporter_name", "").strip()[:120] or (current_user.full_name if current_user.is_authenticated else None),
            reporter_email=form.get("reporter_email", "").strip()[:120] or (current_user.email if current_user.is_authenticated else None),
            reason=form.get("reason", "Other")[:80],
            message=form.get("message", "").strip(),
        )
        if not report.message:
            flash("Please explain the issue so the admin team can investigate.", "danger")
            return render_template("trust/report_listing.html", property=prop, reasons=REPORT_REASONS)
        db.session.add(report)
        db.session.commit()
        flash("Thank you. The listing has been reported to RNW safety moderation.", "success")
        return redirect(url_for("properties.detail", property_id=prop.id))
    return render_template("trust/report_listing.html", property=prop, reasons=REPORT_REASONS)


@trust_bp.route("/properties/<int:property_id>/reviews/new", methods=["GET", "POST"])
@roles_required("tenant", "admin")
@email_verified_required
def create_review(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if prop.status != "approved" and current_user.role != "admin":
        abort(404)
    application = RentalApplication.query.filter_by(property_id=prop.id, applicant_id=current_user.id, status="approved").first()
    if current_user.role != "admin" and not application:
        flash("Only tenants with an approved application can review this property.", "warning")
        return redirect(url_for("properties.detail", property_id=prop.id))
    existing = PropertyReview.query.filter_by(property_id=prop.id, reviewer_id=current_user.id).first()
    if existing:
        flash("You have already reviewed this property.", "info")
        return redirect(url_for("properties.detail", property_id=prop.id))
    if request.method == "POST":
        rating = parse_optional_int(request.form.get("rating")) or 0
        title = request.form.get("title", "").strip()
        comment = request.form.get("comment", "").strip()
        if rating < 1 or rating > 5 or not title or not comment:
            flash("Please provide a rating from 1 to 5, a title, and a review comment.", "danger")
            return render_template("trust/review_form.html", property=prop)
        review = PropertyReview(
            property_id=prop.id,
            reviewer_id=current_user.id,
            landlord_id=prop.landlord_id,
            rental_application_id=application.id if application else None,
            rating=rating,
            title=title[:120],
            comment=comment,
            status="approved" if current_user.role == "admin" else "pending",
        )
        db.session.add(review)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("You have already reviewed this property.", "info")
        else:
            flash("Review submitted. It will appear publicly after moderation.", "success")
        return redirect(url_for("properties.detail", property_id=prop.id))
    return render_template("trust/review_form.html", property=prop)


@trust_bp.post("/reviews/<int:review_id>/respond")
@roles_required("landlord", "admin")
def landlord_review_response(review_id: int):
    review = db.session.get(PropertyReview, review_id) or abort(404)
    if current_user.role != "admin" and review.landlord_id != current_user.id:
        abort(403)
    response = request.form.get("response", "").strip()
    if not response:
        flash("Please write a response before submitting.", "danger")
        return redirect(url_for("properties.detail", property_id=review.property_id))
    review.landlord_response = response
    from datetime import datetime
    review.landlord_responded_at = datetime.utcnow()
    db.session.commit()
    flash("Landlord response added.", "success")
    return redirect(url_for("properties.detail", property_id=review.property_id))
