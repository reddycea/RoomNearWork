from __future__ import annotations

import math
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import Index

from backend.rnw.extensions import db
from .base import TimestampMixin


class Property(TimestampMixin, db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rent_amount = db.Column(db.Integer, nullable=False)
    deposit_amount = db.Column(db.Integer, default=0, nullable=False)
    bedrooms = db.Column(db.Integer, default=1, nullable=False)
    bathrooms = db.Column(db.Integer, default=1, nullable=False)
    city = db.Column(db.String(120), index=True, nullable=False)
    province = db.Column(db.String(120), index=True, nullable=False)
    suburb = db.Column(db.String(120), index=True)
    address_line = db.Column(db.String(255))  # exact address, never exposed publicly by default
    formatted_address = db.Column(db.String(500))
    google_place_id = db.Column(db.String(255), index=True)
    approximate_address = db.Column(db.String(255))
    address_visibility = db.Column(db.String(40), default="approved_viewing", nullable=False)
    latitude = db.Column(db.Float, index=True)
    longitude = db.Column(db.Float, index=True)
    workplace_distance_km = db.Column(db.Float)
    nearest_transport = db.Column(db.String(160))
    commute_notes = db.Column(db.Text)
    furnished = db.Column(db.Boolean, default=False, nullable=False)
    pets_allowed = db.Column(db.Boolean, default=False, nullable=False)
    transport_access = db.Column(db.Boolean, default=False, nullable=False)
    image_url = db.Column(db.String(500))
    status = db.Column(db.String(40), default="under_review", index=True, nullable=False)
    status_reason = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, index=True, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    quality_score = db.Column(db.Integer, default=0, nullable=False)
    quality_score_details = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    renewed_at = db.Column(db.DateTime)
    listing_verified = db.Column(db.Boolean, default=False, nullable=False)
    verified_at = db.Column(db.DateTime)
    verified_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    landlord = db.relationship("User", foreign_keys=[landlord_id], back_populates="properties")
    verified_by = db.relationship("User", foreign_keys=[verified_by_id])
    applications = db.relationship("RentalApplication", back_populates="property", lazy="dynamic")
    assets = db.relationship("PropertyAsset", back_populates="property", cascade="all, delete-orphan", order_by="PropertyAsset.is_primary.desc(), PropertyAsset.created_at")

    __table_args__ = (
        Index("ix_properties_search", "status", "is_active", "city", "province", "rent_amount"),
        Index("ix_properties_geo", "latitude", "longitude"),
    )

    def public_location(self) -> str:
        parts = [self.suburb, self.city, self.province]
        return ", ".join([p for p in parts if p])

    def public_address(self) -> str:
        return self.approximate_address or self.public_location()

    def photo_assets(self) -> list["PropertyAsset"]:
        return [asset for asset in self.assets if asset.kind == "photo"]

    def primary_photo(self) -> "PropertyAsset | None":
        photos = self.photo_assets()
        return photos[0] if photos else None

    def private_document_assets(self) -> list["PropertyAsset"]:
        return [asset for asset in self.assets if asset.kind in {"proof_registration", "id_document"}]

    def has_required_documents(self) -> bool:
        kinds = {asset.kind for asset in self.assets}
        return "proof_registration" in kinds and "id_document" in kinds

    def documents_approved(self) -> bool:
        docs = self.private_document_assets()
        return bool(docs) and all(asset.review_status == "approved" for asset in docs)

    def renew(self, days: int | None = None) -> None:
        days = days or current_app.config.get("LISTING_EXPIRES_DAYS", 30)
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.renewed_at = datetime.utcnow()
        if self.status == "expired":
            self.status = "available"
            self.is_active = True

    @staticmethod
    def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @classmethod
    def increment_views_atomic(cls, property_id: int) -> None:
        db.session.execute(
            db.update(cls).where(cls.id == property_id).values(view_count=cls.view_count + 1)
        )
        db.session.commit()


class PropertyAsset(TimestampMixin, db.Model):
    __tablename__ = "property_assets"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False, index=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    kind = db.Column(db.String(40), nullable=False, index=True)  # photo, proof_registration, id_document
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    relative_path = db.Column(db.String(500), nullable=False, unique=True)
    mime_type = db.Column(db.String(120))
    size_bytes = db.Column(db.Integer, default=0, nullable=False)
    is_private = db.Column(db.Boolean, default=True, nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    review_status = db.Column(db.String(40), default="pending", nullable=False, index=True)
    review_note = db.Column(db.Text)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)
    virus_scan_status = db.Column(db.String(40), default="not_scanned", nullable=False)

    property = db.relationship("Property", back_populates="assets")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        Index("ix_property_assets_kind_property", "property_id", "kind"),
        Index("ix_property_assets_review", "kind", "review_status"),
    )
