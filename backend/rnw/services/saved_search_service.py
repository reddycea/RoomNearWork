from __future__ import annotations

from datetime import datetime

from flask import current_app
from sqlalchemy import or_

from backend.rnw.extensions import db
from backend.rnw.models import Property, SavedSearch
from backend.rnw.services.email_service import send_email
from backend.rnw.services.geolocation_service import bounding_box, filter_properties_by_distance
from backend.rnw.services.google_maps_service import GeocodedAddress, attach_commute_measures


def _apply_saved_search_filters(search: SavedSearch):
    query = Property.query.filter(Property.is_active.is_(True), Property.status == "available")
    if search.max_rent:
        query = query.filter(Property.rent_amount <= search.max_rent)
    if search.min_bedrooms:
        query = query.filter(Property.bedrooms >= search.min_bedrooms)
    if search.furnished is not None:
        query = query.filter(Property.furnished.is_(search.furnished))
    if search.pets_allowed is not None:
        query = query.filter(Property.pets_allowed.is_(search.pets_allowed))
    if search.transport_access is not None:
        query = query.filter(Property.transport_access.is_(search.transport_access))
    if search.workplace_latitude is not None and search.workplace_longitude is not None:
        radius = search.max_distance_km or current_app.config.get("DEFAULT_SEARCH_RADIUS_KM", 20)
        min_lat, max_lat, min_lon, max_lon = bounding_box(search.workplace_latitude, search.workplace_longitude, float(radius))
        query = query.filter(Property.latitude.between(min_lat, max_lat), Property.longitude.between(min_lon, max_lon))
    elif search.workplace_area or search.city or search.province:
        terms = [t for t in {search.workplace_area, search.city, search.province} if t]
        filters = []
        for term in terms:
            like = f"%{term}%"
            filters.extend([Property.suburb.ilike(like), Property.city.ilike(like), Property.province.ilike(like)])
        query = query.filter(or_(*filters))
    return query


def matching_properties_for_search(search: SavedSearch, limit: int = 20) -> list[Property]:
    items = _apply_saved_search_filters(search).order_by(Property.created_at.desc()).limit(limit * 3).all()
    if search.workplace_latitude is None or search.workplace_longitude is None:
        return items[:limit]
    origin = GeocodedAddress(
        query=search.workplace_address or "saved workplace",
        formatted_address=search.workplace_formatted_address or search.workplace_address or "saved workplace",
        latitude=search.workplace_latitude,
        longitude=search.workplace_longitude,
        place_id=search.workplace_place_id,
        suburb=search.workplace_area,
        city=search.city,
        province=search.province,
    )
    radius = float(search.max_distance_km or current_app.config.get("DEFAULT_SEARCH_RADIUS_KM", 20))
    items = filter_properties_by_distance(items, origin.latitude, origin.longitude, radius) or items
    attach_commute_measures(origin, items, selected_mode=search.travel_mode or "all")
    if search.max_travel_minutes:
        items = [p for p in items if any(m.duration_min and m.duration_min <= search.max_travel_minutes for m in getattr(p, "commute_modes", []))]
    return items[:limit]


def run_saved_search_alerts() -> int:
    if not current_app.config.get("SAVED_SEARCH_ALERTS_ENABLED", True):
        return 0
    count = 0
    searches = SavedSearch.query.filter_by(alerts_enabled=True).all()
    for search in searches:
        matches = matching_properties_for_search(search, limit=5)
        if not matches:
            continue
        titles = "\n".join(f"- {item.title} ({item.public_location()}) R{item.rent_amount}" for item in matches)
        send_email(search.user.email, f"New Room Near Work matches for {search.name}", "Here are your latest matches:\n\n" + titles)
        search.last_alerted_at = datetime.utcnow()
        count += 1
    db.session.commit()
    return count
