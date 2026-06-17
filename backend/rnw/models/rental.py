from __future__ import annotations
from builtins import property as builtin_property
from datetime import datetime, timedelta

from ..extensions import db
from .base import TimestampMixin


class Inquiry(TimestampMixin, db.Model):
    __tablename__ = "inquiries"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)

    property = db.relationship("Property", back_populates="inquiries")
    sender = db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    @builtin_property
    def is_reply_needed(self) -> bool:
        return (not self.is_read) and self.created_at > datetime.utcnow() - timedelta(days=2)


class RentalApplication(TimestampMixin, db.Model):
    __tablename__ = "rental_applications"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)  # pending, approved, rejected, withdrawn
    message = db.Column(db.Text, nullable=True)
    monthly_income = db.Column(db.Float, nullable=True)
    employment_status = db.Column(db.String(50), nullable=True)
    employer_name = db.Column(db.String(100), nullable=True)
    years_employed = db.Column(db.Float, nullable=True)
    has_pets = db.Column(db.Boolean, default=False, nullable=False)
    number_of_occupants = db.Column(db.Integer, default=1)
    move_in_date = db.Column(db.Date, nullable=True)
    lease_term = db.Column(db.Integer, default=12)
    rating = db.Column(db.Integer, nullable=True)
    review_text = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)

    property = db.relationship("Property", back_populates="applications")
    applicant = db.relationship("User", back_populates="applications")

    __table_args__ = (db.UniqueConstraint("property_id", "applicant_id", name="uq_property_applicant"),)

    def approve(self) -> None:
        self.status = "approved"
        self.reviewed_at = datetime.utcnow()

    def reject(self) -> None:
        self.status = "rejected"
        self.reviewed_at = datetime.utcnow()
