from backend.rnw.extensions import db
from backend.rnw.models import BillingInvoice, User
from backend.rnw.services.billing_service import activate_subscription_from_invoice, create_invoice
from backend.rnw.services.subscription_service import get_default_plan_for_role


def test_invoice_activation_creates_subscription(app):
    with app.app_context():
        user = User(email="billtenant@test.local", first_name="Bill", last_name="Tenant", role="tenant")
        user.set_password("StrongPass123!")
        db.session.add(user)
        db.session.flush()
        plan = get_default_plan_for_role("tenant")
        invoice = create_invoice(user, plan, provider="sandbox")
        activate_subscription_from_invoice(invoice)
        db.session.commit()
        assert BillingInvoice.query.filter_by(user_id=user.id, status="paid").count() == 1
        assert user.has_active_subscription()
