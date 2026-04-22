import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from pydantic import BaseModel, EmailStr


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Template GPX Files
# ---------------------------------------------------------------------------

class TemplateGpxFileRead(BaseModel):
    id: uuid.UUID
    file_name: str
    description: Optional[str]
    distance_m: Optional[Decimal]
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# User GPX Files
# ---------------------------------------------------------------------------

class GpxFileRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Race Plans
# ---------------------------------------------------------------------------

class RaceConfig(BaseModel):
    """Validated shape of the config JSONB column."""

    pace: str                           # e.g. "5:30"
    pace_unit: str                      # "min/km" | "min/mile"
    loops: int
    start_time: str                     # ISO time string e.g. "08:00"
    decay_enabled: bool = False
    hills_enabled: bool = False
    markers: list[dict[str, Any]] = []


class RacePlanCreate(BaseModel):
    nickname: str
    gpx_file_id: Optional[uuid.UUID] = None
    template_gpx_file_id: Optional[uuid.UUID] = None
    config: RaceConfig


class RacePlanUpdate(BaseModel):
    nickname: Optional[str] = None
    gpx_file_id: Optional[uuid.UUID] = None
    template_gpx_file_id: Optional[uuid.UUID] = None
    config: Optional[RaceConfig] = None


class RacePlanSummary(BaseModel):
    """Lightweight list item returned by GET /routes."""

    id: uuid.UUID
    nickname: str
    gpx_file_id: Optional[uuid.UUID]
    template_gpx_file_id: Optional[uuid.UUID]
    gpx_filename: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RacePlanRead(BaseModel):
    """Full detail returned by GET /routes/{id}."""

    id: uuid.UUID
    user_id: uuid.UUID
    nickname: str
    gpx_file_id: Optional[uuid.UUID]
    template_gpx_file_id: Optional[uuid.UUID]
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# GPX Analysis  (POST /routes/analyze)
# ---------------------------------------------------------------------------

class CustomMarker(BaseModel):
    """A single user-defined marker (aid station, checkpoint, etc.)."""

    distance: float                     # km or miles depending on pace_unit
    nickname: str
    cutoff_time: Optional[str] = None   # "HH:MM" or "HH:MM:SS", omit if no cutoff


class AnalyzeConfig(BaseModel):
    """Request config sent alongside the GPX file for analysis."""

    loops: int = 1
    base_pace: str                      # "M:SS" or "MM:SS", e.g. "5:30" for 5 min 30 sec/km
    race_start_time: str                # "HH:MM" or "HH:MM:SS", e.g. "08:00"
    decay: bool = False
    hill_mode: bool = False
    pace_unit: str = "min/km"           # "min/km" | "min/mile"
    custom_markers: list[CustomMarker] = []


class SplitRow(BaseModel):
    """One km-marker row in the analysis split table."""

    km: int
    total_distance_km: float
    elevation_m: float
    pace_min_per_km: float
    cumulative_time_hms: str
    clock_time: Optional[str] = None
    custom_marker: Optional[str] = None
    cutoff_time: Optional[str] = None       # formatted "HH:MM:SS" if present
    cutoff_buffer_min: Optional[float] = None


class SummaryStats(BaseModel):
    total_distance_km: float
    avg_pace_min_per_km: float
    total_duration_hms: str
    elevation_gain_m: float
    elevation_loss_m: float


class AnalyzeResponse(BaseModel):
    split_table: list[SplitRow]
    summary: SummaryStats
    map_html: str
    elevation_chart_json: Optional[str] = None  # None when GPX has no elevation data
    pace_chart_json: Optional[str] = None


# ---------------------------------------------------------------------------
# GPX File Upload  (POST /routes/gpx)
# ---------------------------------------------------------------------------

class GpxUploadResponse(BaseModel):
    file_id: uuid.UUID
    gpx_filename: str
    file_size_bytes: int
