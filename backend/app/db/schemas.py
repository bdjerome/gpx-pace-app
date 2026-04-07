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
