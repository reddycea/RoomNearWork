from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from backend.rnw.extensions import db, limiter
from backend.rnw.models import ListingReport, Property, SupportTicket
from backend.rnw.utils.security import clean_user_text

trust_bp = Blueprint("trust", __name__, url_prefix="/trust")


@trust_bp.route("/support", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def support():
    if request.method == "POST":
        ticket = SupportTicket(
            user_id=current_user.id if current_user.is_authenticated else None,
            email=request.form.get("email") or (current_user.email if current_user.is_authenticated else ""),
            subject=clean_user_text(request.form.get("subject"), 200),
            message=clean_user_text(request.form.get("message"), 3000),
        )
        db.session.add(ticket)
        db.session.commit()
        flash("Support ticket created.", "success")
        return redirect(url_for("trust.ticket_status", ticket_id=ticket.id, token=ticket.public_token))
    return render_template("support/new.html")


@trust_bp.get("/support/<int:ticket_id>")
def ticket_status(ticket_id: int):
    ticket = db.session.get(SupportTicket, ticket_id) or abort(404)
    if ticket.user_id:
        if not current_user.is_authenticated or (current_user.id != ticket.user_id and not current_user.is_admin):
            abort(403)
    elif request.args.get("token") != ticket.public_token:
        abort(403)
    return render_template("support/status.html", ticket=ticket)


@trust_bp.route("/report-listing/<int:property_id>", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def report_listing(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if request.method == "POST":
        report = ListingReport(
            property_id=property_id,
            reporter_id=current_user.id if current_user.is_authenticated else None,
            reason=clean_user_text(request.form.get("reason"), 120),
            details=clean_user_text(request.form.get("details"), 2000),
        )
        db.session.add(report)
        db.session.commit()
        flash("Report submitted. Thank you for helping keep RNW safe.", "success")
        return redirect(url_for("properties.detail", property_id=property_id))
    return render_template("trust/report_listing.html", property=property_)
