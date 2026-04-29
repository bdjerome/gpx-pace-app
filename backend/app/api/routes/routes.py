import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.routes.analyze import _run_analysis_pipeline
from app.db.models import GpxFile, PlanNote, RacePlan, TemplateGpxFile, User
from app.db.schemas import (
    AnalyzeConfig,
    AnalyzeResponse,
    CustomMarker,
    PlanNoteItem,
    PlanNotesUpdate,
    PlanWithAnalysis,
    RacePlanCreate,
    RacePlanRead,
    RacePlanSummary,
    RacePlanUpdate,
)
from app.db.session import get_db
from app.services import storage

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stored_config_to_analyze_config(config: dict[str, Any]) -> AnalyzeConfig:
    """Convert the stored RaceConfig JSONB dict to an AnalyzeConfig for the pipeline.

    RaceConfig keys (stored)  →  AnalyzeConfig keys (pipeline)
      pace                    →  base_pace
      start_time              →  race_start_time
      decay_enabled           →  decay
      hills_enabled           →  hill_mode
      markers                 →  custom_markers
    """
    return AnalyzeConfig(
        loops=config.get("loops", 1),
        base_pace=config["pace"],
        race_start_time=config["start_time"],
        decay=config.get("decay_enabled", False),
        hill_mode=config.get("hills_enabled", False),
        pace_unit=config.get("pace_unit", "min/km"),
        custom_markers=[CustomMarker(**m) for m in config.get("markers", [])],
    )


def _plan_to_summary(plan: RacePlan) -> RacePlanSummary:
    """Build a RacePlanSummary from an ORM plan with pre-loaded file relationships."""
    filename: Optional[str] = None
    if plan.gpx_file:
        filename = plan.gpx_file.file_name
    elif plan.template_gpx_file:
        filename = plan.template_gpx_file.file_name

    return RacePlanSummary(
        id=plan.id,
        nickname=plan.nickname,
        gpx_file_id=plan.gpx_file_id,
        template_gpx_file_id=plan.template_gpx_file_id,
        gpx_filename=filename,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


async def _get_plan_or_404(plan_id: uuid.UUID, db: AsyncSession) -> RacePlan:
    """Fetch a RacePlan by id with file relationships eagerly loaded. Raises 404 if missing."""
    result = await db.execute(
        select(RacePlan)
        .where(RacePlan.id == plan_id)
        .options(
            selectinload(RacePlan.gpx_file),
            selectinload(RacePlan.template_gpx_file),
            selectinload(RacePlan.notes),
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Race plan not found.",
        )
    return plan


def _verify_ownership(plan: RacePlan, current_user: User) -> None:
    """Raise HTTP 403 if the plan does not belong to the authenticated user."""
    if plan.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this race plan.",
        )


# ---------------------------------------------------------------------------
# POST /routes — Save a new race plan
# ---------------------------------------------------------------------------

@router.post("", response_model=RacePlanSummary, status_code=status.HTTP_201_CREATED)
async def create_race_plan(
    body: RacePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RacePlanSummary:
    """Save a new race plan for the authenticated user.

    Exactly one of gpx_file_id or template_gpx_file_id must be provided.
    User-owned GPX files are validated for ownership before the plan is created.
    """
    # Enforce the CheckConstraint at the application layer with a clear error message
    if body.gpx_file_id is None and body.template_gpx_file_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Exactly one of gpx_file_id or template_gpx_file_id must be provided.",
        )
    if body.gpx_file_id is not None and body.template_gpx_file_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide only one of gpx_file_id or template_gpx_file_id, not both.",
        )

    # Validate the referenced file exists (and is owned by this user if user-uploaded)
    if body.gpx_file_id is not None:
        result = await db.execute(select(GpxFile).where(GpxFile.id == body.gpx_file_id))
        gpx_file = result.scalar_one_or_none()
        if gpx_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPX file not found.",
            )
        if gpx_file.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GPX file does not belong to you.",
            )
    else:
        result = await db.execute(
            select(TemplateGpxFile).where(TemplateGpxFile.id == body.template_gpx_file_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template GPX file not found.",
            )

    plan_id = uuid.uuid4()
    plan = RacePlan(
        id=plan_id,
        user_id=current_user.id,
        gpx_file_id=body.gpx_file_id,
        template_gpx_file_id=body.template_gpx_file_id,
        nickname=body.nickname,
        config=body.config.model_dump(),
    )
    db.add(plan)
    await db.commit()

    # Re-fetch with relationships so _plan_to_summary can resolve the filename
    plan = await _get_plan_or_404(plan_id, db)
    return _plan_to_summary(plan)


# ---------------------------------------------------------------------------
# GET /routes — List all race plans for the authenticated user
# ---------------------------------------------------------------------------

@router.get("", response_model=list[RacePlanSummary])
async def list_race_plans(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RacePlanSummary]:
    """Return all saved race plans for the authenticated user, newest first."""
    result = await db.execute(
        select(RacePlan)
        .where(RacePlan.user_id == current_user.id)
        .options(
            selectinload(RacePlan.gpx_file),
            selectinload(RacePlan.template_gpx_file),
        )
        .order_by(RacePlan.created_at.desc())
    )
    plans = result.scalars().all()
    return [_plan_to_summary(p) for p in plans]


# ---------------------------------------------------------------------------
# GET /routes/{id} — Re-run analysis for a saved plan
# ---------------------------------------------------------------------------

@router.get("/{plan_id}", response_model=PlanWithAnalysis)
async def get_race_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlanWithAnalysis:
    """Re-run the full analysis pipeline for a saved plan and return PlanWithAnalysis.

    Verifies ownership (403 if mismatch), downloads the stored GPX file, and
    re-executes the analysis using the saved config — no result caching.
    """
    plan = await _get_plan_or_404(plan_id, db)
    _verify_ownership(plan, current_user)

    # Resolve GPX storage path from whichever source is set
    if plan.gpx_file:
        gcs_path = plan.gpx_file.gcs_path
    elif plan.template_gpx_file:
        gcs_path = plan.template_gpx_file.gcs_path
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Race plan has no associated GPX file.",
        )

    try:
        file_bytes = storage.download_gpx_file(gcs_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The GPX file for this plan could not be found in storage.",
        )

    try:
        analyze_config = _stored_config_to_analyze_config(plan.config)
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stored plan config is malformed: {exc}",
        )

    return PlanWithAnalysis(
        plan=RacePlanRead.model_validate(plan),
        analysis=_run_analysis_pipeline(file_bytes, analyze_config),
        notes=[PlanNoteItem(km=n.km, note=n.note) for n in plan.notes],
    )


# ---------------------------------------------------------------------------
# PUT /routes/{id} — Update a saved race plan
# ---------------------------------------------------------------------------

@router.put("/{plan_id}", response_model=RacePlanSummary)
async def update_race_plan(
    plan_id: uuid.UUID,
    body: RacePlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RacePlanSummary:
    """Partially update a saved race plan (nickname, config, or GPX source).

    Fields absent from the request body are left unchanged.
    Providing a new gpx_file_id or template_gpx_file_id switches the GPX
    source and automatically clears the other field to maintain the
    exactly-one-source constraint.
    """
    plan = await _get_plan_or_404(plan_id, db)
    _verify_ownership(plan, current_user)

    if body.nickname is not None:
        plan.nickname = body.nickname

    if body.config is not None:
        plan.config = body.config.model_dump()

    # Switching to a user-uploaded GPX file — validate ownership, clear template ref
    if body.gpx_file_id is not None:
        result = await db.execute(select(GpxFile).where(GpxFile.id == body.gpx_file_id))
        gpx_file = result.scalar_one_or_none()
        if gpx_file is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GPX file not found.",
            )
        if gpx_file.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="GPX file does not belong to you.",
            )
        plan.gpx_file_id = body.gpx_file_id
        plan.template_gpx_file_id = None

    # Switching to a template GPX file — validate it exists, clear user file ref
    elif body.template_gpx_file_id is not None:
        result = await db.execute(
            select(TemplateGpxFile).where(TemplateGpxFile.id == body.template_gpx_file_id)
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template GPX file not found.",
            )
        plan.template_gpx_file_id = body.template_gpx_file_id
        plan.gpx_file_id = None

    plan.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.commit()

    # Re-fetch with relationships loaded so the summary has the correct filename
    plan = await _get_plan_or_404(plan_id, db)
    return _plan_to_summary(plan)


# ---------------------------------------------------------------------------
# DELETE /routes/{id} — Hard-delete a race plan
# ---------------------------------------------------------------------------

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_race_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Hard-delete a race plan.

    If the plan references a user-uploaded GPX file (not a template) and no
    other plans share that file, the GpxFile DB record and the file in storage
    are also deleted.
    """
    plan = await _get_plan_or_404(plan_id, db)
    _verify_ownership(plan, current_user)

    # Capture what we need before the plan row is gone
    gpx_file_id: Optional[uuid.UUID] = plan.gpx_file_id
    gcs_path: Optional[str] = plan.gpx_file.gcs_path if plan.gpx_file else None

    # Delete the plan first — this removes the FK reference to gpx_files
    await db.delete(plan)
    await db.commit()

    # Clean up the user-owned GPX file if no other plans still reference it
    if gpx_file_id is not None and gcs_path is not None:
        other = await db.execute(
            select(RacePlan.id).where(RacePlan.gpx_file_id == gpx_file_id).limit(1)
        )
        if other.scalar_one_or_none() is None:
            result = await db.execute(select(GpxFile).where(GpxFile.id == gpx_file_id))
            gpx_file = result.scalar_one_or_none()
            if gpx_file is not None:
                await db.delete(gpx_file)
                await db.commit()
            storage.delete_gpx_file(gcs_path)


# ---------------------------------------------------------------------------
# PUT /routes/{id}/notes — Bulk-replace notes for a saved plan
# ---------------------------------------------------------------------------

@router.put("/{plan_id}/notes", response_model=list[PlanNoteItem])
async def save_plan_notes(
    plan_id: uuid.UUID,
    body: PlanNotesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PlanNoteItem]:
    """Bulk-replace all split-table notes for a saved race plan.

    Deletes all existing notes for the plan and inserts the new set,
    skipping entries with blank text. Ownership is verified before any writes.
    """
    plan = await _get_plan_or_404(plan_id, db)
    _verify_ownership(plan, current_user)

    await db.execute(delete(PlanNote).where(PlanNote.plan_id == plan_id))
    for item in body.notes:
        if item.note.strip():
            db.add(PlanNote(plan_id=plan_id, km=item.km, note=item.note))
    await db.commit()
    return [item for item in body.notes if item.note.strip()]
