from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from flask import current_app

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

from backend.rnw.models import Property


@dataclass(frozen=True)
class GeocodedAddress:
    query: str
    formatted_address: str
    latitude: float | None
    longitude: float | None
    place_id: str | None = None
    suburb: str | None = None
    city: str | None = None
    province: str | None = None
    country: str | None = None
    source: str = "fallback"

    @property
    def area_label(self) -> str:
        return self.suburb or self.city or self.province or self.formatted_address or self.query


@dataclass(frozen=True)
class PlaceSuggestion:
    description: str
    place_id: str | None
    main_text: str
    secondary_text: str | None = None
    source: str = "fallback"


@dataclass(frozen=True)
class RouteMeasure:
    mode: str
    label: str
    distance_km: float | None
    duration_min: int | None
    source: str
    status: str = "OK"


DEMO_AREAS = {
    "umhlanga": (-29.7270, 31.0850, "Umhlanga", "Umhlanga", "KwaZulu-Natal"),
    "11 park avenue": (-29.7270, 31.0850, "Umhlanga", "Umhlanga", "KwaZulu-Natal"),
    "park avenue umhlanga": (-29.7270, 31.0850, "Umhlanga", "Umhlanga", "KwaZulu-Natal"),
    "sandton": (-26.1076, 28.0567, "Sandton", "Johannesburg", "Gauteng"),
    "braamfontein": (-26.1929, 28.0368, "Braamfontein", "Johannesburg", "Gauteng"),
    "durban": (-29.8587, 31.0218, None, "Durban", "KwaZulu-Natal"),
    "johannesburg": (-26.2041, 28.0473, None, "Johannesburg", "Gauteng"),
    "cape town": (-33.9249, 18.4241, None, "Cape Town", "Western Cape"),
}

MODE_TO_GOOGLE = {
    "car": "DRIVE",
    "walking": "WALK",
    # Google has TRANSIT, not a South African minibus taxi mode. RNW labels it as taxi/public transport.
    "taxi": "TRANSIT",
}
MODE_LABELS = {
    "car": "Car",
    "walking": "Walking",
    "taxi": "Taxi / public transport",
}


def _api_key() -> str:
    return current_app.config.get("GOOGLE_MAPS_API_KEY", "")


def _find_component(components: list[dict], wanted: set[str]) -> str | None:
    for component in components:
        types = set(component.get("types", []))
        if wanted.intersection(types):
            return component.get("long_name")
    return None


def fallback_suggestions(text: str) -> list[PlaceSuggestion]:
    normal = (text or "").lower().strip()
    if len(normal) < 2:
        return []
    suggestions: list[PlaceSuggestion] = []
    for key, (_, _, suburb, city, province) in DEMO_AREAS.items():
        if normal in key or key in normal:
            description = f"{text.strip() or key.title()}, {city or suburb}, {province}, South Africa"
            suggestions.append(PlaceSuggestion(description, None, text.strip() or key.title(), f"{city or suburb}, {province}", "fallback"))
    if not suggestions:
        suggestions.append(PlaceSuggestion(f"{text.strip()}, South Africa", None, text.strip(), "South Africa", "fallback"))
    return suggestions[:5]


def places_autocomplete(text: str) -> list[PlaceSuggestion]:
    text = (text or "").strip()
    if len(text) < 2:
        return []
    key = _api_key()
    if not key or requests is None:
        return fallback_suggestions(text)
    params = {
        "input": text,
        "key": key,
        "components": "country:za",
        "language": current_app.config.get("GOOGLE_MAPS_LANGUAGE", "en-ZA"),
    }
    try:
        response = requests.get("https://maps.googleapis.com/maps/api/place/autocomplete/json", params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return fallback_suggestions(text)
    if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
        return fallback_suggestions(text)
    suggestions = []
    for item in payload.get("predictions", [])[:8]:
        formatting = item.get("structured_formatting", {})
        suggestions.append(
            PlaceSuggestion(
                description=item.get("description", text),
                place_id=item.get("place_id"),
                main_text=formatting.get("main_text") or item.get("description", text),
                secondary_text=formatting.get("secondary_text"),
                source="google",
            )
        )
    return suggestions or fallback_suggestions(text)


def fallback_geocode(address: str) -> GeocodedAddress:
    normal = (address or "").strip().lower()
    for key, (lat, lon, suburb, city, province) in DEMO_AREAS.items():
        if key in normal:
            formatted = f"{address.strip()}, {city or suburb}, {province}, South Africa"
            return GeocodedAddress(
                query=address,
                formatted_address=formatted,
                latitude=lat,
                longitude=lon,
                suburb=suburb,
                city=city,
                province=province,
                country="South Africa",
                source="fallback",
            )
    return GeocodedAddress(query=address, formatted_address=address, latitude=None, longitude=None, country="South Africa", source="fallback")


def _parse_geocode_result(query: str, result: dict) -> GeocodedAddress:
    geometry = result.get("geometry", {}).get("location", {})
    components = result.get("address_components", [])
    suburb = _find_component(components, {"sublocality", "sublocality_level_1", "neighborhood"})
    city = _find_component(components, {"locality", "postal_town", "administrative_area_level_2"})
    province = _find_component(components, {"administrative_area_level_1"})
    country = _find_component(components, {"country"})
    return GeocodedAddress(
        query=query,
        formatted_address=result.get("formatted_address", query),
        latitude=geometry.get("lat"),
        longitude=geometry.get("lng"),
        place_id=result.get("place_id"),
        suburb=suburb,
        city=city,
        province=province,
        country=country,
        source="google",
    )


def geocode_address(address: str) -> GeocodedAddress:
    address = (address or "").strip()
    if not address:
        return fallback_geocode(address)
    key = _api_key()
    if not key or requests is None:
        return fallback_geocode(address)
    params = {"address": address, "key": key, "region": current_app.config.get("GOOGLE_MAPS_REGION", "ZA"), "language": current_app.config.get("GOOGLE_MAPS_LANGUAGE", "en-ZA")}
    try:
        response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return fallback_geocode(address)
    if payload.get("status") != "OK" or not payload.get("results"):
        return fallback_geocode(address)
    return _parse_geocode_result(address, payload["results"][0])


def geocode_place_id(place_id: str, fallback_text: str = "") -> GeocodedAddress:
    place_id = (place_id or "").strip()
    if not place_id:
        return geocode_address(fallback_text)
    key = _api_key()
    if not key or requests is None:
        return geocode_address(fallback_text)
    params = {"place_id": place_id, "key": key, "language": current_app.config.get("GOOGLE_MAPS_LANGUAGE", "en-ZA")}
    try:
        response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=8)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return geocode_address(fallback_text)
    if payload.get("status") != "OK" or not payload.get("results"):
        return geocode_address(fallback_text)
    return _parse_geocode_result(fallback_text or place_id, payload["results"][0])


def geocode_property_address(address: str, suburb: str | None = None, city: str | None = None, province: str | None = None) -> GeocodedAddress:
    parts = [address, suburb, city, province, "South Africa"]
    return geocode_address(", ".join([part for part in parts if part]))


def fallback_route(origin: GeocodedAddress, prop: Property, mode: str) -> RouteMeasure:
    if origin.latitude is None or origin.longitude is None or prop.latitude is None or prop.longitude is None:
        return RouteMeasure(mode=mode, label=MODE_LABELS[mode], distance_km=None, duration_min=None, source="fallback", status="NO_COORDINATES")
    distance = Property.haversine_km(origin.latitude, origin.longitude, prop.latitude, prop.longitude)
    speeds = {"walking": 4.8, "taxi": 28.0, "car": 38.0}
    duration = max(1, round(distance / speeds[mode] * 60))
    return RouteMeasure(mode=mode, label=MODE_LABELS[mode], distance_km=round(distance, 2), duration_min=duration, source="fallback")


def compute_route_measures(origin: GeocodedAddress, properties: Iterable[Property], mode: str) -> dict[int, RouteMeasure]:
    props = [prop for prop in properties if prop.latitude is not None and prop.longitude is not None]
    if mode not in MODE_TO_GOOGLE:
        mode = "car"
    if not props:
        return {}
    key = _api_key()
    if not key or requests is None or not current_app.config.get("GOOGLE_ROUTE_MATRIX_ENABLED", True) or origin.latitude is None or origin.longitude is None:
        return {prop.id: fallback_route(origin, prop, mode) for prop in props}
    results: dict[int, RouteMeasure] = {}
    endpoint = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": key, "X-Goog-FieldMask": "originIndex,destinationIndex,status,condition,distanceMeters,duration"}
    for offset in range(0, len(props), 25):
        chunk = props[offset: offset + 25]
        body = {
            "origins": [{"waypoint": {"location": {"latLng": {"latitude": origin.latitude, "longitude": origin.longitude}}}}],
            "destinations": [{"waypoint": {"location": {"latLng": {"latitude": prop.latitude, "longitude": prop.longitude}}}} for prop in chunk],
            "travelMode": MODE_TO_GOOGLE[mode],
        }
        if mode == "car":
            body["routingPreference"] = "TRAFFIC_AWARE"
        try:
            response = requests.post(endpoint, headers=headers, json=body, timeout=12)
            response.raise_for_status()
            rows = response.json()
        except Exception:
            for prop in chunk:
                results[prop.id] = fallback_route(origin, prop, mode)
            continue
        for row in rows:
            idx = row.get("destinationIndex")
            if idx is None or idx >= len(chunk):
                continue
            prop = chunk[idx]
            status = row.get("status", {}).get("code", "OK") if isinstance(row.get("status"), dict) else "OK"
            if "distanceMeters" not in row or "duration" not in row:
                results[prop.id] = fallback_route(origin, prop, mode)
                continue
            duration_seconds = int(str(row.get("duration", "0s")).rstrip("s") or 0)
            results[prop.id] = RouteMeasure(mode=mode, label=MODE_LABELS[mode], distance_km=round(row["distanceMeters"] / 1000, 2), duration_min=max(1, round(duration_seconds / 60)), source="google", status=status)
    return results


def attach_commute_measures(origin: GeocodedAddress, properties: list[Property], selected_mode: str = "all") -> None:
    modes = ["walking", "taxi", "car"] if selected_mode in {"", "all", None} else [selected_mode]
    for prop in properties:
        prop.commute_modes = []
        prop.commute_area = origin.area_label
        prop.commute_address = origin.formatted_address
    for mode in modes:
        measures = compute_route_measures(origin, properties, mode)
        for prop in properties:
            measure = measures.get(prop.id)
            if measure:
                prop.commute_modes.append(measure)
    for prop in properties:
        valid = [m for m in prop.commute_modes if m.duration_min is not None]
        if valid:
            best = min(valid, key=lambda item: item.duration_min)
            prop.workplace_distance_km = best.distance_km
            prop.commute_summary = f"{best.duration_min} min by {best.label.lower()}"
        else:
            prop.commute_summary = None
