from __future__ import annotations

from backend.rnw.extensions import db
from .base import TimestampMixin


class RentalApplication(TimestampMixin, db.Model):
    __tablename__ = "rental_applications"

    id = db.Column(db.Integer, primary_key=True)

    property_id = db.Column(
        db.Integer,
        db.ForeignKey("properties.id"),
        nullable=False,
        index=True,
    )

    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    tenant_subscription_id = db.Column(
        db.Integer,
        db.ForeignKey("user_subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    message = db.Column(db.Text)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)

    property = db.relationship("Property", back_populates="applications")
    applicant = db.relationship("User", back_populates="applications")
    tenant_subscription = db.relationship("UserSubscription")

    __table_args__ = (
        db.UniqueConstraint(
            "property_id",
            "applicant_id",
            name="uq_application_property_applicant",
        ),
    )
