from __future__ import annotations

from datetime import datetime, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from backend.rnw.extensions import db, limiter
from backend.rnw.models import ConversationMessage, ConversationThread, Property, RentalApplication, RentalReview, SavedSearch, ViewingAppointment
from backend.rnw.services.audit_service import log_action
from backend.rnw.services.google_maps_service import geocode_address, geocode_place_id
from backend.rnw.utils.decorators import admin_required, landlord_required, tenant_required
from backend.rnw.utils.security import clean_user_text

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/marketplace")


@marketplace_bp.post("/switch-role")
@login_required
@limiter.limit("20 per hour")
def switch_role():
    role = request.form.get("role", "tenant")
    try:
        current_user.set_active_role(role)
    except ValueError:
        abort(403)
    log_action("role_switched", "User", current_user.id, {"role": role})
    db.session.commit()
    flash(f"Now acting as {role.title()}.", "success")
    return redirect(request.referrer or url_for("main.index"))


@marketplace_bp.route("/saved-searches", methods=["GET", "POST"])
@login_required
@tenant_required
@limiter.limit("10 per hour", methods=["POST"])
def saved_searches():
    if request.method == "POST":
        workplace_address = clean_user_text(request.form.get("workplace_address"), 500)
        workplace_place_id = request.form.get("workplace_place_id", "").strip()
        resolved = geocode_place_id(workplace_place_id, workplace_address) if workplace_place_id else (geocode_address(workplace_address) if workplace_address else None)
        saved = SavedSearch(
            user_id=current_user.id,
            name=clean_user_text(request.form.get("name"), 120) or "My search",
            city=clean_user_text(request.form.get("city"), 120) or (resolved.city if resolved else None),
            province=clean_user_text(request.form.get("province"), 120) or (resolved.province if resolved else None),
            max_rent=request.form.get("max_rent", type=int),
            min_bedrooms=request.form.get("min_bedrooms", type=int),
            furnished=True if request.form.get("furnished") else None,
            pets_allowed=True if request.form.get("pets_allowed") else None,
            transport_access=True if request.form.get("transport_access") else None,
            workplace_address=workplace_address,
            workplace_formatted_address=resolved.formatted_address if resolved else None,
            workplace_place_id=resolved.place_id if resolved else workplace_place_id or None,
            workplace_area=resolved.area_label if resolved else None,
            workplace_latitude=resolved.latitude if resolved else None,
            workplace_longitude=resolved.longitude if resolved else None,
            travel_mode=request.form.get("travel_mode", "all"),
            max_distance_km=request.form.get("max_distance_km", type=float),
            max_travel_minutes=request.form.get("max_travel_minutes", type=int),
            alerts_enabled=bool(request.form.get("alerts_enabled", True)),
        )
        db.session.add(saved)
        try:
            log_action("saved_search_created", "SavedSearch", None, {"name": saved.name})
            db.session.commit()
            flash("Saved search created.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("You already have a saved search with that name.", "danger")
        return redirect(url_for("marketplace.saved_searches"))
    searches = SavedSearch.query.filter_by(user_id=current_user.id).order_by(SavedSearch.created_at.desc()).all()
    return render_template("marketplace/saved_searches.html", searches=searches)


@marketplace_bp.get("/messages")
@login_required
def messages():
    threads = ConversationThread.query.filter((ConversationThread.tenant_id == current_user.id) | (ConversationThread.landlord_id == current_user.id)).order_by(ConversationThread.last_message_at.desc().nullslast()).all()
    return render_template("marketplace/messages.html", threads=threads)


@marketplace_bp.post("/messages/start/<int:property_id>")
@login_required
@tenant_required
@limiter.limit("20 per hour")
def start_message(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if property_.landlord_id == current_user.id:
        abort(403)
    thread = ConversationThread.query.filter_by(property_id=property_id, tenant_id=current_user.id, landlord_id=property_.landlord_id).one_or_none()
    if not thread:
        thread = ConversationThread(property_id=property_id, tenant_id=current_user.id, landlord_id=property_.landlord_id, last_message_at=datetime.utcnow())
        db.session.add(thread)
        db.session.flush()
    body = clean_user_text(request.form.get("body"), 2000) or "Hi, I am interested in this listing."
    db.session.add(ConversationMessage(thread_id=thread.id, sender_id=current_user.id, body=body))
    thread.last_message_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for("marketplace.thread", thread_id=thread.id))


@marketplace_bp.route("/messages/<int:thread_id>", methods=["GET", "POST"])
@login_required
def thread(thread_id: int):
    thread = db.session.get(ConversationThread, thread_id) or abort(404)
    if current_user.id not in {thread.tenant_id, thread.landlord_id} and not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        body = clean_user_text(request.form.get("body"), 2000)
        if body:
            db.session.add(ConversationMessage(thread_id=thread.id, sender_id=current_user.id, body=body))
            thread.last_message_at = datetime.utcnow()
            db.session.commit()
        return redirect(url_for("marketplace.thread", thread_id=thread.id))
    return render_template("marketplace/thread.html", thread=thread)


@marketplace_bp.route("/viewings/request/<int:property_id>", methods=["GET", "POST"])
@login_required
@tenant_required
@limiter.limit("10 per hour", methods=["POST"])
def request_viewing(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if request.method == "POST":
        requested_start = datetime.fromisoformat(request.form.get("requested_start"))
        appointment = ViewingAppointment(
            property_id=property_.id,
            tenant_id=current_user.id,
            landlord_id=property_.landlord_id,
            requested_start=requested_start,
            requested_end=requested_start + timedelta(minutes=30),
            tenant_note=clean_user_text(request.form.get("tenant_note"), 1000),
        )
        db.session.add(appointment)
        log_action("viewing_requested", "ViewingAppointment", None, {"property_id": property_.id})
        db.session.commit()
        flash("Viewing request sent.", "success")
        return redirect(url_for("marketplace.viewings"))
    return render_template("marketplace/request_viewing.html", property=property_)


@marketplace_bp.get("/viewings")
@login_required
def viewings():
    query = ViewingAppointment.query
    if current_user.role == "landlord":
        query = query.filter_by(landlord_id=current_user.id)
    else:
        query = query.filter_by(tenant_id=current_user.id)
    appointments = query.order_by(ViewingAppointment.requested_start.desc()).all()
    return render_template("marketplace/viewings.html", appointments=appointments)


@marketplace_bp.post("/viewings/<int:appointment_id>/<action>")
@login_required
@landlord_required
def viewing_action(appointment_id: int, action: str):
    if action not in {"approved", "rejected"}:
        abort(404)
    appointment = db.session.execute(db.select(ViewingAppointment).where(ViewingAppointment.id == appointment_id).with_for_update()).scalar_one_or_none()
    if not appointment or appointment.landlord_id != current_user.id:
        abort(404)
    appointment.status = action
    appointment.landlord_note = clean_user_text(request.form.get("landlord_note"), 1000)
    log_action(f"viewing_{action}", "ViewingAppointment", appointment.id)
    db.session.commit()
    flash(f"Viewing {action}.", "success")
    return redirect(url_for("marketplace.viewings"))


@marketplace_bp.post("/properties/<int:property_id>/renew")
@login_required
@landlord_required
def renew_property(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if property_.landlord_id != current_user.id:
        abort(403)
    property_.renew()
    db.session.commit()
    flash("Listing renewed.", "success")
    return redirect(url_for("landlord.dashboard"))


@marketplace_bp.get("/admin/moderation")
@login_required
@admin_required
def admin_moderation():
    pending = Property.query.filter_by(status="under_review").order_by(Property.created_at.asc()).all()
    return render_template("marketplace/admin_moderation.html", pending=pending)



def _rating_value(name: str) -> int | None:
    value = request.form.get(name, type=int)
    if value is None:
        return None
    return max(1, min(5, value))


def _can_review_property(property_: Property) -> bool:
    if not current_user.is_authenticated or current_user.role != "tenant" or property_.landlord_id == current_user.id:
        return False
    has_application = RentalApplication.query.filter_by(property_id=property_.id, applicant_id=current_user.id).first() is not None
    has_viewing = ViewingAppointment.query.filter_by(property_id=property_.id, tenant_id=current_user.id).filter(ViewingAppointment.status.in_(["approved", "completed"])).first() is not None
    return has_application or has_viewing


@marketplace_bp.route("/reviews/property/<int:property_id>/new", methods=["GET", "POST"])
@login_required
@tenant_required
@limiter.limit("5 per hour", methods=["POST"])
def new_review(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if not _can_review_property(property_):
        flash("You can review this rental after applying or after an approved viewing.", "warning")
        return redirect(url_for("properties.detail", property_id=property_.id))
    existing = RentalReview.query.filter_by(property_id=property_.id, tenant_id=current_user.id).one_or_none()
    if existing and request.method == "GET":
        return render_template("marketplace/review_form.html", property=property_, review=existing)
    if request.method == "POST":
        review = existing or RentalReview(property_id=property_.id, tenant_id=current_user.id, landlord_id=property_.landlord_id)
        review.rating = _rating_value("rating") or 5
        review.accuracy_rating = _rating_value("accuracy_rating")
        review.safety_rating = _rating_value("safety_rating")
        review.commute_rating = _rating_value("commute_rating")
        review.landlord_communication_rating = _rating_value("landlord_communication_rating")
        review.title = clean_user_text(request.form.get("title"), 140) or "Tenant review"
        review.comment = clean_user_text(request.form.get("comment"), 3000)
        review.status = "pending"
        review.admin_note = None
        if not review.comment:
            flash("Please add a short review comment.", "danger")
            return render_template("marketplace/review_form.html", property=property_, review=review)
        db.session.add(review)
        try:
            log_action("rental_review_submitted", "RentalReview", None, {"property_id": property_.id})
            db.session.commit()
            flash("Review submitted for moderation. Thank you for helping other tenants.", "success")
        except IntegrityError:
            db.session.rollback()
            flash("You already reviewed this rental. Open your existing review to edit it.", "info")
        return redirect(url_for("properties.detail", property_id=property_.id))
    return render_template("marketplace/review_form.html", property=property_, review=existing)


@marketplace_bp.post("/reviews/<int:review_id>/delete")
@login_required
def delete_review(review_id: int):
    review = db.session.get(RentalReview, review_id) or abort(404)
    if review.tenant_id != current_user.id and not current_user.is_admin:
        abort(403)
    property_id = review.property_id
    db.session.delete(review)
    log_action("rental_review_deleted", "RentalReview", review.id)
    db.session.commit()
    flash("Review removed.", "success")
    return redirect(url_for("properties.detail", property_id=property_id))
