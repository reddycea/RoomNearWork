from __future__ import annotations

from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from backend.rnw.extensions import db


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if current_user.role != role:
                if hasattr(current_user, "can_use_role") and current_user.can_use_role(role):
                    current_user.set_active_role(role)
                    db.session.commit()
                else:
                    abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def tenant_required(view):
    return role_required("tenant")(view)


def landlord_required(view):
    return role_required("landlord")(view)


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not getattr(current_user, "is_admin", False):
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def email_verified_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        if not getattr(current_user, "email_verified", False):
            flash("Please verify your email before continuing.", "warning")
            return redirect(url_for("auth.verify_email_notice"))
        return view(*args, **kwargs)
    return wrapped


def two_factor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if getattr(current_user, "is_admin", False) and not getattr(current_user, "two_factor_enabled", False):
            flash("Please enable admin two-factor authentication before continuing.", "warning")
            return redirect(url_for("auth.two_factor_setup"))
        return view(*args, **kwargs)
    return wrapped
