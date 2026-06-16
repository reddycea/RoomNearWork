from flask import Blueprint, jsonify

from ..extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"
    return jsonify({"status": "ok", "database": db_status})
