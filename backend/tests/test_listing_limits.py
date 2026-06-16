from backend.rnw.extensions import db
from backend.rnw.models import Property, User
from backend.rnw.services.subscription_service import get_default_plan_for_role, landlord_can_create_listing, subscribe_user


def test_landlord_listing_limit(app):
    with app.app_context():
        landlord = User(email="limitlandlord@test.local", first_name="Limit", last_name="Landlord", role="landlord")
        landlord.set_password("StrongPass123!")
        db.session.add(landlord)
        db.session.flush()
        plan = get_default_plan_for_role("landlord")
        subscribe_user(landlord, plan, provider="test")
        db.session.flush()
        for index in range(plan.max_listings):
            db.session.add(Property(
                landlord_id=landlord.id,
                title=f"Listing {index}",
                description="Test listing",
                property_type="room",
                address="Main Road",
                city="Empangeni",
                province="KwaZulu-Natal",
                price=3000,
                status="approved",
            ))
        db.session.commit()
        can_create, limit, count = landlord_can_create_listing(landlord)
        assert can_create is False
        assert count == limit == plan.max_listings
