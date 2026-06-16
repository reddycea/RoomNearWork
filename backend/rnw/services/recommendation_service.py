from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_

from ..models import Property, RentalApplication, SavedProperty, SearchHistory, User
from .geolocation_service import haversine_km


@dataclass
class Recommendation:
    property: Property
    score: float
    reasons: list[str]


def score_property(
    prop: Property,
    *,
    target_lat: float | None = None,
    target_lng: float | None = None,
    max_price: float | None = None,
    preferred_bedrooms: int | None = None,
    preferred_city: str | None = None,
    preferred_transport: str | None = None,
) -> tuple[float, list[str]]:
    """Transparent ranking score for explainable recommendations."""
    score = 0.0
    reasons: list[str] = []

    if prop.status == "approved" and prop.is_available:
        score += 20

    if prop.is_featured:
        score += 8
        reasons.append("featured listing")

    if max_price and prop.price <= max_price:
        score += 22
        reasons.append("within budget")
    elif max_price:
        over_ratio = (prop.price - max_price) / max(max_price, 1)
        score -= min(over_ratio * 25, 18)

    if prop.deposit_amount and max_price and prop.deposit_amount <= max_price:
        score += 3
        reasons.append("deposit likely manageable")

    if preferred_bedrooms is not None and prop.bedrooms == preferred_bedrooms:
        score += 12
        reasons.append("matches bedroom preference")

    if preferred_city and prop.city.lower() == preferred_city.lower():
        score += 15
        reasons.append("same city")

    if preferred_transport and prop.transport_access and preferred_transport.lower() in prop.transport_access.lower():
        score += 10
        reasons.append("matches transport preference")
    elif prop.transport_access:
        score += 3
        reasons.append("transport access listed")

    if target_lat is not None and target_lng is not None and prop.latitude is not None and prop.longitude is not None:
        distance = haversine_km(target_lat, target_lng, prop.latitude, prop.longitude)
        distance_score = max(0, 30 - distance * 1.5)
        score += distance_score
        if distance <= 5:
            reasons.append("close to workplace")
        elif distance <= 15:
            reasons.append("reasonable commute")

    if prop.furnished:
        score += 3
        reasons.append("furnished")
    if prop.parking:
        score += 2
    score += min(prop.view_count or 0, 100) / 20

    return round(score, 2), reasons or ["strong overall match"]


def recommend_properties(
    user: User | None = None,
    *,
    limit: int = 10,
    target_lat: float | None = None,
    target_lng: float | None = None,
    max_price: float | None = None,
    preferred_bedrooms: int | None = None,
    preferred_city: str | None = None,
    preferred_transport: str | None = None,
) -> list[Recommendation]:
    query = Property.query.filter(and_(Property.status == "approved", Property.is_available.is_(True)))

    if preferred_city:
        query = query.filter(Property.city.ilike(preferred_city))
    if max_price:
        query = query.filter(Property.price <= max_price * 1.35)

    candidates = query.limit(300).all()

    if user and not any([max_price, preferred_city, preferred_bedrooms, target_lat, target_lng]):
        latest_search = SearchHistory.query.filter_by(user_id=user.id).order_by(SearchHistory.searched_at.desc()).first()
        if latest_search:
            max_price = latest_search.max_price
            preferred_bedrooms = latest_search.bedrooms
            target_lat = latest_search.latitude
            target_lng = latest_search.longitude

    saved_ids: set[int] = set()
    applied_property_ids: set[int] = set()
    saved_cities: set[str] = set()
    if user:
        saved_rows = SavedProperty.query.filter_by(user_id=user.id).all()
        saved_ids = {saved.property_id for saved in saved_rows}
        saved_cities = {saved.property.city.lower() for saved in saved_rows if saved.property and saved.property.city}
        applied_property_ids = {
            app.property_id for app in RentalApplication.query.filter_by(applicant_id=user.id).all()
        }

    recommendations: list[Recommendation] = []
    for prop in candidates:
        if prop.id in applied_property_ids:
            continue
        score, reasons = score_property(
            prop,
            target_lat=target_lat,
            target_lng=target_lng,
            max_price=max_price,
            preferred_bedrooms=preferred_bedrooms,
            preferred_city=preferred_city,
            preferred_transport=preferred_transport,
        )
        if prop.id in saved_ids:
            score += 5
            reasons.append("you saved this listing")
        if prop.city and prop.city.lower() in saved_cities:
            score += 5
            reasons.append("similar city to saved properties")
        recommendations.append(Recommendation(property=prop, score=round(score, 2), reasons=list(dict.fromkeys(reasons))))

    return sorted(recommendations, key=lambda item: item.score, reverse=True)[:limit]
