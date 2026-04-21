import uuid

import gpxpy
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import GpxFile, User
from app.db.schemas import GpxUploadResponse
from app.db.session import get_db
from app.services import storage

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/gpx", response_model=GpxUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_gpx(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GpxUploadResponse:
    """Upload a GPX file for the authenticated user.

    - Validates the file is valid GPX (parseable by gpxpy)
    - Enforces a 10 MB size limit
    - Uploads the file to GCS (or local storage in dev)
    - Creates a gpx_files record in the database
    - Returns file_id, original filename, and file size
    """
    # Read bytes upfront so we can size-check and validate before touching storage
    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # Validate GPX format
    try:
        gpxpy.parse(file_bytes.decode("utf-8", errors="replace"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid GPX file. The file could not be parsed.",
        )

    # Sanitise the filename — keep only the basename to prevent path traversal
    safe_filename = (file.filename or "upload.gpx").split("/")[-1].split("\\")[-1]
    if not safe_filename.lower().endswith(".gpx"):
        safe_filename += ".gpx"

    file_id = uuid.uuid4()

    # Upload to storage (GCS or local dev folder)
    gcs_path = storage.upload_gpx_file(
        user_id=current_user.id,
        file_id=file_id,
        filename=safe_filename,
        file_bytes=file_bytes,
    )

    # Persist the record
    gpx_record = GpxFile(
        id=file_id,
        user_id=current_user.id,
        file_name=safe_filename,
        gcs_path=gcs_path,
    )
    db.add(gpx_record)
    await db.commit()

    return GpxUploadResponse(
        file_id=file_id,
        gpx_filename=safe_filename,
        file_size_bytes=len(file_bytes),
    )
