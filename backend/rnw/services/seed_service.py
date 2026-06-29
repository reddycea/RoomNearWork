from __future__ import annotations

from datetime import datetime, timedelta

from backend.rnw.extensions import db
from backend.rnw.models import (
    ConversationMessage,
    ConversationThread,
    LandlordApplication,
    Property,
    RentalApplication,
    RentalReview,
    SavedSearch,
    TaxiRank,
    User,
    UserSubscription,
    ViewingAppointment,
)
from backend.rnw.services.google_maps_service import geocode_property_address
from backend.rnw.services.listing_quality_service import update_listing_quality
from backend.rnw.services.subscription_service import ensure_default_plans


def _user(
    email: str,
    name: str,
    password: str,
    role: str,
    *,
    is_admin: bool = False,
    can_act_as_landlord: bool = False,
) -> User:
    user = User.query.filter_by(email=email).one_or_none()

    if not user:
        user = User(email=email)
        db.session.add(user)

    user.full_name = name
    user.role = role
    user.can_act_as_tenant = True
    user.can_act_as_landlord = can_act_as_landlord
    user.is_admin = is_admin
    user.is_active_account = True
    user.email_verified = True
    user.email_verified_at = user.email_verified_at or datetime.utcnow()
    user.set_password(password)

    db.session.flush()
    return user


def _active_subscription(user: User, role: str) -> UserSubscription:
    from backend.rnw.models import SubscriptionPlan

    plan_name = "Tenant Plus" if role == "tenant" else "Landlord Pro"

    plan = SubscriptionPlan.query.filter_by(name=plan_name).one()

    sub = (
        UserSubscription.query
        .filter_by(user_id=user.id, role=role, status="active")
        .order_by(UserSubscription.created_at.desc())
        .first()
    )

    if not sub:
        sub = UserSubscription(
            user_id=user.id,
            plan_id=plan.id,
            role=role,
            status="active",
        )
        db.session.add(sub)

    sub.plan_id = plan.id
    sub.status = "active"
    sub.current_period_end = datetime.utcnow() + timedelta(days=30)

    db.session.flush()
    return sub


def _landlord_application(
    applicant: User,
    *,
    status: str,
    admin: User | None = None,
    message: str | None = None,
    note: str | None = None,
) -> LandlordApplication:
    application = (
        LandlordApplication.query
        .filter_by(applicant_id=applicant.id)
        .order_by(LandlordApplication.created_at.desc())
        .first()
    )

    if not application:
        application = LandlordApplication(
            applicant_id=applicant.id,
            message=message,
        )
        db.session.add(application)
        db.session.flush()

    application.message = message or application.message

    if status == "approved":
        application.approve(admin.id if admin else None)
    elif status == "rejected":
        application.reject(note, admin.id if admin else None)
    else:
        application.status = "pending"
        application.admin_note = None
        application.reviewed_by_id = None
        application.reviewed_at = None

    db.session.flush()
    return application


def _property(
    landlord: User,
    *,
    title: str,
    description: str,
    rent: int,
    deposit: int,
    bedrooms: int,
    bathrooms: int,
    city: str,
    province: str,
    suburb: str,
    address: str,
    furnished: bool,
    pets_allowed: bool,
    transport_access: bool,
    nearest_transport: str,
    commute_notes: str,
    image_url: str,
    admin: User | None = None,
) -> Property:
    prop = Property.query.filter_by(title=title, landlord_id=landlord.id).one_or_none()

    if not prop:
        prop = Property(landlord_id=landlord.id, title=title)
        db.session.add(prop)

    geo = geocode_property_address(address, suburb, city, province)

    prop.description = description
    prop.rent_amount = rent
    prop.deposit_amount = deposit
    prop.bedrooms = bedrooms
    prop.bathrooms = bathrooms
    prop.city = city
    prop.province = province
    prop.suburb = suburb
    prop.address_line = address
    prop.formatted_address = geo.formatted_address
    prop.google_place_id = geo.place_id
    prop.approximate_address = f"{suburb}, {city}"
    prop.latitude = geo.latitude
    prop.longitude = geo.longitude
    prop.furnished = furnished
    prop.pets_allowed = pets_allowed
    prop.transport_access = transport_access
    prop.nearest_transport = nearest_transport
    prop.commute_notes = commute_notes
    prop.image_url = image_url
    prop.status = "available"
    prop.status_reason = None
    prop.is_active = True
    prop.listing_verified = True
    prop.verified_at = prop.verified_at or datetime.utcnow()
    prop.verified_by_id = admin.id if admin else None
    prop.expires_at = datetime.utcnow() + timedelta(days=45)

    update_listing_quality(prop)

    db.session.flush()
    return prop


def _taxi_rank(
    name: str,
    suburb: str,
    city: str,
    province: str,
    latitude: float,
    longitude: float,
    notes: str,
) -> TaxiRank:
    rank = TaxiRank.query.filter_by(name=name).one_or_none()

    if not rank:
        rank = TaxiRank(name=name)
        db.session.add(rank)

    rank.suburb = suburb
    rank.city = city
    rank.province = province
    rank.latitude = latitude
    rank.longitude = longitude
    rank.notes = notes
    rank.is_active = True

    db.session.flush()
    return rank


def _saved_search(
    user: User,
    *,
    name: str,
    city: str,
    province: str,
    max_rent: int,
    workplace_address: str,
    workplace_area: str,
) -> SavedSearch:
    search = SavedSearch.query.filter_by(user_id=user.id, name=name).one_or_none()

    if not search:
        search = SavedSearch(user_id=user.id, name=name)
        db.session.add(search)

    search.city = city
    search.province = province
    search.max_rent = max_rent
    search.min_bedrooms = 1
    search.furnished = None
    search.pets_allowed = None
    search.transport_access = True
    search.workplace_address = workplace_address
    search.workplace_formatted_address = workplace_address
    search.workplace_area = workplace_area
    search.travel_mode = "taxi"
    search.max_distance_km = 20
    search.max_travel_minutes = 45
    search.alerts_enabled = True

    db.session.flush()
    return search


def _rental_application(
    tenant: User,
    prop: Property,
    tenant_subscription: UserSubscription,
    *,
    message: str,
    status: str = "pending",
) -> RentalApplication:
    application = RentalApplication.query.filter_by(
        property_id=prop.id,
        applicant_id=tenant.id,
    ).one_or_none()

    if not application:
        application = RentalApplication(
            property_id=prop.id,
            applicant_id=tenant.id,
        )
        db.session.add(application)

    application.tenant_subscription_id = tenant_subscription.id
    application.message = message
    application.status = status

    db.session.flush()
    return application


def _conversation(
    tenant: User,
    landlord: User,
    prop: Property,
) -> ConversationThread:
    thread = ConversationThread.query.filter_by(
        property_id=prop.id,
        tenant_id=tenant.id,
        landlord_id=landlord.id,
    ).one_or_none()

    if not thread:
        thread = ConversationThread(
            property_id=prop.id,
            tenant_id=tenant.id,
            landlord_id=landlord.id,
            status="open",
        )
        db.session.add(thread)
        db.session.flush()

    thread.last_message_at = datetime.utcnow()

    if ConversationMessage.query.filter_by(thread_id=thread.id).count() == 0:
        db.session.add(
            ConversationMessage(
                thread_id=thread.id,
                sender_id=tenant.id,
                body="Hi, I am interested in this room. Is it still available?",
            )
        )
        db.session.add(
            ConversationMessage(
                thread_id=thread.id,
                sender_id=landlord.id,
                body="Yes, it is still available. You can request a viewing.",
            )
        )

    db.session.flush()
    return thread


def _viewing(
    tenant: User,
    landlord: User,
    prop: Property,
) -> ViewingAppointment:
    viewing = ViewingAppointment.query.filter_by(
        property_id=prop.id,
        tenant_id=tenant.id,
        landlord_id=landlord.id,
    ).first()

    if not viewing:
        start = datetime.utcnow() + timedelta(days=2, hours=2)
        viewing = ViewingAppointment(
            property_id=prop.id,
            tenant_id=tenant.id,
            landlord_id=landlord.id,
            requested_start=start,
            requested_end=start + timedelta(minutes=45),
            status="approved",
            tenant_note="I can view after work.",
            landlord_note="Approved. Please bring ID.",
        )
        db.session.add(viewing)

    db.session.flush()
    return viewing


def _review(
    tenant: User,
    landlord: User,
    prop: Property,
    *,
    rating: int,
    title: str,
    comment: str,
    admin: User | None = None,
) -> RentalReview:
    review = RentalReview.query.filter_by(
        property_id=prop.id,
        tenant_id=tenant.id,
    ).one_or_none()

    if not review:
        review = RentalReview(
            property_id=prop.id,
            tenant_id=tenant.id,
            landlord_id=landlord.id,
        )
        db.session.add(review)

    review.rating = rating
    review.accuracy_rating = rating
    review.safety_rating = rating
    review.commute_rating = rating
    review.landlord_communication_rating = rating
    review.title = title
    review.comment = comment
    review.status = "approved"
    review.reviewed_by_id = admin.id if admin else None
    review.reviewed_at = review.reviewed_at or datetime.utcnow()

    db.session.flush()
    return review


def seed_database() -> None:
    """
    Seed RoomNearWork with demo users, subscriptions, listings,
    landlord applications, tenant activity, taxi ranks and reviews.

    Safe to run multiple times.
    """

    ensure_default_plans()
    db.session.flush()

    admin = _user(
        "admin@rnw.local",
        "RNW Admin",
        "AdminPass123!",
        "admin",
        is_admin=True,
        can_act_as_landlord=True,
    )

    landlord = _user(
        "landlord@rnw.local",
        "Lebo Landlord",
        "LandlordPass123!",
        "landlord",
        can_act_as_landlord=True,
    )

    tenant = _user(
        "tenant@rnw.local",
        "Tumi Tenant",
        "TenantPass123!",
        "tenant",
        can_act_as_landlord=False,
    )

    pending_landlord = _user(
        "pending-landlord@rnw.local",
        "Ayanda Pending",
        "PendingPass123!",
        "tenant",
        can_act_as_landlord=False,
    )

    _landlord_application(
        landlord,
        status="approved",
        admin=admin,
        message="I own and manage rooms suitable for workers and students.",
    )

    _landlord_application(
        pending_landlord,
        status="pending",
        admin=admin,
        message="I want to list two rooms near transport routes.",
    )

    tenant_subscription = _active_subscription(tenant, "tenant")
    _active_subscription(landlord, "landlord")

    properties = [
        _property(
            landlord,
            title="Compact room near Sandton",
            description=(
                "A secure modern room with fast access to Sandton offices, taxi routes, "
                "shops and daily services. Ideal for a young professional looking for a "
                "clean and reliable commute."
            ),
            rent=3500,
            deposit=3500,
            bedrooms=1,
            bathrooms=1,
            city="Johannesburg",
            province="Gauteng",
            suburb="Sandton",
            address="12 Rivonia Road",
            furnished=True,
            pets_allowed=False,
            transport_access=True,
            nearest_transport="Sandton taxi rank and Gautrain bus routes",
            commute_notes="Good access to Sandton CBD, Rivonia Road and nearby office parks.",
            image_url="https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
            admin=admin,
        ),
        _property(
            landlord,
            title="Sunny apartment close to Braamfontein CBD",
            description=(
                "Bright apartment with natural light, simple finishes and fast access to "
                "Braamfontein, Park Station, Wits and Johannesburg CBD workplaces."
            ),
            rent=5200,
            deposit=5200,
            bedrooms=1,
            bathrooms=1,
            city="Johannesburg",
            province="Gauteng",
            suburb="Braamfontein",
            address="22 Jorissen Street",
            furnished=False,
            pets_allowed=False,
            transport_access=True,
            nearest_transport="Park Station and Noord taxi routes",
            commute_notes="Strong public transport access into central Johannesburg.",
            image_url="https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
            admin=admin,
        ),
        _property(
            landlord,
            title="Quiet room near Umhlanga offices",
            description=(
                "Quiet lock-up room in a shared home near Umhlanga offices, malls, taxi "
                "routes and coastal work opportunities. Suitable for weekly commuting "
                "professionals."
            ),
            rent=4200,
            deposit=4200,
            bedrooms=1,
            bathrooms=1,
            city="Umhlanga",
            province="KwaZulu-Natal",
            suburb="Umhlanga",
            address="11 Park Avenue",
            furnished=True,
            pets_allowed=False,
            transport_access=True,
            nearest_transport="Gateway and Umhlanga taxi pickup points",
            commute_notes="Convenient for Gateway, Umhlanga Ridge and nearby office parks.",
            image_url="https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
            admin=admin,
        ),
        _property(
            landlord,
            title="Affordable room near Phoenix taxi routes",
            description=(
                "Budget-friendly room with transport access into Umhlanga and Durban. "
                "Good for shift workers, students and weekly commuters who need an "
                "affordable base."
            ),
            rent=2800,
            deposit=2800,
            bedrooms=1,
            bathrooms=1,
            city="Durban",
            province="KwaZulu-Natal",
            suburb="Phoenix",
            address="19 Phoenix Highway",
            furnished=False,
            pets_allowed=False,
            transport_access=True,
            nearest_transport="Phoenix taxi routes",
            commute_notes="Useful access toward Durban, Gateway and surrounding areas.",
            image_url="https://images.unsplash.com/photo-1493809842364-78817add7ffb",
            admin=admin,
        ),
    ]

    taxi_ranks = [
        (
            "Gateway / Umhlanga taxi pickup",
            "Umhlanga",
            "Umhlanga",
            "KwaZulu-Natal",
            -29.7245,
            31.0651,
            "Demo taxi-rank record for Umhlanga commute testing.",
        ),
        (
            "Durban Station taxi rank",
            "CBD",
            "Durban",
            "KwaZulu-Natal",
            -29.8519,
            31.0256,
            "Major Durban public transport interchange.",
        ),
        (
            "Sandton taxi rank",
            "Sandton",
            "Johannesburg",
            "Gauteng",
            -26.1062,
            28.0560,
            "Demo taxi-rank record for Sandton workplace commute testing.",
        ),
        (
            "Noord taxi rank",
            "CBD",
            "Johannesburg",
            "Gauteng",
            -26.1980,
            28.0462,
            "Demo taxi-rank record for central Johannesburg.",
        ),
        (
            "Park Station taxi rank",
            "Braamfontein",
            "Johannesburg",
            "Gauteng",
            -26.1952,
            28.0416,
            "Demo transport node for Braamfontein and Johannesburg CBD.",
        ),
    ]

    for rank in taxi_ranks:
        _taxi_rank(*rank)

    _saved_search(
        tenant,
        name="Work near Sandton under R4000",
        city="Johannesburg",
        province="Gauteng",
        max_rent=4000,
        workplace_address="Sandton City, Johannesburg",
        workplace_area="Sandton",
    )

    _saved_search(
        tenant,
        name="Umhlanga taxi access",
        city="Umhlanga",
        province="KwaZulu-Natal",
        max_rent=5000,
        workplace_address="Gateway Theatre of Shopping, Umhlanga",
        workplace_area="Umhlanga",
    )

    first_property = properties[0]
    third_property = properties[2]

    _rental_application(
        tenant,
        first_property,
        tenant_subscription,
        message="I work nearby and would like to arrange a viewing.",
        status="pending",
    )

    _rental_application(
        tenant,
        third_property,
        tenant_subscription,
        message="I am interested because it is close to Umhlanga offices.",
        status="approved",
    )

    _conversation(tenant, landlord, first_property)
    _viewing(tenant, landlord, third_property)

    _review(
        tenant,
        landlord,
        third_property,
        rating=5,
        title="Good commute and clean room",
        comment="The room was clean, the landlord communicated well, and transport access was convenient.",
        admin=admin,
    )

    db.session.commit()
