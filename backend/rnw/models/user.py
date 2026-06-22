from __future__ import annotations

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from backend.rnw.extensions import db, login_manager
from .base import TimestampMixin


class User(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(30), default="tenant", nullable=False)  # active role
    can_act_as_tenant = db.Column(db.Boolean, default=True, nullable=False)
    can_act_as_landlord = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)

    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    email_verified_at = db.Column(db.DateTime)
    failed_login_count = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(db.String(64))

    two_factor_secret = db.Column(db.String(64))
    two_factor_enabled = db.Column(db.Boolean, default=False, nullable=False)

    properties = db.relationship(
        "Property",
        back_populates="landlord",
        foreign_keys="Property.landlord_id",
        lazy="dynamic",
    )
    applications = db.relationship("RentalApplication", back_populates="applicant", lazy="dynamic")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_active(self) -> bool:  # Flask-Login property
        return self.is_active_account

    def available_roles(self) -> list[str]:
        roles: list[str] = []
        if self.can_act_as_tenant:
            roles.append("tenant")
        if self.can_act_as_landlord:
            roles.append("landlord")
        if self.is_admin:
            roles.append("admin")
        return roles

    def can_use_role(self, role: str) -> bool:
        return role in self.available_roles()

    def set_active_role(self, role: str) -> None:
        if not self.can_use_role(role):
            raise ValueError(f"User cannot use role: {role}")
        self.role = role

    def mark_login_success(self, ip: str | None) -> None:
        self.failed_login_count = 0
        self.locked_until = None
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip


@login_manager.user_loader
def load_user(user_id: str):
    if not user_id.isdigit():
        return None
    return db.session.get(User, int(user_id))
