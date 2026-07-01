from __future__ import annotations

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from backend.rnw.extensions import db
from backend.rnw.models import LandlordApplication
from backend.rnw.services.audit_service import log_action
from backend.rnw.utils.security import clean_user_text, password_is_strong

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


@profile_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    pending_landlord_application = (
        LandlordApplication.query
        .filter_by(applicant_id=current_user.id, status="pending")
        .order_by(LandlordApplication.created_at.desc())
        .first()
    )

    latest_landlord_application = (
        LandlordApplication.query
        .filter_by(applicant_id=current_user.id)
        .order_by(LandlordApplication.created_at.desc())
        .first()
    )

    if request.method == "POST":
        full_name = clean_user_text(request.form.get("full_name"), 160)
        phone = clean_user_text(request.form.get("phone"), 40)

        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("profile.index"))

        current_user.full_name = full_name
        current_user.phone = phone

        log_action("profile_updated", "User", current_user.id)
        db.session.commit()

        flash("Profile updated.", "success")
        return redirect(url_for("profile.index"))

    return render_template(
        "profile/index.html",
        pending_landlord_application=pending_landlord_application,
        latest_landlord_application=latest_landlord_application,
    )


@profile_bp.post("/change-password")
@login_required
def change_password():
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("profile.index"))

    if new_password != confirm_password:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("profile.index"))

    if not password_is_strong(new_password):
        flash("Use at least 8 characters with uppercase, lowercase and a number.", "danger")
        return redirect(url_for("profile.index"))

    current_user.set_password(new_password)

    log_action("password_changed", "User", current_user.id)
    db.session.commit()

    flash("Password changed successfully.", "success")
    return redirect(url_for("profile.index"))


@profile.post("/apply-landlord") if False else profile_bp.post("/apply-landlord")
@login_required
def apply_landlord():
    if current_user.can_act_as_landlord:
        flash("You are already approved as a landlord.", "info")
        return redirect(url_for("profile.index"))

    existing_pending = LandlordApplication.query.filter_by(
        applicant_id=current_user.id,
        status="pending",
    ).first()

    if existing_pending:
        flash("Your landlord application is already pending admin approval.", "info")
        return redirect(url_for("profile.index"))

    message = clean_user_text(request.form.get("message"), 3000)

    application = LandlordApplication(
        applicant_id=current_user.id,
        message=message,
        status="pending",
    )

    db.session.add(application)
    db.session.flush()

    log_action("landlord_application_submitted", "LandlordApplication", application.id)
    db.session.commit()

    flash("Your landlord application has been submitted for admin approval.", "success")
    return redirect(url_for("profile.index"))


@profile_bp.post("/switch-role/<role>")
@login_required
def switch_role(role: str):
    if role not in {"tenant", "landlord"}:
        abort(404)

    if not current_user.can_use_role(role):
        flash("That role is not available for your account yet.", "danger")
        return redirect(url_for("profile.index"))

    current_user.set_active_role(role)

    log_action("role_switched", "User", current_user.id, {"role": role})
    db.session.commit()

    flash(f"You are now using Room Near Work as a {role}.", "success")

    if role == "landlord":
        return redirect(url_for("landlord.dashboard"))

    return redirect(url_for("tenant.dashboard"))
