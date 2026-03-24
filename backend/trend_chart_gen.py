#!/usr/bin/env python3
"""Generate trend analysis data from defect maps and production history.

Aggregates defect counts by defect_code, timestamp, and tool_id
into daily/hourly JSON summaries for charting.
"""

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "static" / "datasets"
DEFECT_MAP_PATH = OUTPUT_DIR / "defect_maps" / "defect_maps.csv"
PRODUCTION_HISTORY_PATH = OUTPUT_DIR / "production_history" / "production_history.csv"


def _load_defect_maps() -> list[dict]:
    with open(DEFECT_MAP_PATH) as f:
        return list(csv.DictReader(f))


def _load_production_history() -> list[dict]:
    with open(PRODUCTION_HISTORY_PATH) as f:
        return list(csv.DictReader(f))


def _build_wafer_tool_map(prod_rows: list[dict]) -> dict[str, set[str]]:
    """Map wafer_id -> set of tool_ids it was processed on."""
    mapping: dict[str, set[str]] = defaultdict(set)
    for row in prod_rows:
        mapping[row["wafer_id"]].add(row["tool_id"])
    return mapping


def generate_trends() -> None:
    """Generate trend JSON files."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    defects = _load_defect_maps()
    prod_rows = _load_production_history()
    wafer_tools = _build_wafer_tool_map(prod_rows)

    # --- Daily defect counts by defect_code ---
    daily_by_code: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in defects:
        day = datetime.fromisoformat(row["timestamp"]).strftime("%Y-%m-%d")
        code = row["defect_code"]
        daily_by_code[day][code] += 1

    # Sort by date
    daily_by_code_sorted = {
        day: dict(sorted(codes.items(), key=lambda x: int(x[0])))
        for day, codes in sorted(daily_by_code.items())
    }

    # --- Hourly defect counts (total) ---
    hourly_total: dict[str, int] = defaultdict(int)
    for row in defects:
        hour = datetime.fromisoformat(row["timestamp"]).strftime("%Y-%m-%d %H:00")
        hourly_total[hour] += 1
    hourly_total_sorted = dict(sorted(hourly_total.items()))

    # --- Daily defect counts by tool_id ---
    daily_by_tool: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in defects:
        day = datetime.fromisoformat(row["timestamp"]).strftime("%Y-%m-%d")
        wafer_id = row["wafer_id"]
        tools = wafer_tools.get(wafer_id, set())
        for tool_id in tools:
            daily_by_tool[day][tool_id] += 1

    daily_by_tool_sorted = {
        day: dict(sorted(tools.items()))
        for day, tools in sorted(daily_by_tool.items())
    }

    # --- Top defect codes summary ---
    code_totals: dict[str, int] = defaultdict(int)
    for row in defects:
        code_totals[row["defect_code"]] += 1
    top_codes = sorted(code_totals.items(), key=lambda x: -x[1])[:20]

    # --- Assemble output ---
    trend_data = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_defects": len(defects),
            "total_wafers": len({r["wafer_id"] for r in defects}),
            "date_range": {
                "start": min(daily_by_code_sorted.keys()),
                "end": max(daily_by_code_sorted.keys()),
            },
            "top_defect_codes": [{"code": c, "count": n} for c, n in top_codes],
        },
        "daily_by_defect_code": daily_by_code_sorted,
        "hourly_total": hourly_total_sorted,
        "daily_by_tool": daily_by_tool_sorted,
    }

    out_path = OUTPUT_DIR / "trend_data.json"
    with open(out_path, "w") as f:
        json.dump(trend_data, f, indent=2)

    print(f"[trend_chart_gen] Wrote trend data to {out_path}")
    print(f"  Total defects: {len(defects)}")
    print(f"  Date range: {trend_data['summary']['date_range']}")
    print(f"  Top defect code: {top_codes[0][0]} ({top_codes[0][1]} occurrences)")


if __name__ == "__main__":
    generate_trends()
