from __future__ import annotations

import re
from datetime import datetime

PROVINCES = [
    "Eastern Cape",
    "Free State",
    "Gauteng",
    "KwaZulu-Natal",
    "Limpopo",
    "Mpumalanga",
    "Northern Cape",
    "North West",
    "Western Cape",
]


def validate_sa_id(id_number: str | None) -> bool:
    """Validate a 13-digit South African ID number with date and Luhn checks."""
    if not id_number or not re.fullmatch(r"\d{13}", id_number):
        return False

    yy = int(id_number[0:2])
    mm = int(id_number[2:4])
    dd = int(id_number[4:6])
    current_yy = datetime.utcnow().year % 100
    century = 1900 if yy > current_yy else 2000

    try:
        datetime(century + yy, mm, dd)
    except ValueError:
        return False

    digits = [int(char) for char in id_number]
    checksum = digits[-1]
    total = 0
    reverse_body = list(reversed(digits[:-1]))
    for index, digit in enumerate(reverse_body):
        if index % 2 == 0:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return (10 - (total % 10)) % 10 == checksum


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).lower() in {"1", "true", "yes", "on"}


def parse_optional_float(value):
    if value in (None, ""):
        return None
    return float(value)


def parse_optional_int(value):
    if value in (None, ""):
        return None
    return int(value)
