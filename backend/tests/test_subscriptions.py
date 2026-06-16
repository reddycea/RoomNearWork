def test_subscription_plans_api_contains_rnw_prices(client):
    response = client.get("/billing/api/plans")
    assert response.status_code == 200
    plans = {item["role"]: item for item in response.get_json()["data"]}
    assert plans["tenant"]["price"] == 50
    assert plans["tenant"]["price_label"] == "R50pm"
    assert plans["landlord"]["price"] == 100
    assert plans["landlord"]["price_label"] == "R100pm"


def test_seed_users_have_active_subscriptions(app):
    from rnw.models import User

    with app.app_context():
        tenant = User.query.filter_by(email="tenant@rnw.local").first()
        landlord = User.query.filter_by(email="landlord@rnw.local").first()
        assert tenant.has_active_subscription()
        assert landlord.has_active_subscription()
        assert tenant.active_subscription.plan.price == 50
        assert landlord.active_subscription.plan.price == 100
