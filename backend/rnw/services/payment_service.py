from __future__ import annotations

import hashlib
from urllib.parse import quote_plus

from flask import current_app

from backend.rnw.utils.security import safe_compare


def _payfast_pairs(data: dict) -> list[tuple[str, str]]:
    return [(k, str(v).strip()) for k, v in data.items() if k != "signature" and v is not None and str(v).strip() != ""]


def build_payfast_signature(data: dict, passphrase: str | None = None) -> str:
    pairs = _payfast_pairs(data)
    pairs.sort(key=lambda item: item[0])
    payload = "&".join(f"{k}={quote_plus(v)}" for k, v in pairs)
    if passphrase:
        payload += f"&passphrase={quote_plus(passphrase)}"
    return hashlib.md5(payload.encode("utf-8")).hexdigest()


def validate_payfast_itn(data: dict) -> tuple[bool, str]:
    expected_merchant = current_app.config.get("PAYFAST_MERCHANT_ID", "")
    if expected_merchant and data.get("merchant_id") != expected_merchant:
        return False, "Invalid merchant_id"
    expected = build_payfast_signature(data, current_app.config.get("PAYFAST_PASSPHRASE", ""))
    if not safe_compare(data.get("signature"), expected):
        return False, "Invalid signature"
    if data.get("payment_status") not in {"COMPLETE", "COMPLETE ", "Completed", "paid"}:
        return False, "Payment not complete"
    return True, "OK"
