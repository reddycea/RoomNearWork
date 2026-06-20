from __future__ import annotations

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
