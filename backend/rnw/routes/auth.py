from __future__ import annotations

from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from ..extensions import db, limiter
from ..models import User
from ..services.auth_service import (
    TOKEN_PURPOSE_EMAIL_VERIFY,
    TOKEN_PURPOSE_PASSWORD_RESET,
    consume_auth_token,
    is_login_locked,
    password_strength_errors,
    record_login_attempt,
    send_password_reset_email,
    send_verification_email,
)
from ..utils.validators import PROVINCES, validate_sa_id

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("tenant.dashboard" if current_user.role == "tenant" else "landlord.dashboard" if current_user.role == "landlord" else "admin.dashboard"))

    if request.method == "POST":
        form = request.form
        email = form.get("email", "").strip().lower()
        password = form.get("password", "")
        confirm = form.get("confirm_password", "")
        role = form.get("role", "tenant")
        id_number = form.get("id_number") or None

        errors = []
        if role not in {"tenant", "landlord"}:
            errors.append("Invalid account type.")
        errors.extend(password_strength_errors(password))
        if password != confirm:
            errors.append("Passwords do not match.")
        if id_number and not validate_sa_id(id_number):
            errors.append("Invalid South African ID number.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html", provinces=PROVINCES), 400

        user = User(
            email=email,
            first_name=form.get("first_name", "").strip(),
            last_name=form.get("last_name", "").strip(),
            phone=form.get("phone", "").strip(),
            id_number=id_number,
            role=role,
            province=form.get("province"),
        )
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.flush()
            send_verification_email(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("This email or ID number is already registered.", "danger")
            return render_template("auth/register.html", provinces=PROVINCES), 409

        login_user(user)
        flash("Account created successfully. Check your email to verify your address.", "success")
        return redirect(url_for("landlord.dashboard" if role == "landlord" else "tenant.dashboard"))

    return render_template("auth/register.html", provinces=PROVINCES)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

        if is_login_locked(email, ip_address):
            flash("Too many failed login attempts. Try again later or reset your password.", "danger")
            return render_template("auth/login.html"), 429

        user = User.query.filter_by(email=email).first()
        ok = bool(user and user.check_password(password) and user.is_active)
        record_login_attempt(email, ip_address, ok)
        if not ok:
            db.session.commit()
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html"), 401

        from flask import current_app
        if current_app.config.get("EMAIL_VERIFICATION_REQUIRED", False) and not user.email_verified:
            db.session.commit()
            flash("Please verify your email before logging in.", "warning")
            return redirect(url_for("auth.resend_verification"))

        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user, remember=bool(request.form.get("remember")))
        flash("Welcome back.", "success")
        return redirect(url_for("admin.dashboard" if user.role == "admin" else "landlord.dashboard" if user.role == "landlord" else "tenant.dashboard"))

    return render_template("auth/login.html")


@auth_bp.get("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))


@auth_bp.get("/verify-email/<token>")
def verify_email(token: str):
    user = consume_auth_token(token, TOKEN_PURPOSE_EMAIL_VERIFY)
    if not user:
        flash("This email verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.login"))
    user.email_verified_at = datetime.utcnow()
    db.session.commit()
    flash("Email address verified successfully.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and not user.email_verified:
            send_verification_email(user)
            db.session.commit()
        flash("If the address exists and is not verified, a verification email has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/resend_verification.html")


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user and user.is_active:
            send_password_reset_email(user)
            db.session.commit()
        flash("If that email exists, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token: str):
    if request.method == "POST":
        user = consume_auth_token(token, TOKEN_PURPOSE_PASSWORD_RESET)
        if not user:
            flash("This password reset link is invalid or expired.", "danger")
            return redirect(url_for("auth.forgot_password"))
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        errors = password_strength_errors(password)
        if password != confirm:
            errors.append("Passwords do not match.")
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/reset_password.html", token=token), 400
        user.set_password(password)
        db.session.commit()
        flash("Password updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/reset_password.html", token=token)


@auth_bp.post("/api/token")
@limiter.limit("10 per minute")
def api_token():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).lower()
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if is_login_locked(email, ip_address):
        return jsonify({"message": "Too many failed login attempts"}), 429
    user = User.query.filter_by(email=email).first()
    ok = bool(user and user.check_password(data.get("password", "")) and user.is_active)
    record_login_attempt(email, ip_address, ok)
    if not ok:
        db.session.commit()
        return jsonify({"message": "Invalid credentials"}), 401
    user.last_login = datetime.utcnow()
    db.session.commit()
    identity = str(user.id)
    return jsonify({
        "access_token": create_access_token(identity=identity, additional_claims={"role": user.role}),
        "refresh_token": create_refresh_token(identity=identity),
        "user": user.to_dict(),
    })


@auth_bp.post("/api/refresh")
@jwt_required(refresh=True)
def refresh_token():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    return jsonify({"access_token": create_access_token(identity=identity, additional_claims={"role": user.role if user else None})})
