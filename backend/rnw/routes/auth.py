from __future__ import annotations

import re
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from backend.rnw.extensions import db, limiter
from backend.rnw.models import User
from backend.rnw.services.audit_service import log_action
from backend.rnw.services.auth_service import is_locked, record_failed_login, record_successful_login
from backend.rnw.services.auth_token_service import reset_password_with_token, send_password_reset_email, send_verification_email, verify_email_token
from backend.rnw.utils.security import clean_user_text, password_is_strong

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per minute")
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        first_name = clean_user_text(request.form.get("first_name"), 80)
        last_name = clean_user_text(request.form.get("last_name"), 80)
        phone = clean_user_text(request.form.get("phone"), 40)
        id_number = request.form.get("id_number", "").strip()
        reference_code = clean_user_text(request.form.get("reference_code"), 80)
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        phone = re.sub(r"\s+", "", phone)
        id_number = re.sub(r"\s+", "", id_number)

        if not first_name or not last_name:
            flash("First name and last name are required.", "danger")
            return render_template("auth/register.html")

        if not email:
            flash("Email is required.", "danger")
            return render_template("auth/register.html")

        if not phone:
            flash("Phone number is required.", "danger")
            return render_template("auth/register.html")

        if not id_number:
            flash("ID number is required.", "danger")
            return render_template("auth/register.html")

        if not id_number.isdigit():
            flash("ID number must contain numbers only.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if not password_is_strong(password):
            flash("Use at least 8 characters with uppercase, lowercase and a number.", "danger")
            return render_template("auth/register.html")

        full_name = f"{first_name} {last_name}".strip()

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            phone=phone,
            id_number=id_number,
            reference_code=reference_code or None,
            role="tenant",
            can_act_as_tenant=True,
            can_act_as_landlord=False,
        )

        user.set_password(password)
        db.session.add(user)

        try:
            db.session.flush()
            verification_url = send_verification_email(user)
            log_action("user_registered", "User", user.id)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email or ID number already exists.", "danger")
            return render_template("auth/register.html")

        login_user(user)
        flash("Account created. Check your email to verify your account.", "success")

        if verification_url:
            flash(f"Development verification link: {verification_url}", "info")

        return redirect(url_for("auth.choose_role"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).one_or_none()
        if user and is_locked(user):
            flash("Account locked temporarily after failed login attempts.", "danger")
            return render_template("auth/login.html")
        if not user or not user.check_password(password):
            record_failed_login(user)
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")
        login_user(user, remember=bool(request.form.get("remember")))
        record_successful_login(user)
        log_action("login_success", "User", user.id)
        db.session.commit()
        return redirect(url_for("main.index"))
    return render_template("auth/login.html")


@auth_bp.post("/logout")
@login_required
def logout():
    log_action("logout", "User", current_user.id)
    db.session.commit()
    logout_user()
    flash("Signed out.", "success")
    return redirect(url_for("main.index"))


@auth_bp.route("/choose-role", methods=["GET", "POST"])
@login_required
def choose_role():
    if request.method == "POST":
        role = request.form.get("role", "tenant")
        try:
            current_user.set_active_role(role)
        except ValueError:
            flash("That role is not available for your account.", "danger")
            return render_template("auth/choose_role.html")
        log_action("role_chosen", "User", current_user.id, {"role": role})
        db.session.commit()
        return redirect(url_for("tenant.dashboard") if role == "tenant" else url_for("landlord.dashboard"))
    return render_template("auth/choose_role.html")


@auth_bp.get("/verify-email-notice")
@login_required
def verify_email_notice():
    return render_template("auth/verify_email_notice.html")


@auth_bp.post("/resend-verification")
@login_required
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.email_verified:
        flash("Your email is already verified.", "info")
        return redirect(url_for("main.index"))
    link = send_verification_email(current_user)
    log_action("email_verification_resent", "User", current_user.id)
    db.session.commit()
    flash("Verification email sent.", "success")
    if link:
        flash(f"Development verification link: {link}", "info")
    return redirect(url_for("auth.verify_email_notice"))


@auth_bp.get("/verify-email/<token>")
def verify_email(token: str):
    user = verify_email_token(token)
    if not user:
        flash("That verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.login"))
    log_action("email_verified", "User", user.id)
    db.session.commit()
    flash("Email verified. You can now use all Room Near Work features.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).one_or_none()
        link = None
        if user:
            link = send_password_reset_email(user)
            log_action("password_reset_requested", "User", user.id)
            db.session.commit()
        flash("If an account exists for that email, a reset link has been sent.", "success")
        if link:
            flash(f"Development reset link: {link}", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def reset_password(token: str):
    if request.method == "POST":
        password = request.form.get("password", "")
        if not password_is_strong(password):
            flash("Use at least 8 characters with uppercase, lowercase and a number.", "danger")
            return render_template("auth/reset_password.html")
        user = reset_password_with_token(token, password)
        if not user:
            db.session.rollback()
            flash("That reset link is invalid or expired.", "danger")
            return redirect(url_for("auth.forgot_password"))
        log_action("password_reset_completed", "User", user.id)
        db.session.commit()
        flash("Password updated. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html")

