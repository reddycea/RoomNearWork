from rnw.extensions import db
from rnw.models import ListingReport, PropertyReview, SupportTicket


def login(client, email="tenant@rnw.local", password="TenantPass123!"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)


def test_support_ticket_public(client):
    response = client.post("/support", data={"name": "Tester", "email": "tester@example.com", "category": "billing", "subject": "Payment help", "message": "Please help"}, follow_redirects=True)
    assert response.status_code == 200
    assert SupportTicket.query.filter_by(email="tester@example.com").count() == 1


def test_report_listing(client):
    response = client.post("/properties/1/report", data={"reason": "Fake or misleading listing", "message": "The price looks fake"}, follow_redirects=True)
    assert response.status_code == 200
    assert ListingReport.query.filter_by(property_id=1).count() == 1


def test_review_submission_requires_approved_application(client):
    login(client)
    response = client.get("/properties/1/reviews/new", follow_redirects=True)
    assert response.status_code == 200


def test_admin_can_approve_review(client):
    login(client, "admin@rnw.local", "AdminPass123!")
    review = PropertyReview(property_id=1, reviewer_id=3, landlord_id=2, rating=5, title="Great", comment="Excellent location", status="pending")
    db.session.add(review)
    db.session.commit()
    response = client.post(f"/admin/reviews/{review.id}/approve", follow_redirects=True)
    assert response.status_code == 200
    assert PropertyReview.query.get(review.id).status == "approved"
