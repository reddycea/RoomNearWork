from __future__ import annotations

from datetime import datetime

from ..extensions import db
from .base import TimestampMixin


class Property(TimestampMixin, db.Model):
    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)
    landlord_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.String(50), nullable=False, index=True)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    province = db.Column(db.String(50), nullable=False, index=True)
    postal_code = db.Column(db.String(10), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    price = db.Column(db.Float, nullable=False, index=True)
    deposit_amount = db.Column(db.Float, nullable=True, index=True)
    bedrooms = db.Column(db.Integer, default=0)
    bathrooms = db.Column(db.Float, default=0)
    parking = db.Column(db.Integer, default=0)
    area_sqm = db.Column(db.Float, nullable=True)
    pets_allowed = db.Column(db.Boolean, default=False, nullable=False)
    furnished = db.Column(db.Boolean, default=False, nullable=False, index=True)
    transport_access = db.Column(db.String(255), nullable=True)
    available_date = db.Column(db.Date, nullable=True)
    minimum_lease = db.Column(db.Integer, default=12)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(20), default="pending", index=True)  # pending, approved, rejected
    view_count = db.Column(db.Integer, default=0, nullable=False)
    featured_until = db.Column(db.DateTime, nullable=True)

    landlord = db.relationship("User", back_populates="properties")
    photos = db.relationship("PropertyPhoto", back_populates="property", cascade="all, delete-orphan")
    saved_by = db.relationship("SavedProperty", back_populates="property", cascade="all, delete-orphan")
    inquiries = db.relationship("Inquiry", back_populates="property", cascade="all, delete-orphan")
    applications = db.relationship("RentalApplication", back_populates="property", cascade="all, delete-orphan")

    @property
    def primary_photo(self) -> str | None:
        primary = next((photo for photo in self.photos if photo.is_primary), None)
        return (primary or self.photos[0]).photo_url if self.photos else None

    @property
    def average_rating(self) -> float:
        ratings = [app.rating for app in self.applications if app.rating]
        return round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    @property
    def is_featured(self) -> bool:
        return bool(self.featured_until and self.featured_until > datetime.utcnow())

    def increment_views(self) -> None:
        self.view_count = (self.view_count or 0) + 1

    def to_dict(self, include_landlord: bool = False) -> dict:
        payload = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "property_type": self.property_type,
            "address": self.address,
            "city": self.city,
            "province": self.province,
            "postal_code": self.postal_code,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "price": self.price,
            "deposit_amount": self.deposit_amount,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "parking": self.parking,
            "area_sqm": self.area_sqm,
            "pets_allowed": self.pets_allowed,
            "furnished": self.furnished,
            "transport_access": self.transport_access,
            "available_date": self.available_date.isoformat() if self.available_date else None,
            "minimum_lease": self.minimum_lease,
            "is_available": self.is_available,
            "status": self.status,
            "view_count": self.view_count,
            "primary_photo": self.primary_photo,
            "average_rating": self.average_rating,
        }
        if include_landlord and self.landlord:
            payload["landlord"] = self.landlord.to_dict()
        return payload


class PropertyPhoto(db.Model):
    __tablename__ = "property_photos"

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False, nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    property = db.relationship("Property", back_populates="photos")


class SavedProperty(db.Model):
    __tablename__ = "saved_properties"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="saved_properties")
    property = db.relationship("Property", back_populates="saved_by")

    __table_args__ = (db.UniqueConstraint("user_id", "property_id", name="uq_saved_property"),)


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    search_address = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    radius_km = db.Column(db.Float, default=5)
    min_price = db.Column(db.Float, nullable=True)
    max_price = db.Column(db.Float, nullable=True)
    bedrooms = db.Column(db.Integer, nullable=True)
    property_type = db.Column(db.String(50), nullable=True)
    result_count = db.Column(db.Integer, default=0)
    session_id = db.Column(db.String(100), nullable=True)
    searched_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="searches")
