from __future__ import annotations

import math

from backend.rnw.models import Property


def bounding_box(lat: float, lon: float, km: float) -> tuple[float, float, float, float]:
    # Rough but useful pre-filter before exact haversine/Google route distance.
    lat_delta = km / 111.0
    lon_delta = km / max(1.0, 111.0 * math.cos(math.radians(lat)))
    return lat - lat_delta, lat + lat_delta, lon - lon_delta, lon + lon_delta


def filter_properties_by_distance(properties: list[Property], lat: float, lon: float, max_km: float) -> list[Property]:
    matched = []
    for prop in properties:
        if prop.latitude is None or prop.longitude is None:
            continue
        distance = Property.haversine_km(lat, lon, prop.latitude, prop.longitude)
        if distance <= max_km:
            prop.workplace_distance_km = round(distance, 2)
            matched.append(prop)
    return matched
