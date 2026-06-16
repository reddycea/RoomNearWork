from __future__ import annotations

import math
from dataclasses import dataclass

from ..models import Property

SOUTH_AFRICAN_CITY_COORDINATES = {
    "johannesburg": (-26.2041, 28.0473),
    "sandton": (-26.1076, 28.0567),
    "pretoria": (-25.7479, 28.2293),
    "durban": (-29.8587, 31.0218),
    "cape town": (-33.9249, 18.4241),
    "gqeberha": (-33.9608, 25.6022),
    "port elizabeth": (-33.9608, 25.6022),
    "bloemfontein": (-29.0852, 26.1596),
    "polokwane": (-23.9045, 29.4689),
    "nelspruit": (-25.4753, 30.9694),
    "mbombela": (-25.4753, 30.9694),
    "kimberley": (-28.7282, 24.7499),
    "mafikeng": (-25.8652, 25.6442),
    "mahikeng": (-25.8652, 25.6442),
    "richards bay": (-28.7807, 32.0383),
    "empangeni": (-28.7619, 31.8932),
}


@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return radius * c


def geocode_address(address: str | None) -> Coordinate | None:
    """Offline-first geocoder using major SA city centroids.

    In production, replace this with a paid geocoding provider or a controlled
    Nominatim integration with caching and usage-policy compliance.
    """
    if not address:
        return None
    text = address.lower()
    for city, coords in SOUTH_AFRICAN_CITY_COORDINATES.items():
        if city in text:
            return Coordinate(*coords)
    return None


def filter_properties_by_distance(properties: list[Property], lat: float, lng: float, radius_km: float) -> list[tuple[Property, float]]:
    matches: list[tuple[Property, float]] = []
    for prop in properties:
        if prop.latitude is None or prop.longitude is None:
            continue
        distance = haversine_km(lat, lng, prop.latitude, prop.longitude)
        if distance <= radius_km:
            matches.append((prop, round(distance, 2)))
    return sorted(matches, key=lambda item: item[1])
