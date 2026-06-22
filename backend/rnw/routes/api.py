from __future__ import annotations

from flask import Blueprint, jsonify, request

from flask_login import current_user

from backend.rnw.extensions import db
from backend.rnw.models import PlacesSession, Property, TaxiRank
from backend.rnw.models.marketplace import hash_token
from backend.rnw.services.google_maps_service import geocode_address, geocode_place_id, places_autocomplete

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/properties")
def properties():
    items = Property.query.filter_by(is_active=True, status="available").limit(50).all()
    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "rent_amount": p.rent_amount,
            "location": p.public_location(),
            "quality_score": p.quality_score,
            "latitude": p.latitude,
            "longitude": p.longitude,
        }
        for p in items
    ])




@api_bp.post("/places/session")
def places_session():
    user_id = current_user.id if getattr(current_user, "is_authenticated", False) else None
    session, raw = PlacesSession.issue(user_id=user_id, purpose=request.json.get("purpose", "workplace_search") if request.is_json else "workplace_search")
    db.session.add(session)
    db.session.commit()
    return jsonify({"session_token": raw, "expires_in_seconds": 300})


@api_bp.get("/places/autocomplete")
def places():
    text = request.args.get("q", "")
    session_token = request.args.get("session_token", "")
    suggestions = places_autocomplete(text, session_token=session_token)
    return jsonify([
        {
            "description": s.description,
            "place_id": s.place_id,
            "main_text": s.main_text,
            "secondary_text": s.secondary_text,
            "source": s.source,
        }
        for s in suggestions
    ])


@api_bp.get("/geocode")
def geocode():
    place_id = request.args.get("place_id", "")
    address = request.args.get("address", "")
    result = geocode_place_id(place_id, address) if place_id else geocode_address(address)
    return jsonify({
        "query": result.query,
        "formatted_address": result.formatted_address,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "place_id": result.place_id,
        "suburb": result.suburb,
        "city": result.city,
        "province": result.province,
        "country": result.country,
        "area_label": result.area_label,
        "source": result.source,
    })


@api_bp.get("/map-listings")
def map_listings():
    items = Property.query.filter(Property.is_active.is_(True), Property.status == "available", Property.latitude.isnot(None), Property.longitude.isnot(None)).limit(250).all()
    return jsonify([
        {
            "id": p.id,
            "title": p.title,
            "rent_amount": p.rent_amount,
            "location": p.public_address(),
            "latitude": p.latitude,
            "longitude": p.longitude,
        }
        for p in items
    ])


@api_bp.get("/places/candidates")
def place_candidates():
    """Return candidate addresses for an ambiguous workplace search.

    Frontend can show these as a Did-you-mean confirmation before running a commute search.
    """
    text = request.args.get("q", "")
    session_token = request.args.get("session_token", "")
    suggestions = places_autocomplete(text, session_token=session_token)
    return jsonify([
        {
            "description": s.description,
            "place_id": s.place_id,
            "main_text": s.main_text,
            "secondary_text": s.secondary_text,
            "source": s.source,
        }
        for s in suggestions
    ])


@api_bp.post("/places/confirm")
def confirm_place():
    payload = request.get_json(silent=True) or {}
    session_token = payload.get("session_token", "")
    place_id = payload.get("place_id")
    description = payload.get("description")
    if session_token:
        session = PlacesSession.query.filter_by(token_hash=hash_token(session_token)).one_or_none()
        if session and session.is_valid():
            session.mark_used(place_id, description)
            db.session.commit()
    result = geocode_place_id(place_id, description or "") if place_id else geocode_address(description or "")
    return jsonify({
        "formatted_address": result.formatted_address,
        "place_id": result.place_id,
        "latitude": result.latitude,
        "longitude": result.longitude,
        "area_label": result.area_label,
        "city": result.city,
        "province": result.province,
        "source": result.source,
    })


@api_bp.get("/taxi-ranks")
def taxi_ranks():
    items = TaxiRank.query.filter_by(is_active=True).limit(250).all()
    return jsonify([
        {
            "id": rank.id,
            "name": rank.name,
            "area": ", ".join([part for part in [rank.suburb, rank.city, rank.province] if part]),
            "latitude": rank.latitude,
            "longitude": rank.longitude,
            "notes": rank.notes,
        }
        for rank in items
    ])
