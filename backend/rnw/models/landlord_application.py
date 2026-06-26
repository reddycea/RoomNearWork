from __future__ import annotations

from datetime import datetime

from backend.rnw.extensions import db
from .base import TimestampMixin


class LandlordApplication(TimestampMixin, db.Model):
    __tablename__ = "landlord_applications"

    id = db.Column(db.Integer, primary_key=True)

    applicant_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    property_id = db.Column(
        db.Integer,
        db.ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    # pending, approved, rejected

    message = db.Column(db.Text)
    admin_note = db.Column(db.Text)

    reviewed_by_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    reviewed_at = db.Column(db.DateTime)

    applicant = db.relationship(
        "User",
        foreign_keys=[applicant_id],
    )

    reviewed_by = db.relationship(
        "User",
        foreign_keys=[reviewed_by_id],
    )

    rental_property = db.relationship("Property")

    __table_args__ = (
        db.Index(
            "ix_landlord_applications_applicant_status",
            "applicant_id",
            "status",
        ),
        db.Index(
            "ix_landlord_applications_status_created",
            "status",
            "created_at",
        ),
    )

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    def approve(self, admin_id: int | None = None) -> None:
        now = datetime.utcnow()

        self.status = "approved"
        self.reviewed_by_id = admin_id
        self.reviewed_at = now

        self.applicant.can_act_as_landlord = True
        self.applicant.landlord_approved_at = now
        self.applicant.landlord_approved_by_id = admin_id

    def reject(self, note: str | None = None, admin_id: int | None = None) -> None:
        self.status = "rejected"
        self.admin_note = note
        self.reviewed_by_id = admin_id
        self.reviewed_at = datetime.utcnow()
