from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.rnw.models import Property, TaxiRank


@dataclass(frozen=True)
class TaxiRankEstimate:
    rank_name: str
    area: str
    walking_to_rank_km: float | None
    rank_to_property_km: float | None
    estimated_total_minutes: int | None
    estimated_fare_min: int | None
    estimated_fare_max: int | None
    notes: str | None = None


def _nearest_rank(lat: float, lon: float, city: str | None = None, province: str | None = None) -> TaxiRank | None:
    query = TaxiRank.query.filter_by(is_active=True)
    if city:
        query = query.filter(TaxiRank.city.ilike(f"%{city}%"))
    if province:
        query = query.filter(TaxiRank.province.ilike(f"%{province}%"))
    ranks = query.limit(250).all()
    if not ranks:
        return None
    return min(ranks, key=lambda rank: Property.haversine_km(lat, lon, rank.latitude, rank.longitude))


def estimate_minibus_taxi_trip(origin_lat: float | None, origin_lon: float | None, prop: Property) -> TaxiRankEstimate | None:
    """Estimate a minibus taxi commute using RNW taxi-rank data.

    This is deliberately transparent: it does not pretend Google has a SA taxi mode.
    It combines walking-to-rank + route distance estimate + walking-to-property.
    """
    if origin_lat is None or origin_lon is None or prop.latitude is None or prop.longitude is None:
        return None
    origin_rank = _nearest_rank(origin_lat, origin_lon, city=prop.city, province=prop.province)
    dest_rank = _nearest_rank(prop.latitude, prop.longitude, city=prop.city, province=prop.province)
    if not origin_rank or not dest_rank:
        return None

    walk_to = Property.haversine_km(origin_lat, origin_lon, origin_rank.latitude, origin_rank.longitude)
    rank_to_rank = Property.haversine_km(origin_rank.latitude, origin_rank.longitude, dest_rank.latitude, dest_rank.longitude)
    walk_from = Property.haversine_km(dest_rank.latitude, dest_rank.longitude, prop.latitude, prop.longitude)

    walking_minutes = round((walk_to + walk_from) / 4.8 * 60)
    taxi_minutes = round(rank_to_rank / 28.0 * 60)
    waiting_minutes = 8
    total = max(1, walking_minutes + taxi_minutes + waiting_minutes)
    fare_base = max(12, round(rank_to_rank * 2.2))
    return TaxiRankEstimate(
        rank_name=dest_rank.name,
        area=", ".join([part for part in [dest_rank.suburb, dest_rank.city] if part]),
        walking_to_rank_km=round(walk_to + walk_from, 2),
        rank_to_property_km=round(rank_to_rank, 2),
        estimated_total_minutes=total,
        estimated_fare_min=fare_base,
        estimated_fare_max=fare_base + 10,
        notes=dest_rank.notes,
    )


def attach_taxi_rank_estimates(origin_lat: float | None, origin_lon: float | None, properties: Iterable[Property]) -> None:
    for prop in properties:
        prop.taxi_rank_estimate = estimate_minibus_taxi_trip(origin_lat, origin_lon, prop)
