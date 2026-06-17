from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import click
from flask import Flask

from .config import config_by_name
from .extensions import cache, csrf, db, jwt, limiter, login_manager, mail, migrate


def create_app(config_name: str | None = None) -> Flask:
    """Application factory used by Flask, Gunicorn, tests, and CLI commands."""
    app = Flask(__name__, instance_relative_config=True)
    config_name = config_name or app.config.get("ENV") or "default"
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    app.instance_path and app.config["UPLOAD_FOLDER_PATH"].mkdir(parents=True, exist_ok=True)
    setup_logging(app)
    register_extensions(app)
    register_blueprints(app)
    register_cli(app)
    register_error_handlers(app)

    return app


def setup_logging(app: Flask) -> None:
    log_file = app.config.get("LOG_FILE")
    if not log_file:
        return
    from pathlib import Path
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
    limiter.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)


def register_blueprints(app: Flask) -> None:
    from .routes.admin import admin_bp
    from .routes.api import api_bp
    from .routes.auth import auth_bp
    from .routes.billing import billing_bp
    from .routes.health import health_bp
    from .routes.landlord import landlord_bp
    from .routes.main import main_bp
    from .routes.properties import properties_bp
    from .routes.tenant import tenant_bp
    from .routes.trust import trust_bp

    csrf.exempt(api_bp)
    csrf.exempt(health_bp)

    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(tenant_bp)
    app.register_blueprint(landlord_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(trust_bp)


def register_cli(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db_command() -> None:
        """Create all database tables. Use Flask-Migrate in production."""
        from . import models  # noqa: F401 - imports model metadata
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("seed-db")
    def seed_db_command() -> None:
        """Seed database with demo users and properties."""
        from .services.seed_service import seed_database
        seed_database()
        click.echo("Demo data inserted.")

    @app.cli.command("ensure-plans")
    def ensure_plans_command() -> None:
        """Create or update official RNW R50/R100 monthly plans."""
        from .services.subscription_service import ensure_default_plans
        ensure_default_plans()
        db.session.commit()
        click.echo("RNW subscription plans ensured.")


def register_error_handlers(app: Flask) -> None:
    from flask import render_template

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
