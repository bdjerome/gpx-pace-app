import uuid
from typing import Optional

import gpxpy
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import TemplateGpxFile
from app.db.schemas import TemplateGpxFileRead
from app.db.session import get_db
from app.services import storage

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _require_admin_key(x_admin_key: Optional[str] = Header(default=None)) -> None:
    """Dependency that enforces the X-Admin-Key header.

    Raises 503 if ADMIN_API_KEY is not configured on the server.
    Raises 401 if the header is missing or incorrect.
    """
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin key not configured on this server.",
        )
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header.",
        )


@router.get("", response_model=list[TemplateGpxFileRead])
async def list_templates(
    db: AsyncSession = Depends(get_db),
) -> list[TemplateGpxFileRead]:
    """Return all platform-provided template GPX files. No authentication required."""
    result = await db.execute(
        select(TemplateGpxFile).order_by(TemplateGpxFile.file_name)
    )
    return result.scalars().all()


@router.post("", response_model=TemplateGpxFileRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    file: UploadFile = File(...),
    description: Optional[str] = Form(default=None),
    distance_m: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_require_admin_key),
) -> TemplateGpxFileRead:
    """Upload a new template GPX file (admin only — requires X-Admin-Key header).

    Validates the file is parseable GPX, stores it, and creates a
    template_gpx_files record. Not exposed on the frontend.
    """
    # Coerce empty string → None, then parse
    distance_m_float: Optional[float] = None
    if distance_m and distance_m.strip():
        try:
            distance_m_float = float(distance_m)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid distance_m value '{distance_m}'. Expected a number.",
            )
    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {_MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    try:
        gpxpy.parse(file_bytes.decode("utf-8", errors="replace"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid GPX file. The file could not be parsed.",
        )

    safe_filename = (file.filename or "template.gpx").split("/")[-1].split("\\")[-1]
    if not safe_filename.lower().endswith(".gpx"):
        safe_filename += ".gpx"

    file_id = uuid.uuid4()
    gcs_path = storage.upload_template_gpx_file(
        file_id=file_id,
        filename=safe_filename,
        file_bytes=file_bytes,
    )

    record = TemplateGpxFile(
        id=file_id,
        file_name=safe_filename,
        gcs_path=gcs_path,
        description=description if description and description.strip() else None,
        distance_m=distance_m_float,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
