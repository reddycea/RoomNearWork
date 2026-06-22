from __future__ import annotations

import builtins
import hashlib
import secrets
from datetime import datetime, timedelta

from backend.rnw.extensions import db
from .base import TimestampMixin


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class SavedSearch(TimestampMixin, db.Model):
    __tablename__ = "saved_searches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), index=True)
    province = db.Column(db.String(120), index=True)
    max_rent = db.Column(db.Integer)
    min_bedrooms = db.Column(db.Integer)
    furnished = db.Column(db.Boolean)
    pets_allowed = db.Column(db.Boolean)
    transport_access = db.Column(db.Boolean)
    workplace_address = db.Column(db.String(500))
    workplace_formatted_address = db.Column(db.String(500))
    workplace_place_id = db.Column(db.String(255), index=True)
    workplace_area = db.Column(db.String(160), index=True)
    workplace_latitude = db.Column(db.Float)
    workplace_longitude = db.Column(db.Float)
    travel_mode = db.Column(db.String(40), default="all", nullable=False)
    max_distance_km = db.Column(db.Float)
    max_travel_minutes = db.Column(db.Integer)
    alerts_enabled = db.Column(db.Boolean, default=True, nullable=False)
    last_alerted_at = db.Column(db.DateTime)

    user = db.relationship("User")

    __table_args__ = (db.UniqueConstraint("user_id", "name", name="uq_saved_search_user_name"),)


class ConversationThread(TimestampMixin, db.Model):
    __tablename__ = "conversation_threads"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(40), default="open", nullable=False)
    last_message_at = db.Column(db.DateTime)

    property = db.relationship("Property")
    tenant = db.relationship("User", foreign_keys=[tenant_id])
    landlord = db.relationship("User", foreign_keys=[landlord_id])
    messages = db.relationship("ConversationMessage", back_populates="thread", cascade="all, delete-orphan", order_by="ConversationMessage.created_at")

    __table_args__ = (db.UniqueConstraint("property_id", "tenant_id", "landlord_id", name="uq_thread_property_tenant_landlord"),)


class ConversationMessage(TimestampMixin, db.Model):
    __tablename__ = "conversation_messages"

    id = db.Column(db.Integer, primary_key=True)
    thread_id = db.Column(db.Integer, db.ForeignKey("conversation_threads.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime)

    thread = db.relationship("ConversationThread", back_populates="messages")
    sender = db.relationship("User")


class ViewingAppointment(TimestampMixin, db.Model):
    __tablename__ = "viewing_appointments"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    requested_start = db.Column(db.DateTime, nullable=False)
    requested_end = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    tenant_note = db.Column(db.Text)
    landlord_note = db.Column(db.Text)

    property = db.relationship("Property")
    tenant = db.relationship("User", foreign_keys=[tenant_id])
    landlord = db.relationship("User", foreign_keys=[landlord_id])


class UserAuditLog(TimestampMixin, db.Model):
    __tablename__ = "user_audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    action = db.Column(db.String(120), nullable=False, index=True)
    target_type = db.Column(db.String(80))
    target_id = db.Column(db.String(80))
    ip_address = db.Column(db.String(64))
    user_agent = db.Column(db.String(255))
    metadata_json = db.Column(db.Text)

    actor = db.relationship("User")


class EmailVerificationToken(TimestampMixin, db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)

    user = db.relationship("User")

    @classmethod
    def issue(cls, user_id: int, hours: int = 24) -> tuple["EmailVerificationToken", str]:
        raw = secrets.token_urlsafe(32)
        token = cls(user_id=user_id, token_hash=hash_token(raw), expires_at=datetime.utcnow() + timedelta(hours=hours))
        return token, raw

    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > datetime.utcnow()


class PasswordResetToken(TimestampMixin, db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)

    user = db.relationship("User")

    @classmethod
    def issue(cls, user_id: int, minutes: int = 60) -> tuple["PasswordResetToken", str]:
        raw = secrets.token_urlsafe(32)
        token = cls(user_id=user_id, token_hash=hash_token(raw), expires_at=datetime.utcnow() + timedelta(minutes=minutes))
        return token, raw

    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > datetime.utcnow()


class PlacesSession(TimestampMixin, db.Model):
    """Short-lived Google Places autocomplete session for cost control and address confirmation.

    The raw token is sent to the browser and Google. We store only a hash so leaked DB dumps
    do not expose active session tokens. Sessions are intentionally lightweight and can be
    cleaned up by a scheduled job.
    """

    __tablename__ = "places_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    purpose = db.Column(db.String(80), default="workplace_search", nullable=False)
    selected_place_id = db.Column(db.String(255))
    selected_description = db.Column(db.String(500))
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)

    user = db.relationship("User")

    @classmethod
    def issue(cls, user_id: int | None = None, purpose: str = "workplace_search", minutes: int = 5) -> tuple["PlacesSession", str]:
        raw = secrets.token_urlsafe(24)
        session = cls(
            user_id=user_id,
            token_hash=hash_token(raw),
            purpose=purpose,
            expires_at=datetime.utcnow() + timedelta(minutes=minutes),
        )
        return session, raw

    def mark_used(self, place_id: str | None, description: str | None = None) -> None:
        self.selected_place_id = place_id
        self.selected_description = description
        self.used_at = datetime.utcnow()

    def is_valid(self) -> bool:
        return self.expires_at > datetime.utcnow()


class TaxiRank(TimestampMixin, db.Model):
    """Simple RNW-owned taxi-rank dataset for South African commute estimates.

    Google has no dedicated minibus taxi mode, so this table lets RNW build local
    transport intelligence over time. It can be seeded manually or crowdsourced later.
    """

    __tablename__ = "taxi_ranks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    suburb = db.Column(db.String(120), index=True)
    city = db.Column(db.String(120), index=True)
    province = db.Column(db.String(120), index=True)
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class RentalReview(TimestampMixin, db.Model):
    """Tenant review of a rental/listing after a viewing, application, or completed stay."""

    __tablename__ = "rental_reviews"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    accuracy_rating = db.Column(db.Integer)
    safety_rating = db.Column(db.Integer)
    commute_rating = db.Column(db.Integer)
    landlord_communication_rating = db.Column(db.Integer)
    title = db.Column(db.String(140), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    admin_note = db.Column(db.Text)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)

    property = db.relationship("Property", back_populates="reviews")
    tenant = db.relationship("User", foreign_keys=[tenant_id])
    landlord = db.relationship("User", foreign_keys=[landlord_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        db.UniqueConstraint("property_id", "tenant_id", name="uq_rental_review_property_tenant"),
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_rental_reviews_rating_range"),
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "pending")
        super().__init__(**kwargs)

    @builtins.property
    def public_comment(self) -> str:
        return self.comment or ""
