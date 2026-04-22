import datetime
import io
import json
import os
import tempfile
from typing import Optional

import gpxpy
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.gpx.misc_functions import (
    calculate_time_difference,
    merge_custom_markers,
    plotly_elevation_plot,
    plotly_pace_plot,
)
from app.core.gpx.pace_planner import GPXAnalyzer, MapVisualizer, PaceCalculator
from app.db.schemas import AnalyzeConfig, AnalyzeResponse, SplitRow, SummaryStats

router = APIRouter()

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_pace(pace_str: str) -> float:
    """Convert a 'M:SS' or 'MM:SS' pace string to decimal minutes per km."""
    try:
        parts = pace_str.strip().split(":")
        if len(parts) != 2:
            raise ValueError
        minutes = int(parts[0])
        seconds = int(parts[1])
        if seconds < 0 or seconds >= 60:
            raise ValueError
        return minutes + seconds / 60.0
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid base_pace '{pace_str}'. Expected format 'M:SS' e.g. '5:30'.",
        )


def _parse_time(time_str: str) -> datetime.time:
    """Convert 'HH:MM' or 'HH:MM:SS' to a datetime.time object."""
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.datetime.strptime(time_str.strip(), fmt).time()
        except ValueError:
            continue
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=f"Invalid race_start_time '{time_str}'. Expected 'HH:MM' or 'HH:MM:SS'.",
    )


def _markers_to_df(config: AnalyzeConfig) -> Optional[pd.DataFrame]:
    """Convert the custom_markers list from AnalyzeConfig into the DataFrame
    shape that merge_custom_markers() expects."""
    if not config.custom_markers:
        return None

    rows = []
    for m in config.custom_markers:
        row = {"Distance": m.distance, "Nickname": m.nickname}
        if m.cutoff_time is not None:
            row["Cutoff Time"] = m.cutoff_time
        rows.append(row)

    return pd.DataFrame(rows)


def _build_split_table(df: pd.DataFrame) -> list[SplitRow]:
    """Extract km-marker rows from final_df and serialise to SplitRow list."""
    km_rows = df[df["is_km_marker"] == 1].copy()
    rows: list[SplitRow] = []

    for _, row in km_rows.iterrows():
        # cutoff_time_formatted is a datetime.time object or pd.NA
        cutoff_raw = row.get("cutoff_time_formatted", None)
        cutoff_str: Optional[str] = None
        if cutoff_raw is not None and not (isinstance(cutoff_raw, float) and pd.isna(cutoff_raw)):
            try:
                cutoff_str = cutoff_raw.strftime("%H:%M:%S")
            except AttributeError:
                pass

        cutoff_buffer = row.get("cutoff_buffer_min", None)
        if cutoff_buffer is not None:
            try:
                if pd.isna(cutoff_buffer):
                    cutoff_buffer = None
            except (TypeError, ValueError):
                pass

        custom_marker_val = row.get("custom_marker", None)
        if custom_marker_val is not None and str(custom_marker_val).strip() == "":
            custom_marker_val = None

        rows.append(
            SplitRow(
                km=int(row["km_number"]),
                total_distance_km=round(float(row["total_distance"]), 3),
                elevation_m=round(float(row["elevation"]), 1),
                pace_min_per_km=round(float(row["pace"]), 3),
                cumulative_time_hms=str(row["cumulative_time_hms"]),
                clock_time=str(row["clock_time"]) if "clock_time" in row and pd.notna(row.get("clock_time")) else None,
                custom_marker=str(custom_marker_val) if custom_marker_val is not None else None,
                cutoff_time=cutoff_str,
                cutoff_buffer_min=float(cutoff_buffer) if cutoff_buffer is not None else None,
            )
        )

    return rows


def _compute_summary(df: pd.DataFrame) -> SummaryStats:
    """Compute summary statistics from the full final_df."""
    km_rows = df[df["is_km_marker"] == 1]

    total_distance_km = round(float(df["total_distance"].max()), 3)
    avg_pace = round(float(km_rows["pace"].mean()), 3) if len(km_rows) > 0 else 0.0

    # Last km-marker row holds the total cumulative time
    total_duration = str(km_rows.iloc[-1]["cumulative_time_hms"]) if len(km_rows) > 0 else "00:00:00"

    segment_gain = df["elevation"].diff()
    elevation_gain = round(float(segment_gain[segment_gain > 0].sum()), 1)
    elevation_loss = round(float(abs(segment_gain[segment_gain < 0].sum())), 1)

    return SummaryStats(
        total_distance_km=total_distance_km,
        avg_pace_min_per_km=avg_pace,
        total_duration_hms=total_duration,
        elevation_gain_m=elevation_gain,
        elevation_loss_m=elevation_loss,
    )


# ---------------------------------------------------------------------------
# Shared pipeline
# ---------------------------------------------------------------------------

def _run_analysis_pipeline(file_bytes: bytes, config: AnalyzeConfig) -> AnalyzeResponse:
    """Run the full GPX analysis pipeline and return an AnalyzeResponse.

    Accepts already-validated GPX bytes and a parsed AnalyzeConfig.
    Called by both POST /routes/analyze and GET /routes/{id}.
    """
    base_pace_float = _parse_pace(config.base_pace)
    start_time = _parse_time(config.race_start_time)
    use_km = config.pace_unit == "min/km"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".gpx", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        # 1. GPXAnalyzer
        analyzer = GPXAnalyzer(tmp_path)
        analyzer.load_gpx()
        analyzer.map_adjustment(loops=config.loops)
        analyzer.calculate_distances()
        analyzer.find_kilometer_markers()

        # 2. PaceCalculator
        pace_calc = PaceCalculator(analyzer, base_pace_float)
        pace_calc.calculate_pace(
            decay=config.decay,
            hill_mode=config.hill_mode,
        )
        pace_calc.calculate_times()
        pace_calc.calculate_clock_times(start_time)

        # 3. Custom markers
        marker_df = _markers_to_df(config)
        analyzer.final_df = merge_custom_markers(
            analyzer.final_df,
            marker_df,
            use_km_markers=use_km,
        )

        # 4. Cutoff buffer column
        if "cutoff_time_formatted" in analyzer.final_df.columns:
            analyzer.final_df["cutoff_buffer_min"] = analyzer.final_df.apply(
                calculate_time_difference, axis=1
            )

        # 5. Map — render to HTML string without writing to disk
        map_viz = MapVisualizer(analyzer.final_df)
        map_viz.create_base_map()
        map_viz.add_kilometer_markers_directional()
        map_html: str = map_viz.map.get_root().render()

        # 6. Charts
        total_gain = float(
            analyzer.final_df["elevation"].diff().clip(lower=0).sum()
        )
        elev_fig = plotly_elevation_plot(analyzer, total_gain, use_metric=use_km)
        pace_fig = plotly_pace_plot(analyzer.final_df, use_metric=use_km)

        elevation_chart_json = elev_fig.to_json() if elev_fig is not None else None
        pace_chart_json = pace_fig.to_json() if pace_fig is not None else None

        # 7. Serialise results
        split_table = _build_split_table(analyzer.final_df)
        summary = _compute_summary(analyzer.final_df)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return AnalyzeResponse(
        split_table=split_table,
        summary=summary,
        map_html=map_html,
        elevation_chart_json=elevation_chart_json,
        pace_chart_json=pace_chart_json,
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_gpx(
    file: UploadFile = File(...),
    config: str = Form(...),  # JSON string — no auth required
) -> AnalyzeResponse:
    """Analyze a GPX file and return split table, summary stats, map, and charts.

    No authentication required — available to guest users.

    Accepts multipart/form-data with:
      - file:   the .gpx file
      - config: JSON string matching AnalyzeConfig schema

    For testing use {"loops": 1, "base_pace": "5:30", "race_start_time": "08:00", "decay": false, "hill_mode": false, "pace_unit": "min/km", "custom_markers": []}
    """
    # --- Parse config ---
    try:
        config_data = AnalyzeConfig(**json.loads(config))
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid config JSON: {exc}",
        )

    # --- Read and validate the file ---
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

    return _run_analysis_pipeline(file_bytes, config_data)
