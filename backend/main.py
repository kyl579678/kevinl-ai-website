#!/usr/bin/env python3
"""FastAPI backend for Defect iDoctor semiconductor defect diagnosis platform."""

import csv
import json
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Defect iDoctor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = Path(__file__).parent / "static"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATASETS_DIR = STATIC_DIR / "datasets"
DEFECT_MAP_CSV = DATASETS_DIR / "defect_maps" / "defect_maps.csv"
PRODUCTION_CSV = DATASETS_DIR / "production_history" / "production_history.csv"
TREND_JSON = DATASETS_DIR / "trend_data.json"


def _load_csv(path: Path) -> list[dict]:
    with open(path) as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Cache data in memory at startup
# ---------------------------------------------------------------------------
_defect_rows: list[dict] = []
_production_rows: list[dict] = []
_trend_data: dict = {}
_wafer_ids: list[str] = []


@app.on_event("startup")
def _load_data():
    global _defect_rows, _production_rows, _trend_data, _wafer_ids
    _defect_rows = _load_csv(DEFECT_MAP_CSV)
    _production_rows = _load_csv(PRODUCTION_CSV)
    with open(TREND_JSON) as f:
        _trend_data = json.load(f)
    _wafer_ids = sorted({r["wafer_id"] for r in _defect_rows})


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/defects/maps")
def list_defect_maps(limit: int = 100, offset: int = 0):
    """List all wafer IDs with defect counts."""
    counts: dict[str, dict] = {}
    for row in _defect_rows:
        wid = row["wafer_id"]
        if wid not in counts:
            counts[wid] = {"wafer_id": wid, "lot_id": row["lot_id"], "defect_count": 0}
        counts[wid]["defect_count"] += 1

    wafers = sorted(counts.values(), key=lambda w: w["wafer_id"])
    total = len(wafers)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "wafers": wafers[offset : offset + limit],
    }


@app.get("/api/defects/map/{wafer_id}")
def get_wafer_defect_map(wafer_id: str):
    """Get all defect points for a specific wafer."""
    points = [r for r in _defect_rows if r["wafer_id"] == wafer_id]
    if not points:
        raise HTTPException(status_code=404, detail=f"Wafer {wafer_id} not found")
    return {
        "wafer_id": wafer_id,
        "lot_id": points[0]["lot_id"],
        "defect_count": len(points),
        "defects": [
            {
                "x": float(r["x"]),
                "y": float(r["y"]),
                "defect_code": int(r["defect_code"]),
                "timestamp": r["timestamp"],
            }
            for r in points
        ],
    }


@app.get("/api/production/history")
def get_production_history(
    wafer_id: str | None = None,
    stage_id: str | None = None,
    tool_id: str | None = None,
    limit: int = 500,
    offset: int = 0,
):
    """Get production history with optional filters."""
    rows = _production_rows
    if wafer_id:
        rows = [r for r in rows if r["wafer_id"] == wafer_id]
    if stage_id:
        rows = [r for r in rows if r["stage_id"] == stage_id]
    if tool_id:
        rows = [r for r in rows if r["tool_id"] == tool_id]

    total = len(rows)
    page = rows[offset : offset + limit]
    # Cast numeric fields
    for r in page:
        r["parameter_value"] = float(r["parameter_value"])
        r["upper_limit"] = float(r["upper_limit"])
        r["lower_limit"] = float(r["lower_limit"])

    return {"total": total, "offset": offset, "limit": limit, "records": page}


@app.get("/api/trends")
def get_trends():
    """Get pre-computed trend analysis data."""
    return _trend_data


@app.get("/api/stats")
def get_stats():
    """Dashboard summary statistics."""
    wafer_count = len(_wafer_ids)
    defect_count = len(_defect_rows)
    lot_ids = {r["lot_id"] for r in _defect_rows}
    tool_ids = {r["tool_id"] for r in _production_rows}
    stage_ids = {r["stage_id"] for r in _production_rows}

    # Defect code distribution (top 10)
    code_counts: dict[int, int] = defaultdict(int)
    for r in _defect_rows:
        code_counts[int(r["defect_code"])] += 1
    top_codes = sorted(code_counts.items(), key=lambda x: -x[1])[:10]

    # Out-of-spec count
    oos_count = sum(
        1
        for r in _production_rows
        if float(r["parameter_value"]) > float(r["upper_limit"])
        or float(r["parameter_value"]) < float(r["lower_limit"])
    )

    return {
        "wafer_count": wafer_count,
        "defect_count": defect_count,
        "lot_count": len(lot_ids),
        "tool_count": len(tool_ids),
        "stage_count": len(stage_ids),
        "out_of_spec_count": oos_count,
        "top_defect_codes": [{"code": c, "count": n} for c, n in top_codes],
    }


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.get("/")
def serve_home():
    return FileResponse(PROJECT_ROOT / "index.html")


@app.get("/frontend/defect-idoctor.html")
def serve_defect_idoctor():
    return FileResponse(FRONTEND_DIR / "defect-idoctor.html")


# Serve static files (datasets, frontend assets)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
