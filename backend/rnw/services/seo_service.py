from __future__ import annotations

import json

from flask import current_app, url_for

from backend.rnw.models import Property


def real_estate_json_ld(property_: Property) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "name": property_.title,
        "description": property_.description[:500],
        "url": current_app.config.get("APP_BASE_URL", "").rstrip("/") + url_for("properties.detail", property_id=property_.id),
        "address": {
            "@type": "PostalAddress",
            "addressLocality": property_.city,
            "addressRegion": property_.province,
            "streetAddress": property_.approximate_address or property_.public_location(),
        },
        "offers": {
            "@type": "Offer",
            "price": property_.rent_amount,
            "priceCurrency": "ZAR",
            "availability": "https://schema.org/InStock" if property_.status == "available" else "https://schema.org/OutOfStock",
        },
    }
    if property_.image_url:
        data["image"] = property_.image_url
    return json.dumps(data, ensure_ascii=False)
