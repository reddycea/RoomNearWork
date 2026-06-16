from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required


def roles_required(*roles: str):
    """Require login and one of the listed roles."""
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def subscription_required(func):
    """Require an active subscription for tenant/landlord SaaS actions."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role == "admin" or current_user.has_active_subscription():
            return func(*args, **kwargs)
        flash("Please activate your RNW monthly subscription before using this feature.", "info")
        return redirect(url_for("billing.plans"))
    return wrapper


def email_verified_required(func):
    """Require verified email only when EMAIL_VERIFICATION_REQUIRED is enabled."""
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        from flask import current_app
        if not current_app.config.get("EMAIL_VERIFICATION_REQUIRED", False):
            return func(*args, **kwargs)
        if current_user.email_verified or current_user.role == "admin":
            return func(*args, **kwargs)
        flash("Please verify your email address before using this feature.", "warning")
        return redirect(url_for("auth.resend_verification"))
    return wrapper
