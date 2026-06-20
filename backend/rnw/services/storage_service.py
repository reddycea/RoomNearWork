from __future__ import annotations

from pathlib import Path

from flask import current_app
from werkzeug.datastructures import FileStorage

from backend.rnw.utils.uploads import ALLOWED_DOCUMENT_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS, save_upload


def save_property_image(file: FileStorage) -> str:
    path = save_upload(file, current_app.config["UPLOAD_FOLDER_PATH"] / "property_images", ALLOWED_IMAGE_EXTENSIONS)
    return str(path.relative_to(current_app.config["UPLOAD_FOLDER_PATH"].parent))


def save_private_document(file: FileStorage) -> str:
    path = save_upload(file, current_app.config["UPLOAD_FOLDER_PATH"] / "private_documents", ALLOWED_DOCUMENT_EXTENSIONS)
    return str(path)
