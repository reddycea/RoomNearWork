from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db, login_manager
from .base import TimestampMixin


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    id_number = db.Column(db.String(13), unique=True, nullable=True)
    role = db.Column(db.String(20), default="tenant", index=True)  # tenant, landlord, admin
    province = db.Column(db.String(50), nullable=True)
    is_verified = db.Column(db.Boolean, default=False, nullable=False)  # landlord/admin verification, not email verification
    email_verified_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_password_reset_at = db.Column(db.DateTime, nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    properties = db.relationship("Property", back_populates="landlord", cascade="all, delete-orphan")
    saved_properties = db.relationship("SavedProperty", back_populates="user", cascade="all, delete-orphan")
    searches = db.relationship("SearchHistory", back_populates="user", cascade="all, delete-orphan")
    applications = db.relationship("RentalApplication", back_populates="applicant", cascade="all, delete-orphan")
    verification = db.relationship("LandlordVerification", foreign_keys="LandlordVerification.user_id", back_populates="user", uselist=False, cascade="all, delete-orphan")
    subscriptions = db.relationship("UserSubscription", back_populates="user", cascade="all, delete-orphan", order_by="UserSubscription.created_at.desc()")
    invoices = db.relationship("BillingInvoice", back_populates="user", cascade="all, delete-orphan", order_by="BillingInvoice.created_at.desc()")
    auth_tokens = db.relationship("AuthToken", back_populates="user", cascade="all, delete-orphan")
    reviews = db.relationship(
        "PropertyReview",
        foreign_keys="PropertyReview.reviewer_id",
        back_populates="reviewer",
        cascade="all, delete-orphan",
    )
    
    landlord_reviews = db.relationship(
        "PropertyReview",
        foreign_keys="PropertyReview.landlord_id",
        back_populates="landlord",
    )
    
    listing_reports = db.relationship(
        "ListingReport",
        foreign_keys="ListingReport.reporter_id",
        back_populates="reporter",
        cascade="all, delete-orphan",
    )
    
    support_tickets = db.relationship(
        "SupportTicket",
        foreign_keys="SupportTicket.user_id",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    legal_consents = db.relationship(
        "LegalConsent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
        self.last_password_reset_at = datetime.utcnow()

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    def has_role(self, *roles: str) -> bool:
        return self.role in roles

    @property
    def active_subscription(self):
        from .subscription import SubscriptionPlan, UserSubscription

        return (
            UserSubscription.query
            .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
            .filter(
                UserSubscription.user_id == self.id,
                UserSubscription.status == "active",
                SubscriptionPlan.role == self.role,
                SubscriptionPlan.is_active.is_(True),
            )
            .order_by(UserSubscription.end_date.desc())
            .first()
        )

    def has_active_subscription(self) -> bool:
        if self.role == "admin":
            return True
        subscription = self.active_subscription
        return bool(subscription and subscription.is_current)

    def active_listing_count(self) -> int:
        from .property import Property
        if not self.id:
            return 0
        return Property.query.filter(
            Property.landlord_id == self.id,
            Property.status.in_(["pending", "approved"]),
            Property.is_available.is_(True),
        ).count()

    def listing_limit(self) -> int | None:
        if self.role == "admin":
            return None
        subscription = self.active_subscription
        if not subscription or not subscription.plan:
            return 0
        return subscription.plan.max_listings

    def can_create_listing(self) -> bool:
        limit = self.listing_limit()
        return limit is None or self.active_listing_count() < limit

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role,
            "province": self.province,
            "is_verified": self.is_verified,
            "email_verified": self.email_verified,
            "has_active_subscription": self.has_active_subscription(),
            "listing_limit": self.listing_limit(),
            "active_listing_count": self.active_listing_count() if self.role == "landlord" else None,
        }


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    if not user_id or not user_id.isdigit():
        return None
    return db.session.get(User, int(user_id))


class AuthToken(TimestampMixin, db.Model):
    __tablename__ = "auth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token_hash = db.Column(db.String(128), nullable=False, unique=True, index=True)
    purpose = db.Column(db.String(30), nullable=False, index=True)  # email_verify, password_reset
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", back_populates="auth_tokens")

    @property
    def is_valid(self) -> bool:
        return self.used_at is None and self.expires_at > datetime.utcnow()

    def consume(self) -> None:
        self.used_at = datetime.utcnow()


class LoginAttempt(db.Model):
    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True, index=True)
    success = db.Column(db.Boolean, default=False, nullable=False, index=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)


class LandlordVerification(TimestampMixin, db.Model):
    __tablename__ = "landlord_verifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    id_document_url = db.Column(db.String(255), nullable=False)
    proof_of_address_url = db.Column(db.String(255), nullable=False)
    tax_clearance_url = db.Column(db.String(255), nullable=True)
    business_registration_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default="pending", index=True)  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="verification")
