from __future__ import annotations

import mimetypes
import secrets
from pathlib import Path

from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
PRIVATE_DOCUMENT_KINDS = {"proof_registration", "id_document"}


def allowed_file(filename: str, allowed: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def random_upload_name(filename: str) -> str:
    suffix = Path(secure_filename(filename)).suffix.lower()
    return f"{secrets.token_urlsafe(24)}{suffix}"


def _verify_image(path: Path) -> None:
    with Image.open(path) as img:
        img.verify()


def save_upload(file: FileStorage, target_dir: Path, allowed: set[str]) -> Path:
    if not file or not file.filename:
        raise ValueError("No file uploaded")
    if not allowed_file(file.filename, allowed):
        raise ValueError("File type not allowed")
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / random_upload_name(file.filename)
    file.save(path)
    if path.suffix.lower().lstrip(".") in ALLOWED_IMAGE_EXTENSIONS:
        _verify_image(path)
    return path


def guess_mime(path: Path, fallback: str | None = None) -> str | None:
    return mimetypes.guess_type(path.name)[0] or fallback
