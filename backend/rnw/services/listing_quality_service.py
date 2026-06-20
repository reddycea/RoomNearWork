from __future__ import annotations

import json

from backend.rnw.models import Property


def calculate_listing_quality(property_: Property) -> tuple[int, dict]:
    photos = property_.photo_assets() if hasattr(property_, "photo_assets") else []
    checks = {
        "has_description": bool(property_.description and len(property_.description) >= 80),
        "has_photo": bool(photos or property_.image_url),
        "has_three_photos": len(photos) >= 3,
        "has_location": bool(property_.city and property_.province and property_.suburb),
        "has_exact_address_for_admin": bool(property_.address_line and property_.latitude and property_.longitude),
        "has_price": bool(property_.rent_amount and property_.rent_amount > 0),
        "has_transport": bool(property_.transport_access or property_.nearest_transport),
        "has_commute_notes": bool(property_.commute_notes),
        "has_owner_documents": bool(getattr(property_, "has_required_documents", lambda: False)()),
        "verified": bool(property_.listing_verified),
    }
    score = round(sum(1 for ok in checks.values() if ok) / len(checks) * 100)
    return score, checks


def update_listing_quality(property_: Property) -> None:
    score, details = calculate_listing_quality(property_)
    property_.quality_score = score
    property_.quality_score_details = json.dumps(details, sort_keys=True)
