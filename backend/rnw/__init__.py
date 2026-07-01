from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import click
from flask import Flask, render_template
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import config_by_name
from .extensions import cache, csrf, db, jwt, limiter, login_manager, mail, migrate, talisman


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    config_name = config_name or app.config.get("ENV") or "default"
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    app.config["UPLOAD_FOLDER_PATH"].mkdir(parents=True, exist_ok=True)

    setup_logging(app)
    register_proxy(app)
    register_extensions(app)
    register_security(app)
    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)
    return app


def register_proxy(app: Flask) -> None:
    if not app.config.get("PROXY_FIX_ENABLED"):
        return
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=app.config.get("PROXY_FIX_X_FOR", 1),
        x_proto=app.config.get("PROXY_FIX_X_PROTO", 1),
        x_host=app.config.get("PROXY_FIX_X_HOST", 1),
    )


def setup_logging(app: Flask) -> None:
    log_file = app.config.get("LOG_FILE")
    if not log_file:
        return
    path = Path(log_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    handler.setLevel(app.config.get("LOG_LEVEL", "INFO"))
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config.get("LOG_LEVEL", "INFO"))


def register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.storage_uri = app.config.get("RATELIMIT_STORAGE_URI", "memory://")
    limiter.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"


def register_security(app: Flask) -> None:
    if app.config.get("TESTING") or app.debug:
        return
    talisman.init_app(
        app,
        force_https=True,
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        content_security_policy={
            "default-src": "'self'",
            "img-src": ["'self'", "data:", "https:", "https://maps.gstatic.com"],
            "script-src": ["'self'", "https://maps.googleapis.com", "https://maps.gstatic.com"],
            "style-src": ["'self'", "'unsafe-inline'"],
            "font-src": ["'self'", "data:"],
            "connect-src": ["'self'", "https://maps.googleapis.com"],
            "frame-ancestors": "'none'",
        },
    )


def register_blueprints(app: Flask) -> None:
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    from .routes.profile import profile_bp
    from .routes.billing import billing_bp
    from .routes.health import health_bp
    from .routes.legal import legal_bp
    from .routes.landlord import landlord_bp
    from .routes.main import main_bp
    from .routes.marketplace import marketplace_bp
    from .routes.properties import properties_bp
    from .routes.tenant import tenant_bp
    from .routes.trust import trust_bp

    csrf.exempt(api_bp)
    csrf.exempt(health_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(legal_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(landlord_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(trust_bp)
    app.register_blueprint(marketplace_bp)


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        from . import models  # noqa: F401
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db_command() -> None:
        from .services.seed_service import seed_database
        seed_database()
        click.echo("Demo data inserted.")

    @app.cli.command("ensure-plans")
    def ensure_plans_command() -> None:
        from .services.subscription_service import ensure_default_plans
        ensure_default_plans()
        db.session.commit()
        click.echo("RNW subscription plans ensured.")

    @app.cli.command("set-plan-prices")
    @click.option("--tenant", type=int, required=True)
    @click.option("--landlord", type=int, required=True)
    @click.option("--landlord-listings", type=int, default=25)
    def set_plan_prices_command(tenant: int, landlord: int, landlord_listings: int) -> None:
        from .services.subscription_service import set_plan_prices
        set_plan_prices(tenant, landlord, landlord_listings)
        db.session.commit()
        click.echo("Subscription plan prices updated.")


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        app.logger.exception("Unhandled server error: %s", error)
        return render_template("errors/500.html"), 500
