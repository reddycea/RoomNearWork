from __future__ import annotations

from datetime import date, datetime

from ..extensions import db
from ..models import Property, PropertyReview, RentalApplication, SupportTicket, User
from .subscription_service import ensure_default_plans, get_default_plan_for_role, subscribe_user


def _get_or_create_user(email: str, password: str, role: str, first_name: str, last_name: str, province: str) -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone="0710000000",
        role=role,
        province=province,
        is_verified=role in {"admin", "landlord"},
        email_verified_at=datetime.utcnow(),
    )
    user.set_password(password)
    db.session.add(user)
    return user


def seed_database() -> None:
    db.create_all()

    admin = _get_or_create_user("admin@rnw.local", "AdminPass123!", "admin", "RNW", "Admin", "Gauteng")
    landlord = _get_or_create_user("landlord@rnw.local", "LandlordPass123!", "landlord", "Lindiwe", "Mkhize", "KwaZulu-Natal")
    tenant = _get_or_create_user("tenant@rnw.local", "TenantPass123!", "tenant", "Thabo", "Dlamini", "KwaZulu-Natal")
    db.session.flush()

    ensure_default_plans()
    db.session.flush()
    if not tenant.has_active_subscription():
        subscribe_user(tenant, get_default_plan_for_role("tenant"), provider="seed")
    if not landlord.has_active_subscription():
        subscribe_user(landlord, get_default_plan_for_role("landlord"), provider="seed")

    if not Property.query.first():
        demo_properties = [
            Property(
                landlord_id=landlord.id,
                title="Modern Room Near Empangeni CBD",
                description="Secure furnished room close to transport, shops, and workplaces.",
                property_type="room",
                address="Main Road, Empangeni",
                city="Empangeni",
                province="KwaZulu-Natal",
                latitude=-28.7619,
                longitude=31.8932,
                price=3200,
                deposit_amount=3200,
                bedrooms=1,
                bathrooms=1,
                parking=1,
                area_sqm=28,
                furnished=True,
                transport_access="Taxi rank 500m away; close to CBD",
                available_date=date.today(),
                status="approved",
            ),
            Property(
                landlord_id=landlord.id,
                title="Two Bedroom Apartment in Richards Bay",
                description="Family-friendly apartment with parking and quick access to industrial areas.",
                property_type="apartment",
                address="Meerensee, Richards Bay",
                city="Richards Bay",
                province="KwaZulu-Natal",
                latitude=-28.7807,
                longitude=32.0383,
                price=7200,
                deposit_amount=7200,
                bedrooms=2,
                bathrooms=1.5,
                parking=1,
                area_sqm=68,
                pets_allowed=True,
                transport_access="Quick access to industrial areas and public transport",
                status="approved",
            ),
            Property(
                landlord_id=landlord.id,
                title="Studio Apartment in Sandton",
                description="Compact studio for professionals near offices and Gautrain.",
                property_type="studio",
                address="Rivonia Road, Sandton",
                city="Sandton",
                province="Gauteng",
                latitude=-26.1076,
                longitude=28.0567,
                price=8500,
                deposit_amount=8500,
                bedrooms=0,
                bathrooms=1,
                parking=1,
                area_sqm=38,
                furnished=True,
                transport_access="Near Gautrain and office nodes",
                status="approved",
            ),
        ]
        db.session.add_all(demo_properties)


    db.session.flush()
    first_property = Property.query.order_by(Property.id.asc()).first()
    if first_property and not RentalApplication.query.filter_by(property_id=first_property.id, applicant_id=tenant.id).first():
        db.session.add(RentalApplication(
            property_id=first_property.id,
            applicant_id=tenant.id,
            status="approved",
            message="I work near Empangeni CBD and need a safe room.",
            monthly_income=12500,
            employment_status="employed",
            employer_name="Demo Employer",
            years_employed=2,
            number_of_occupants=1,
            lease_term=12,
        ))
        db.session.flush()
    application = RentalApplication.query.filter_by(property_id=first_property.id, applicant_id=tenant.id).first() if first_property else None
    if first_property and application and not PropertyReview.query.filter_by(property_id=first_property.id, reviewer_id=tenant.id).first():
        db.session.add(PropertyReview(
            property_id=first_property.id,
            reviewer_id=tenant.id,
            landlord_id=landlord.id,
            rental_application_id=application.id,
            rating=5,
            title="Great location for work",
            comment="The room is close to transport and the listing details were accurate.",
            status="approved",
        ))
    if not SupportTicket.query.first():
        db.session.add(SupportTicket(
            user_id=tenant.id,
            name=tenant.full_name,
            email=tenant.email,
            category="billing",
            subject="Demo payment question",
            message="I want to confirm my Tenant Plus subscription.",
            priority="high",
        ))

    db.session.commit()
