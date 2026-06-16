from __future__ import annotations

from datetime import datetime

from ..extensions import db
from .base import TimestampMixin


class PropertyReview(TimestampMixin, db.Model):
    """Moderated tenant review for a property/listing.

    Reviews are designed to be trustworthy: by default a tenant can review only
    once per property and only after an approved rental application. Admins can
    moderate abusive or fake reviews before they affect public ratings.
    """

    __tablename__ = "property_reviews"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rental_application_id = db.Column(db.Integer, db.ForeignKey("rental_applications.id"), nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)  # pending, approved, rejected
    landlord_response = db.Column(db.Text, nullable=True)
    landlord_responded_at = db.Column(db.DateTime, nullable=True)
    moderated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    moderated_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    property = db.relationship("Property", back_populates="reviews")
    reviewer = db.relationship("User", foreign_keys=[reviewer_id], back_populates="reviews")
    landlord = db.relationship("User", foreign_keys=[landlord_id], back_populates="landlord_reviews")
    application = db.relationship("RentalApplication")

    __table_args__ = (
        db.UniqueConstraint("property_id", "reviewer_id", name="uq_property_reviewer"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_property_review_rating"),
    )

    @property
    def is_public(self) -> bool:
        return self.status == "approved"

    def approve(self, admin_id: int | None = None) -> None:
        self.status = "approved"
        self.moderated_by = admin_id
        self.moderated_at = datetime.utcnow()
        self.rejection_reason = None

    def reject(self, reason: str | None = None, admin_id: int | None = None) -> None:
        self.status = "rejected"
        self.rejection_reason = reason
        self.moderated_by = admin_id
        self.moderated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "property_id": self.property_id,
            "reviewer": self.reviewer.full_name if self.reviewer else None,
            "rating": self.rating,
            "title": self.title,
            "comment": self.comment,
            "status": self.status,
            "landlord_response": self.landlord_response,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ListingReport(TimestampMixin, db.Model):
    __tablename__ = "listing_reports"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    reporter_name = db.Column(db.String(120), nullable=True)
    reporter_email = db.Column(db.String(120), nullable=True)
    reason = db.Column(db.String(80), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False, index=True)  # open, investigating, resolved, dismissed
    admin_notes = db.Column(db.Text, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    property = db.relationship("Property", back_populates="reports")
    reporter = db.relationship("User", foreign_keys=[reporter_id], back_populates="listing_reports")

    def close(self, status: str, admin_id: int | None = None, notes: str | None = None) -> None:
        self.status = status
        self.resolved_by = admin_id
        self.admin_notes = notes
        self.resolved_at = datetime.utcnow()


class SupportTicket(TimestampMixin, db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="general", index=True)
    subject = db.Column(db.String(160), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="open", nullable=False, index=True)  # open, pending_user, resolved, closed
    priority = db.Column(db.String(20), default="normal", nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    admin_response = db.Column(db.Text, nullable=True)
    responded_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="support_tickets")
    assignee = db.relationship("User", foreign_keys=[assigned_to])

    def respond(self, admin_id: int, response: str, status: str = "pending_user") -> None:
        self.assigned_to = admin_id
        self.admin_response = response
        self.responded_at = datetime.utcnow()
        self.status = status
        if status in {"resolved", "closed"}:
            self.closed_at = datetime.utcnow()


class LegalConsent(TimestampMixin, db.Model):
    __tablename__ = "legal_consents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    email = db.Column(db.String(120), nullable=True, index=True)
    consent_type = db.Column(db.String(50), nullable=False, index=True)  # terms, privacy, popia, marketing
    version = db.Column(db.String(20), nullable=False, default="2026-06")
    accepted = db.Column(db.Boolean, nullable=False, default=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    accepted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="legal_consents")


class PaymentWebhookLog(TimestampMixin, db.Model):
    __tablename__ = "payment_webhook_logs"

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(30), nullable=False, index=True)
    reference = db.Column(db.String(120), nullable=True, index=True)
    external_id = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(50), nullable=True, index=True)
    valid_signature = db.Column(db.Boolean, default=False, nullable=False)
    payload = db.Column(db.Text, nullable=False)
    processed_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)

    def mark_processed(self) -> None:
        self.processed_at = datetime.utcnow()
