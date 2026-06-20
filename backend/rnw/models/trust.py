from __future__ import annotations

import secrets

from backend.rnw.extensions import db
from .base import TimestampMixin


class SupportTicket(TimestampMixin, db.Model):
    __tablename__ = "support_tickets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    public_token = db.Column(db.String(96), unique=True, index=True, default=lambda: secrets.token_urlsafe(32), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default="open", nullable=False)

    user = db.relationship("User")


class ListingReport(TimestampMixin, db.Model):
    __tablename__ = "listing_reports"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    reason = db.Column(db.String(120), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(40), default="open", nullable=False, index=True)

    property = db.relationship("Property")
    reporter = db.relationship("User")


class LandlordVerification(TimestampMixin, db.Model):
    __tablename__ = "landlord_verifications"

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    document_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    notes = db.Column(db.Text)

    landlord = db.relationship("User", foreign_keys=[landlord_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])
