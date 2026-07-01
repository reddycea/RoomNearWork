from __future__ import annotations

from datetime import datetime, timedelta

from backend.rnw.extensions import db
from backend.rnw.models import (
    LandlordApplication,
    Property,
    RentalApplication,
    TaxiRank,
    User,
)
from backend.rnw.services.subscription_service import ensure_default_plans


DEMO_PASSWORDS = {
    "admin@rnw.local": "AdminPass123!",
    "tenant@rnw.local": "TenantPass123!",
    "landlord@rnw.local": "LandlordPass123!",
    "pending-landlord@rnw.local": "PendingPass123!",
}


def _user(
    *,
    email: str,
    first_name: str,
    last_name: str,
    phone: str,
    id_number: str,
    password: str,
    role: str = "tenant",
    is_admin: bool = False,
    can_act_as_tenant: bool = True,
    can_act_as_landlord: bool = False,
) -> User:
    user = User.query.filter_by(email=email).one_or_none()
    full_name = f"{first_name} {last_name}".strip()

    if user:
        user.first_name = user.first_name or first_name
        user.last_name = user.last_name or last_name
        user.full_name = user.full_name or full_name
        user.phone = user.phone or phone
        user.id_number = user.id_number or id_number
        user.role = role
        user.is_admin = is_admin
        user.can_act_as_tenant = can_act_as_tenant
        user.can_act_as_landlord = can_act_as_landlord
        user.email_verified = True
        user.email_verified_at = user.email_verified_at or datetime.utcnow()
        return user

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        phone=phone,
        id_number=id_number,
        role=role,
        is_admin=is_admin,
        can_act_as_tenant=can_act_as_tenant,
        can_act_as_landlord=can_act_as_landlord,
        email_verified=True,
        email_verified_at=datetime.utcnow(),
    )
    user.set_password(password)

    db.session.add(user)
    db.session.flush()

    return user


def _property(
    *,
    landlord: User,
    title: str,
    description: str,
    rent_amount: int,
    deposit_amount: int,
    city: str,
    province: str,
    suburb: str,
    address_line: str,
    latitude: float,
    longitude: float,
    furnished: bool = False,
    pets_allowed: bool = False,
    transport_access: bool = True,
) -> Property:
    existing = Property.query.filter_by(title=title, landlord_id=landlord.id).one_or_none()

    if existing:
        return existing

    prop = Property(
        landlord_id=landlord.id,
        title=title,
        description=description,
        rent_amount=rent_amount,
        deposit_amount=deposit_amount,
        bedrooms=1,
        bathrooms=1,
        city=city,
        province=province,
        suburb=suburb,
        address_line=address_line,
        formatted_address=f"{address_line}, {suburb}, {city}, {province}, South Africa",
        approximate_address=f"{suburb}, {city}",
        address_visibility="approved_viewing",
        latitude=latitude,
        longitude=longitude,
        workplace_distance_km=3.5,
        nearest_transport="Taxi route nearby" if transport_access else None,
        commute_notes="Demo commute data for testing Room Near Work.",
        furnished=furnished,
        pets_allowed=pets_allowed,
        transport_access=transport_access,
        status="available",
        is_active=True,
        quality_score=80,
        listing_verified=True,
        verified_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )

    db.session.add(prop)
    db.session.flush()

    return prop


def _taxi_rank(
    *,
    name: str,
    suburb: str,
    city: str,
    province: str,
    latitude: float,
    longitude: float,
    notes: str,
) -> TaxiRank:
    existing = TaxiRank.query.filter_by(name=name).one_or_none()

    if existing:
        return existing

    rank = TaxiRank(
        name=name,
        suburb=suburb,
        city=city,
        province=province,
        latitude=latitude,
        longitude=longitude,
        notes=notes,
        is_active=True,
    )

    db.session.add(rank)
    db.session.flush()

    return rank


def _landlord_application(applicant: User, message: str) -> LandlordApplication:
    existing = LandlordApplication.query.filter_by(
        applicant_id=applicant.id,
        status="pending",
    ).one_or_none()

    if existing:
        return existing

    application = LandlordApplication(
        applicant_id=applicant.id,
        status="pending",
        message=message,
    )

    db.session.add(application)
    db.session.flush()

    return application


def _rental_application(
    *,
    applicant: User,
    rental_property: Property,
    message: str,
) -> RentalApplication:
    existing = RentalApplication.query.filter_by(
        applicant_id=applicant.id,
        property_id=rental_property.id,
    ).one_or_none()

    if existing:
        return existing

    application = RentalApplication(
        applicant_id=applicant.id,
        property_id=rental_property.id,
        message=message,
        status="pending",
    )

    db.session.add(application)
    db.session.flush()

    return application


def seed_database() -> None:
    ensure_default_plans()

    admin = _user(
        email="admin@rnw.local",
        first_name="RNW",
        last_name="Admin",
        phone="+270600000001",
        id_number="9001015000001",
        password=DEMO_PASSWORDS["admin@rnw.local"],
        role="admin",
        is_admin=True,
        can_act_as_tenant=True,
        can_act_as_landlord=True,
    )

    landlord = _user(
        email="landlord@rnw.local",
        first_name="Lebo",
        last_name="Landlord",
        phone="+270600000002",
        id_number="9001015000002",
        password=DEMO_PASSWORDS["landlord@rnw.local"],
        role="landlord",
        can_act_as_tenant=True,
        can_act_as_landlord=True,
    )

    tenant = _user(
        email="tenant@rnw.local",
        first_name="Tumi",
        last_name="Tenant",
        phone="+270600000003",
        id_number="9001015000003",
        password=DEMO_PASSWORDS["tenant@rnw.local"],
        role="tenant",
        can_act_as_tenant=True,
        can_act_as_landlord=False,
    )

    pending_landlord = _user(
        email="pending-landlord@rnw.local",
        first_name="Sizwe",
        last_name="Applicant",
        phone="+270600000004",
        id_number="9001015000004",
        password=DEMO_PASSWORDS["pending-landlord@rnw.local"],
        role="tenant",
        can_act_as_tenant=True,
        can_act_as_landlord=False,
    )

    prop1 = _property(
        landlord=landlord,
        title="Compact room near Sandton",
        description=(
            "A secure modern room with quick access to transport and major work nodes. "
            "Ideal for a young professional looking for a clean commute."
        ),
        rent_amount=3500,
        deposit_amount=3500,
        city="Johannesburg",
        province="Gauteng",
        suburb="Sandton",
        address_line="12 Rivonia Road",
        latitude=-26.1076,
        longitude=28.0567,
        furnished=True,
        pets_allowed=False,
        transport_access=True,
    )

    _property(
        landlord=landlord,
        title="Sunny apartment close to Braamfontein CBD",
        description=(
            "Bright apartment with natural light, simple finishes and quick access "
            "to taxi routes, shops and workplaces."
        ),
        rent_amount=5200,
        deposit_amount=5200,
        city="Johannesburg",
        province="Gauteng",
        suburb="Braamfontein",
        address_line="22 Jorissen Street",
        latitude=-26.1929,
        longitude=28.0365,
        furnished=False,
        pets_allowed=False,
        transport_access=True,
    )

    _property(
        landlord=landlord,
        title="Quiet room near Umhlanga offices",
        description=(
            "Quiet lock-up room in a shared home near offices, malls and transport. "
            "Suitable for weekly commuting professionals."
        ),
        rent_amount=4200,
        deposit_amount=4200,
        city="Umhlanga",
        province="KwaZulu-Natal",
        suburb="Umhlanga",
        address_line="11 Park Avenue",
        latitude=-29.7250,
        longitude=31.0660,
        furnished=True,
        pets_allowed=False,
        transport_access=True,
    )

    _property(
        landlord=landlord,
        title="Affordable room near Phoenix taxi routes",
        description=(
            "Budget-friendly room with transport access into Umhlanga and Durban. "
            "Good for shift workers and weekly commuters."
        ),
        rent_amount=2800,
        deposit_amount=2800,
        city="Durban",
        province="KwaZulu-Natal",
        suburb="Phoenix",
        address_line="19 Phoenix Highway",
        latitude=-29.7050,
        longitude=30.9970,
        furnished=False,
        pets_allowed=False,
        transport_access=True,
    )

    _taxi_rank(
        name="Gateway / Umhlanga taxi pickup",
        suburb="Umhlanga",
        city="Umhlanga",
        province="KwaZulu-Natal",
        latitude=-29.7245,
        longitude=31.0651,
        notes="Demo taxi-rank record for commute testing.",
    )

    _taxi_rank(
        name="Durban Station taxi rank",
        suburb="CBD",
        city="Durban",
        province="KwaZulu-Natal",
        latitude=-29.8519,
        longitude=31.0256,
        notes="Major Durban public transport interchange.",
    )

    _taxi_rank(
        name="Sandton taxi rank",
        suburb="Sandton",
        city="Johannesburg",
        province="Gauteng",
        latitude=-26.1062,
        longitude=28.0560,
        notes="Demo taxi-rank record for Sandton commute testing.",
    )

    _taxi_rank(
        name="Noord taxi rank",
        suburb="CBD",
        city="Johannesburg",
        province="Gauteng",
        latitude=-26.1980,
        longitude=28.0462,
        notes="Demo taxi-rank record for central Johannesburg.",
    )

    _landlord_application(
        applicant=pending_landlord,
        message="I own rental rooms and would like admin approval to list them on Room Near Work.",
    )

    _rental_application(
        applicant=tenant,
        rental_property=prop1,
        message="I am interested in this room because it is close to my workplace.",
    )

    landlord.landlord_approved_at = landlord.landlord_approved_at or datetime.utcnow()
    landlord.landlord_approved_by_id = landlord.landlord_approved_by_id or admin.id

    db.session.commit()
