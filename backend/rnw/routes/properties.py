from __future__ import annotations

from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Property, PropertyPhoto, SearchHistory
from ..services.geolocation_service import filter_properties_by_distance, geocode_address
from ..services.subscription_service import landlord_can_create_listing
from ..utils.decorators import email_verified_required, roles_required, subscription_required
from ..utils.security import save_image
from ..utils.validators import PROVINCES, parse_bool, parse_optional_float, parse_optional_int

properties_bp = Blueprint("properties", __name__, url_prefix="/properties")


@properties_bp.get("/")
def list_properties():
    query = Property.query.filter_by(status="approved", is_available=True)

    city = request.args.get("city", "").strip()
    province = request.args.get("province", "").strip()
    property_type = request.args.get("property_type", "").strip()
    transport_access = request.args.get("transport_access", "").strip()
    min_price = parse_optional_float(request.args.get("min_price"))
    max_price = parse_optional_float(request.args.get("max_price"))
    max_deposit = parse_optional_float(request.args.get("max_deposit"))
    bedrooms = parse_optional_int(request.args.get("bedrooms"))
    workplace = request.args.get("workplace", "").strip()
    radius_km = parse_optional_float(request.args.get("radius_km")) or 10
    furnished = request.args.get("furnished")
    pets_allowed = request.args.get("pets_allowed")
    sort = request.args.get("sort", "newest")

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if province:
        query = query.filter(Property.province == province)
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if transport_access:
        query = query.filter(Property.transport_access.ilike(f"%{transport_access}%"))
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if max_deposit is not None:
        query = query.filter((Property.deposit_amount == None) | (Property.deposit_amount <= max_deposit))  # noqa: E711
    if bedrooms is not None:
        query = query.filter(Property.bedrooms >= bedrooms)
    if furnished == "1":
        query = query.filter(Property.furnished.is_(True))
    if pets_allowed == "1":
        query = query.filter(Property.pets_allowed.is_(True))

    coord = geocode_address(workplace)
    distances = {}
    if coord:
        base_properties = query.limit(500).all()
        matches = filter_properties_by_distance(base_properties, coord.latitude, coord.longitude, radius_km)
        properties = [prop for prop, distance in matches]
        distances = {prop.id: distance for prop, distance in matches}
        if sort == "cheapest":
            properties = sorted(properties, key=lambda p: p.price)
        elif sort == "highest":
            properties = sorted(properties, key=lambda p: p.price, reverse=True)
        elif sort == "newest":
            properties = sorted(properties, key=lambda p: p.created_at, reverse=True)
    else:
        if sort == "cheapest":
            query = query.order_by(Property.price.asc())
        elif sort == "highest":
            query = query.order_by(Property.price.desc())
        elif sort == "popular":
            query = query.order_by(Property.view_count.desc(), Property.created_at.desc())
        else:
            query = query.order_by(Property.created_at.desc())
        properties = query.limit(200).all()

    search = SearchHistory(
        user_id=current_user.id if current_user.is_authenticated else None,
        search_address=workplace or city or province,
        latitude=coord.latitude if coord else None,
        longitude=coord.longitude if coord else None,
        radius_km=radius_km,
        min_price=min_price,
        max_price=max_price,
        bedrooms=bedrooms,
        property_type=property_type,
        result_count=len(properties),
        session_id=request.cookies.get("session"),
    )
    db.session.add(search)
    db.session.commit()

    return render_template("properties/list.html", properties=properties, distances=distances, provinces=PROVINCES)


@properties_bp.get("/<int:property_id>")
def detail(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if prop.status != "approved" and (not current_user.is_authenticated or current_user.id != prop.landlord_id and current_user.role != "admin"):
        abort(404)
    prop.increment_views()
    db.session.commit()
    return render_template("properties/detail.html", property=prop)


@properties_bp.route("/new", methods=["GET", "POST"])
@roles_required("landlord", "admin")
@email_verified_required
@subscription_required
def create():
    allowed, limit, count = landlord_can_create_listing(current_user)
    if not allowed:
        flash(f"Your Landlord Pro plan allows {limit} active listings. You currently have {count}.", "warning")
        return redirect(url_for("landlord.dashboard"))
    if request.method == "POST":
        prop = _property_from_form(Property(landlord_id=current_user.id))
        db.session.add(prop)
        db.session.flush()
        _attach_uploaded_photos(prop)
        db.session.commit()
        flash("Property submitted for admin approval.", "success")
        return redirect(url_for("landlord.dashboard"))
    return render_template("properties/form.html", property=None, provinces=PROVINCES)


@properties_bp.route("/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
def edit(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if current_user.id != prop.landlord_id and current_user.role != "admin":
        abort(403)
    if request.method == "POST":
        _property_from_form(prop)
        _attach_uploaded_photos(prop)
        db.session.commit()
        flash("Property updated.", "success")
        return redirect(url_for("properties.detail", property_id=prop.id))
    return render_template("properties/form.html", property=prop, provinces=PROVINCES)


@properties_bp.post("/<int:property_id>/delete")
@login_required
def delete(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if current_user.id != prop.landlord_id and current_user.role != "admin":
        abort(403)
    db.session.delete(prop)
    db.session.commit()
    flash("Property deleted.", "info")
    return redirect(url_for("landlord.dashboard"))


def _property_from_form(prop: Property) -> Property:
    form = request.form
    prop.title = form.get("title", "").strip()
    prop.description = form.get("description", "").strip()
    prop.property_type = form.get("property_type", "room")
    prop.address = form.get("address", "").strip()
    prop.city = form.get("city", "").strip()
    prop.province = form.get("province", "")
    prop.postal_code = form.get("postal_code", "")
    prop.price = float(form.get("price") or 0)
    prop.deposit_amount = parse_optional_float(form.get("deposit_amount"))
    prop.bedrooms = int(form.get("bedrooms") or 0)
    prop.bathrooms = float(form.get("bathrooms") or 0)
    prop.parking = int(form.get("parking") or 0)
    prop.area_sqm = parse_optional_float(form.get("area_sqm"))
    prop.pets_allowed = parse_bool(form.get("pets_allowed"))
    prop.furnished = parse_bool(form.get("furnished"))
    prop.transport_access = form.get("transport_access", "").strip()
    prop.minimum_lease = int(form.get("minimum_lease") or 12)
    prop.latitude = parse_optional_float(form.get("latitude"))
    prop.longitude = parse_optional_float(form.get("longitude"))

    if not prop.latitude or not prop.longitude:
        coord = geocode_address(f"{prop.address}, {prop.city}, {prop.province}")
        if coord:
            prop.latitude = coord.latitude
            prop.longitude = coord.longitude

    available_date = form.get("available_date")
    if available_date:
        prop.available_date = datetime.strptime(available_date, "%Y-%m-%d").date()
    return prop


def _attach_uploaded_photos(prop: Property) -> None:
    for index, file in enumerate(request.files.getlist("photos")):
        if file and file.filename:
            url = save_image(file, "properties")
            db.session.add(PropertyPhoto(property=prop, photo_url=url, is_primary=(not prop.photos and index == 0)))
