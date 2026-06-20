from flask import Blueprint, render_template

legal_bp = Blueprint("legal", __name__, url_prefix="/legal")


@legal_bp.get("/privacy")
def privacy():
    return render_template("legal/privacy.html")


@legal_bp.get("/terms")
def terms():
    return render_template("legal/terms.html")


@legal_bp.get("/safety")
def safety():
    return render_template("legal/safety.html")


@legal_bp.get("/popia")
def popia():
    return render_template("legal/popia.html")


@legal_bp.get("/data-requests")
def data_requests():
    return render_template("legal/data_requests.html")
