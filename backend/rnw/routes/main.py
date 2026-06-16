from flask import Blueprint, current_app, render_template, send_from_directory

from ..models import Property

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    featured = (
        Property.query.filter_by(status="approved", is_available=True)
        .order_by(Property.view_count.desc(), Property.created_at.desc())
        .limit(6)
        .all()
    )
    stats = {
        "approved_properties": Property.query.filter_by(status="approved").count(),
        "cities": len({p.city for p in Property.query.with_entities(Property.city).distinct().all()}),
    }
    return render_template("index.html", featured=featured, stats=stats)


@main_bp.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    """Serve public property photos in development/small deployments.

    Production deployments should let Nginx or object storage serve public files.
    Private verification documents are never served by this route.
    """
    return send_from_directory(current_app.config["UPLOAD_FOLDER_PATH"], filename)



@main_bp.get("/legal/terms")
def terms():
    return render_template("legal/terms.html")


@main_bp.get("/legal/privacy")
def privacy():
    return render_template("legal/privacy.html")


@main_bp.get("/legal/refunds")
def refunds():
    return render_template("legal/refunds.html")


@main_bp.get("/legal/popia")
def popia():
    return render_template("legal/popia.html")


@main_bp.get("/legal/safety")
def safety():
    return render_template("legal/safety.html")
