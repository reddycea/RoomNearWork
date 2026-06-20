from flask import Blueprint, render_template

from backend.rnw.models import Property

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    featured = Property.query.filter_by(is_active=True, status="available").order_by(Property.created_at.desc()).limit(6).all()
    return render_template("main/index.html", featured=featured)
