from __future__ import annotations

from datetime import datetime, timedelta

from backend.rnw.extensions import db
from backend.rnw.models import Property, TaxiRank, User
from backend.rnw.services.google_maps_service import geocode_property_address
from backend.rnw.services.listing_quality_service import update_listing_quality
from backend.rnw.services.subscription_service import ensure_default_plans


def _user(email: str, name: str, password: str, role: str, is_admin: bool = False) -> User:
    user = User.query.filter_by(email=email).one_or_none()
    if user:
        return user
    user = User(email=email, full_name=name, role=role, can_act_as_tenant=True, can_act_as_landlord=True, is_admin=is_admin, email_verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def seed_database() -> None:
    ensure_default_plans()
    _user("admin@rnw.local", "RNW Admin", "AdminPass123!", "admin", True)
    landlord = _user("landlord@rnw.local", "Lebo Landlord", "LandlordPass123!", "landlord")
    _user("tenant@rnw.local", "Tumi Tenant", "TenantPass123!", "tenant")

    if Property.query.count() == 0:
        samples = [
            ("Compact room near Sandton", "A secure modern room with fast access to transport and work nodes. Ideal for a young professional looking for a clean commute.", 3500, "Johannesburg", "Gauteng", "Sandton", "12 Rivonia Road", True, True),
            ("Sunny apartment close to CBD", "Bright apartment with natural light, simple finishes and quick access to taxi routes. Close to shops and workplaces.", 5200, "Johannesburg", "Gauteng", "Braamfontein", "22 Jorissen Street", False, True),
            ("Quiet room near Umhlanga offices", "Quiet lock-up room in a shared home near offices, malls and transport. Suitable for weekly commuting professionals.", 4200, "Umhlanga", "KwaZulu-Natal", "Umhlanga", "11 Park Avenue", True, True),
            ("Affordable room near Phoenix taxi routes", "Budget-friendly room with transport access into Umhlanga and Durban. Good for shift workers and weekly commuters.", 2800, "Durban", "KwaZulu-Natal", "Phoenix", "19 Phoenix Highway", False, True),
        ]
        for title, desc, rent, city, province, suburb, address, furnished, transport in samples:
            geo = geocode_property_address(address, suburb, city, province)
            prop = Property(
                landlord_id=landlord.id,
                title=title,
                description=desc,
                rent_amount=rent,
                deposit_amount=rent,
                bedrooms=1,
                bathrooms=1,
                city=city,
                province=province,
                suburb=suburb,
                address_line=address,
                formatted_address=geo.formatted_address,
                google_place_id=geo.place_id,
                latitude=geo.latitude,
                longitude=geo.longitude,
                approximate_address=f"{suburb}, {city}",
                furnished=furnished,
                transport_access=transport,
                nearest_transport="Taxi route nearby" if transport else None,
                status="available",
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            update_listing_quality(prop)
            db.session.add(prop)
    seed_taxi_ranks()
    db.session.commit()



def seed_taxi_ranks() -> None:
    ranks = [
        ("Gateway / Umhlanga taxi pickup", "Umhlanga", "Umhlanga", "KwaZulu-Natal", -29.7245, 31.0651, "Use as demo data; verify exact rank before production."),
        ("Durban Station taxi rank", "CBD", "Durban", "KwaZulu-Natal", -29.8519, 31.0256, "Major Durban public transport interchange."),
        ("Sandton taxi rank", "Sandton", "Johannesburg", "Gauteng", -26.1062, 28.0560, "Demo taxi-rank record for workplace commute testing."),
        ("Noord taxi rank", "CBD", "Johannesburg", "Gauteng", -26.1980, 28.0462, "Demo taxi-rank record for central Johannesburg."),
    ]
    for name, suburb, city, province, lat, lon, notes in ranks:
        existing = TaxiRank.query.filter_by(name=name).first()
        if not existing:
            db.session.add(TaxiRank(name=name, suburb=suburb, city=city, province=province, latitude=lat, longitude=lon, notes=notes, is_active=True))
