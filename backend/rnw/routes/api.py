from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.rnw.models import Property
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


@api_bp.get("/places/autocomplete")
def places():
    text = request.args.get("q", "")
    suggestions = places_autocomplete(text)
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
