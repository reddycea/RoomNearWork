from __future__ import annotations

from pathlib import Path

from flask import current_app


class StorageService:
    """Small storage abstraction used by RNW.

    Local storage works for development and small VPS deployments. For production
    on Render/DigitalOcean, configure CLOUDINARY or S3-compatible storage and
    replace the upload code in this class with the provider SDK upload calls.
    Keeping this service boundary makes the rest of the app production-ready.
    """

    def provider(self) -> str:
        return current_app.config.get("STORAGE_PROVIDER", "local").lower()

    def save_public_file(self, local_path: Path, subfolder: str, filename: str) -> str:
        provider = self.provider()
        if provider == "local":
            return f"/uploads/{subfolder}/{filename}"
        if provider == "cloudinary":
            base = current_app.config.get("CLOUDINARY_DELIVERY_BASE", "").rstrip("/")
            return f"{base}/rnw/{subfolder}/{filename}" if base else f"cloudinary://rnw/{subfolder}/{filename}"
        if provider in {"s3", "spaces"}:
            base = current_app.config.get("PUBLIC_STORAGE_BASE_URL", "").rstrip("/")
            return f"{base}/{subfolder}/{filename}" if base else f"s3://rnw/{subfolder}/{filename}"
        raise RuntimeError(f"Unsupported STORAGE_PROVIDER: {provider}")

    def save_private_file(self, local_path: Path, subfolder: str, filename: str) -> str:
        provider = self.provider()
        if provider == "local":
            return f"private://{subfolder}/{filename}"
        if provider == "cloudinary":
            return f"private-cloudinary://rnw/private/{subfolder}/{filename}"
        if provider in {"s3", "spaces"}:
            return f"private-s3://rnw/private/{subfolder}/{filename}"
        raise RuntimeError(f"Unsupported STORAGE_PROVIDER: {provider}")
