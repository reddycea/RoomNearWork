from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from flask import current_app
from PIL import Image
from werkzeug.utils import secure_filename


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def allowed_file(filename: str) -> bool:
    return _extension(filename) in current_app.config["ALLOWED_IMAGE_EXTENSIONS"]


def allowed_document(filename: str) -> bool:
    return _extension(filename) in current_app.config.get("ALLOWED_DOCUMENT_EXTENSIONS", {"pdf", "png", "jpg", "jpeg"})


def safe_upload_name(filename: str) -> str:
    clean_name = secure_filename(filename)
    extension = _extension(clean_name) or "bin"
    return f"{uuid4().hex}.{extension}"


def save_image(file_storage, subfolder: str = "properties") -> str:
    if not file_storage or not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type")

    upload_root: Path = current_app.config["UPLOAD_FOLDER_PATH"]
    target_dir = upload_root / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_upload_name(file_storage.filename)
    path = target_dir / filename
    file_storage.save(path)
    compress_image(path)
    return f"/uploads/{subfolder}/{filename}"


def save_private_document(file_storage, subfolder: str = "verification") -> str:
    """Store sensitive documents outside public static routes.

    The returned private:// URL is resolved only through protected admin routes.
    """
    if not file_storage or not allowed_document(file_storage.filename):
        raise ValueError("Unsupported verification document type. Use PDF, PNG, JPG, or JPEG.")

    upload_root: Path = current_app.config["UPLOAD_FOLDER_PATH"]
    target_dir = upload_root / "private" / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = safe_upload_name(file_storage.filename)
    path = target_dir / filename
    file_storage.save(path)
    if _extension(filename) in {"png", "jpg", "jpeg", "webp"}:
        compress_image(path)
    return f"private://{subfolder}/{filename}"


def private_relative_path(private_url: str | None) -> str | None:
    if not private_url or not private_url.startswith("private://"):
        return None
    relative = private_url.replace("private://", "", 1).lstrip("/")
    # Block path traversal even if an old DB record is maliciously modified.
    if ".." in Path(relative).parts:
        return None
    return relative


def compress_image(path: Path, max_size: tuple[int, int] = (1200, 1200), quality: int = 85) -> None:
    try:
        with Image.open(path) as image:
            image.thumbnail(max_size)
            image.save(path, optimize=True, quality=quality)
    except Exception:
        # Do not fail business workflow if image optimization fails after upload.
        current_app.logger.exception("Image compression failed for %s", path)
