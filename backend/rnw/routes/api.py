from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..extensions import cache, db
from ..models import Property, User
from ..services.geolocation_service import filter_properties_by_distance, geocode_address
from ..services.recommendation_service import recommend_properties

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/properties")
@cache.cached(timeout=60, query_string=True)
def properties():
    query = Property.query.filter_by(status="approved", is_available=True)
    city = request.args.get("city")
    province = request.args.get("province")
    max_price = request.args.get("max_price", type=float)
    max_deposit = request.args.get("max_deposit", type=float)
    bedrooms = request.args.get("bedrooms", type=int)
    furnished = request.args.get("furnished", type=int)
    transport_access = request.args.get("transport_access")
    workplace = request.args.get("workplace")
    radius_km = request.args.get("radius_km", 10, type=float)

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if province:
        query = query.filter(Property.province == province)
    if max_price:
        query = query.filter(Property.price <= max_price)
    if max_deposit:
        query = query.filter((Property.deposit_amount == None) | (Property.deposit_amount <= max_deposit))  # noqa: E711
    if bedrooms is not None:
        query = query.filter(Property.bedrooms >= bedrooms)
    if furnished == 1:
        query = query.filter(Property.furnished.is_(True))
    if transport_access:
        query = query.filter(Property.transport_access.ilike(f"%{transport_access}%"))

    coord = geocode_address(workplace)
    if coord:
        matches = filter_properties_by_distance(query.limit(500).all(), coord.latitude, coord.longitude, radius_km)
        return jsonify({"data": [{**prop.to_dict(include_landlord=True), "distance_km": distance} for prop, distance in matches]})

    properties = query.order_by(Property.created_at.desc()).limit(100).all()
    return jsonify({"data": [prop.to_dict(include_landlord=True) for prop in properties]})


@api_bp.get("/properties/<int:property_id>")
def property_detail(property_id: int):
    prop = db.session.get(Property, property_id)
    if not prop or prop.status != "approved":
        return jsonify({"message": "Property not found"}), 404
    return jsonify(prop.to_dict(include_landlord=True))


@api_bp.get("/geocode")
def geocode():
    address = request.args.get("address")
    coord = geocode_address(address)
    if not coord:
        return jsonify({"message": "Address could not be geocoded by the offline geocoder"}), 404
    return jsonify({"latitude": coord.latitude, "longitude": coord.longitude})


@api_bp.get("/recommendations")
@jwt_required(optional=True)
def recommendations():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity else None
    workplace = request.args.get("workplace")
    coord = geocode_address(workplace)
    items = recommend_properties(
        user,
        limit=request.args.get("limit", 10, type=int),
        target_lat=coord.latitude if coord else request.args.get("lat", type=float),
        target_lng=coord.longitude if coord else request.args.get("lng", type=float),
        max_price=request.args.get("max_price", type=float),
        preferred_bedrooms=request.args.get("bedrooms", type=int),
        preferred_city=request.args.get("city"),
    )
    return jsonify({
        "data": [
            {
                "property": item.property.to_dict(include_landlord=True),
                "score": item.score,
                "reasons": item.reasons,
            }
            for item in items
        ]
    })
