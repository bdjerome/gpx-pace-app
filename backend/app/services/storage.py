"""
GPX file storage service.

Two modes controlled by the USE_LOCAL_STORAGE env var:

  USE_LOCAL_STORAGE=true  (local dev)
    Files are written to backend/tmp/ on disk.
    gcs_path stored in the DB uses the prefix  local://...
    No GCP credentials required.

  USE_LOCAL_STORAGE=false  (default / production)
    Files are written to / read from Google Cloud Storage.
    gcs_path stored in the DB uses the prefix  gs://bucket/...
    Requires GCS_BUCKET_NAME env var and ADC / service-account credentials.
"""

import uuid
from pathlib import Path

from app.core.config import settings

# Root directory for local-dev file storage, resolved relative to this file:
# backend/app/services/storage.py  →  backend/tmp/
_LOCAL_ROOT = Path(__file__).resolve().parents[3] / "tmp"

_LOCAL_PREFIX = "local://"
_GCS_PREFIX = "gs://"


def _local_path(relative: str) -> Path:
    """Resolve a relative object path to an absolute local filesystem path."""
    return _LOCAL_ROOT / relative


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

def upload_gpx_file(
    user_id: uuid.UUID,
    file_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
) -> str:
    """Upload a GPX file and return the storage path to persist in the DB.

    Returns a string in one of two formats:
      - local://users/{user_id}/gpx/{file_id}/{filename}   (local dev)
      - gs://bucket/users/{user_id}/gpx/{file_id}/{filename}  (GCS)
    """
    object_path = f"users/{user_id}/gpx/{file_id}/{filename}"

    if settings.use_local_storage:
        dest = _local_path(object_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file_bytes)
        return f"{_LOCAL_PREFIX}{object_path}"

    # --- GCS ---
    from google.cloud import storage as gcs

    if not settings.gcs_bucket_name:
        raise RuntimeError(
            "GCS_BUCKET_NAME must be set when USE_LOCAL_STORAGE is false."
        )

    client = gcs.Client()
    bucket = client.bucket(settings.gcs_bucket_name)
    blob = bucket.blob(object_path)
    blob.upload_from_string(file_bytes, content_type="application/gpx+xml")
    return f"{_GCS_PREFIX}{settings.gcs_bucket_name}/{object_path}"


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_gpx_file(gcs_path: str) -> bytes:
    """Download a GPX file by its stored path and return the raw bytes."""

    if gcs_path.startswith(_LOCAL_PREFIX):
        relative = gcs_path[len(_LOCAL_PREFIX):]
        src = _local_path(relative)
        if not src.exists():
            raise FileNotFoundError(f"Local GPX file not found: {src}")
        return src.read_bytes()

    # --- GCS ---
    from google.cloud import storage as gcs

    # Strip the  gs://bucket/  prefix to get the object path
    without_prefix = gcs_path[len(_GCS_PREFIX):]          # "bucket/users/..."
    bucket_name, _, object_path = without_prefix.partition("/")

    client = gcs.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    return blob.download_as_bytes()


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def delete_gpx_file(gcs_path: str) -> None:
    """Delete a stored GPX file. Used when a race plan is hard-deleted."""

    if gcs_path.startswith(_LOCAL_PREFIX):
        relative = gcs_path[len(_LOCAL_PREFIX):]
        src = _local_path(relative)
        if src.exists():
            src.unlink()
        return

    # --- GCS ---
    from google.cloud import storage as gcs

    without_prefix = gcs_path[len(_GCS_PREFIX):]
    bucket_name, _, object_path = without_prefix.partition("/")

    client = gcs.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_path)
    if blob.exists():
        blob.delete()
