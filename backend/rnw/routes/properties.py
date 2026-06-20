from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from backend.rnw.extensions import db, limiter
from backend.rnw.models import Property, PropertyAsset, RentalApplication
from backend.rnw.services.audit_service import log_action
from backend.rnw.services.geolocation_service import bounding_box, filter_properties_by_distance
from backend.rnw.services.google_maps_service import attach_commute_measures, geocode_address, geocode_place_id, geocode_property_address
from backend.rnw.services.listing_quality_service import update_listing_quality
from backend.rnw.services.seo_service import real_estate_json_ld
from backend.rnw.services.subscription_service import landlord_can_create_listing, lock_user
from backend.rnw.utils.decorators import landlord_required, tenant_required
from backend.rnw.utils.security import clean_user_text
from backend.rnw.utils.uploads import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS, guess_mime, save_upload

properties_bp = Blueprint("properties", __name__, url_prefix="/properties")


def _save_property_asset(prop: Property, file, kind: str, private: bool) -> PropertyAsset | None:
    if not file or not file.filename:
        return None
    allowed = ALLOWED_IMAGE_EXTENSIONS if kind == "photo" else ALLOWED_DOCUMENT_EXTENSIONS
    subdir = "private" if private else "photos"
    base_dir = current_app.config["UPLOAD_FOLDER_PATH"] / "properties" / str(prop.id) / subdir
    saved_path = save_upload(file, base_dir, allowed)
    relative_path = saved_path.relative_to(current_app.config["UPLOAD_FOLDER_PATH"])
    existing_primary = any(asset.kind == "photo" and asset.is_primary for asset in prop.assets)
    return PropertyAsset(
        property_id=prop.id,
        uploaded_by_id=current_user.id,
        kind=kind,
        original_filename=clean_user_text(file.filename, 255),
        stored_filename=saved_path.name,
        relative_path=str(relative_path),
        mime_type=guess_mime(saved_path, file.mimetype),
        size_bytes=saved_path.stat().st_size,
        is_private=private,
        is_primary=(kind == "photo" and not existing_primary),
        review_status="approved" if kind == "photo" else "pending",
    )


def _query_by_area(query, area: str | None, city: str | None, province: str | None):
    area_terms = [term for term in {area, city, province} if term]
    if not area_terms:
        return query
    filters = []
    for term in area_terms:
        like = f"%{term}%"
        filters.extend([Property.suburb.ilike(like), Property.city.ilike(like), Property.province.ilike(like)])
    return query.filter(or_(*filters))


def _populate_property_from_form(prop: Property) -> None:
    exact_address = clean_user_text(request.form.get("address_line"), 255)
    city = clean_user_text(request.form.get("city"), 120)
    province = clean_user_text(request.form.get("province"), 120)
    suburb = clean_user_text(request.form.get("suburb"), 120)
    place_id = request.form.get("google_place_id", "").strip()
    geocoded = geocode_place_id(place_id, exact_address) if place_id else (geocode_property_address(exact_address, suburb, city, province) if exact_address else None)

    prop.title = clean_user_text(request.form.get("title"), 200)
    prop.description = clean_user_text(request.form.get("description"), 5000)
    prop.rent_amount = request.form.get("rent_amount", type=int) or 0
    prop.deposit_amount = request.form.get("deposit_amount", type=int) or 0
    prop.bedrooms = request.form.get("bedrooms", type=int) or 1
    prop.bathrooms = request.form.get("bathrooms", type=int) or 1
    prop.city = city or (geocoded.city if geocoded else "")
    prop.province = province or (geocoded.province if geocoded else "")
    prop.suburb = suburb or (geocoded.suburb if geocoded else None)
    prop.address_line = exact_address
    prop.formatted_address = geocoded.formatted_address if geocoded else None
    prop.google_place_id = geocoded.place_id if geocoded else place_id or None
    prop.latitude = geocoded.latitude if geocoded else None
    prop.longitude = geocoded.longitude if geocoded else None
    prop.approximate_address = clean_user_text(request.form.get("approximate_address"), 255) or (geocoded.area_label if geocoded else None)
    prop.furnished = bool(request.form.get("furnished"))
    prop.pets_allowed = bool(request.form.get("pets_allowed"))
    prop.transport_access = bool(request.form.get("transport_access"))
    prop.nearest_transport = clean_user_text(request.form.get("nearest_transport"), 160)
    prop.commute_notes = clean_user_text(request.form.get("commute_notes"), 1000)


def _handle_asset_uploads(prop: Property) -> None:
    for photo in request.files.getlist("photos")[:8]:
        asset = _save_property_asset(prop, photo, "photo", private=False)
        if asset:
            db.session.add(asset)
    proof = _save_property_asset(prop, request.files.get("proof_registration"), "proof_registration", private=True)
    id_doc = _save_property_asset(prop, request.files.get("id_document"), "id_document", private=True)
    if proof:
        db.session.add(proof)
    if id_doc:
        db.session.add(id_doc)


@properties_bp.get("")
def index():
    query = Property.query.filter(Property.is_active.is_(True), Property.status == "available")
    city = request.args.get("city", "").strip()
    workplace_address = request.args.get("workplace_address", "").strip()
    workplace_place_id = request.args.get("workplace_place_id", "").strip()
    travel_mode = request.args.get("travel_mode", "all")
    max_rent = request.args.get("max_rent", type=int)
    furnished = request.args.get("furnished")
    transport = request.args.get("transport")
    max_distance = request.args.get("max_distance", type=float) or current_app.config.get("DEFAULT_SEARCH_RADIUS_KM", 20)
    max_travel_minutes = request.args.get("max_travel_minutes", type=int) or current_app.config.get("DEFAULT_MAX_TRAVEL_MINUTES", 45)
    search_context = None

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if max_rent:
        query = query.filter(Property.rent_amount <= max_rent)
    if furnished:
        query = query.filter(Property.furnished.is_(True))
    if transport:
        query = query.filter(Property.transport_access.is_(True))

    if workplace_address or workplace_place_id:
        origin = geocode_place_id(workplace_place_id, workplace_address) if workplace_place_id else geocode_address(workplace_address)
        search_context = origin
        if origin.latitude is not None and origin.longitude is not None:
            min_lat, max_lat, min_lon, max_lon = bounding_box(origin.latitude, origin.longitude, float(max_distance))
            candidate_query = query.filter(Property.latitude.between(min_lat, max_lat), Property.longitude.between(min_lon, max_lon))
            candidates = candidate_query.limit(2000).all()
            if not candidates:
                candidates = _query_by_area(query, origin.area_label, origin.city, origin.province).limit(2000).all()
            properties = filter_properties_by_distance(candidates, origin.latitude, origin.longitude, float(max_distance)) or candidates
            attach_commute_measures(origin, properties, selected_mode=travel_mode)
            if max_travel_minutes:
                properties = [prop for prop in properties if not getattr(prop, "commute_modes", None) or any(m.duration_min is not None and m.duration_min <= max_travel_minutes for m in prop.commute_modes)]
            properties.sort(key=lambda prop: min([m.duration_min for m in getattr(prop, "commute_modes", []) if m.duration_min is not None] or [999999]))
        else:
            properties = _query_by_area(query, origin.area_label, origin.city, origin.province).order_by(Property.created_at.desc()).limit(100).all()
    else:
        properties = query.order_by(Property.created_at.desc()).limit(100).all()

    return render_template("properties/index.html", properties=properties, search_context=search_context, google_maps_browser_key=current_app.config.get("GOOGLE_MAPS_BROWSER_KEY", ""))


@properties_bp.get("/<int:property_id>")
def detail(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if not property_.is_active and not (current_user.is_authenticated and (current_user.id == property_.landlord_id or current_user.is_admin)):
        abort(404)
    Property.increment_views_atomic(property_id)
    json_ld = real_estate_json_ld(property_)
    return render_template("properties/detail.html", property=property_, json_ld=json_ld)


@properties_bp.route("/new", methods=["GET", "POST"])
@login_required
@landlord_required
@limiter.limit("10 per hour")
def create():
    if request.method == "POST":
        lock_user(current_user.id)
        if not landlord_can_create_listing(current_user.id):
            db.session.rollback()
            flash("Your active listing limit has been reached.", "danger")
            return render_template("properties/form.html", property=None)
        prop = Property(landlord_id=current_user.id, status="under_review", is_active=True)
        _populate_property_from_form(prop)
        prop.renew()
        db.session.add(prop)
        db.session.flush()
        try:
            _handle_asset_uploads(prop)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return render_template("properties/form.html", property=prop)
        db.session.flush()
        update_listing_quality(prop)
        log_action("listing_created", "Property", prop.id)
        db.session.commit()
        flash("Listing submitted for review. Admin will check your photos, property registration proof and ID document.", "success")
        return redirect(url_for("landlord.dashboard"))
    return render_template("properties/form.html", property=None)


@properties_bp.route("/<int:property_id>/edit", methods=["GET", "POST"])
@login_required
@landlord_required
def edit(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if prop.landlord_id != current_user.id and not current_user.is_admin:
        abort(403)
    if request.method == "POST":
        _populate_property_from_form(prop)
        if prop.status in {"available", "rejected"}:
            prop.status = "under_review"
            prop.status_reason = None
            prop.is_active = True
        try:
            _handle_asset_uploads(prop)
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return render_template("properties/form.html", property=prop)
        db.session.flush()
        update_listing_quality(prop)
        log_action("listing_updated", "Property", prop.id)
        db.session.commit()
        flash("Listing updated and sent for review if needed.", "success")
        return redirect(url_for("landlord.dashboard"))
    return render_template("properties/form.html", property=prop)


@properties_bp.post("/<int:property_id>/archive")
@login_required
@landlord_required
def archive(property_id: int):
    prop = db.session.get(Property, property_id) or abort(404)
    if prop.landlord_id != current_user.id:
        abort(403)
    prop.status = "archived"
    prop.is_active = False
    log_action("listing_archived", "Property", prop.id)
    db.session.commit()
    flash("Listing archived.", "success")
    return redirect(url_for("landlord.dashboard"))


@properties_bp.post("/assets/<int:asset_id>/delete")
@login_required
@landlord_required
def delete_asset(asset_id: int):
    asset = db.session.get(PropertyAsset, asset_id) or abort(404)
    prop = asset.property
    if prop.landlord_id != current_user.id and not current_user.is_admin:
        abort(403)
    path = current_app.config["UPLOAD_FOLDER_PATH"] / asset.relative_path
    db.session.delete(asset)
    db.session.flush()
    update_listing_quality(prop)
    db.session.commit()
    try:
        path.unlink(missing_ok=True)
    except Exception:
        current_app.logger.warning("Could not remove upload %s", path)
    flash("File removed.", "success")
    return redirect(url_for("properties.edit", property_id=prop.id))


@properties_bp.post("/assets/<int:asset_id>/primary")
@login_required
@landlord_required
def primary_asset(asset_id: int):
    asset = db.session.get(PropertyAsset, asset_id) or abort(404)
    if asset.kind != "photo":
        abort(400)
    prop = asset.property
    if prop.landlord_id != current_user.id and not current_user.is_admin:
        abort(403)
    for photo in prop.photo_assets():
        photo.is_primary = False
    asset.is_primary = True
    db.session.commit()
    flash("Main photo updated.", "success")
    return redirect(url_for("properties.edit", property_id=prop.id))


@properties_bp.get("/media/<int:asset_id>")
def media(asset_id: int):
    asset = db.session.get(PropertyAsset, asset_id) or abort(404)
    prop = asset.property
    if asset.is_private:
        if not current_user.is_authenticated:
            abort(403)
        if not (current_user.is_admin or current_user.id == prop.landlord_id):
            abort(403)
    root = current_app.config["UPLOAD_FOLDER_PATH"]
    path = root / asset.relative_path
    if not path.exists():
        abort(404)
    return send_from_directory(path.parent, path.name, mimetype=asset.mime_type)


@properties_bp.post("/<int:property_id>/apply")
@login_required
@tenant_required
@limiter.limit("10 per hour")
def apply(property_id: int):
    property_ = db.session.get(Property, property_id) or abort(404)
    if property_.landlord_id == current_user.id:
        abort(403)
    application = RentalApplication(property_id=property_id, applicant_id=current_user.id, message=clean_user_text(request.form.get("message"), 2000))
    db.session.add(application)
    try:
        db.session.commit()
        flash("Application sent.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("You already applied for this listing.", "info")
    return redirect(url_for("properties.detail", property_id=property_id))
