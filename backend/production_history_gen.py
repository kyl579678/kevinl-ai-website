#!/usr/bin/env python3
"""Generate synthetic FDC/SPC production history data.

Produces CSV records of manufacturing parameters across process stages,
tools, and chambers — matched to wafer IDs from defect map data.
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

SEED = 42
OUTPUT_DIR = Path(__file__).parent / "static" / "datasets" / "production_history"
DEFECT_MAP_PATH = Path(__file__).parent / "static" / "datasets" / "defect_maps" / "defect_maps.csv"

np.random.seed(SEED)
random.seed(SEED)

# Process stages with tools, chambers, and parameters
STAGES = {
    "Litho": {
        "tools": ["LITHO-A1", "LITHO-A2", "LITHO-A3"],
        "chambers": 2,
        "parameters": {
            "exposure_dose": {"nominal": 35.0, "sigma": 1.5, "lower": 30.0, "upper": 40.0, "unit": "mJ/cm2"},
            "focus_offset": {"nominal": 0.0, "sigma": 0.05, "lower": -0.2, "upper": 0.2, "unit": "um"},
            "develop_time": {"nominal": 60.0, "sigma": 2.0, "lower": 50.0, "upper": 70.0, "unit": "s"},
            "bake_temperature": {"nominal": 110.0, "sigma": 1.0, "lower": 105.0, "upper": 115.0, "unit": "C"},
        },
    },
    "Etch": {
        "tools": ["ETCH-B1", "ETCH-B2", "ETCH-B3", "ETCH-B4"],
        "chambers": 3,
        "parameters": {
            "rf_power": {"nominal": 500.0, "sigma": 15.0, "lower": 450.0, "upper": 550.0, "unit": "W"},
            "pressure": {"nominal": 20.0, "sigma": 1.0, "lower": 15.0, "upper": 25.0, "unit": "mTorr"},
            "gas_flow_cf4": {"nominal": 50.0, "sigma": 3.0, "lower": 40.0, "upper": 60.0, "unit": "sccm"},
            "gas_flow_o2": {"nominal": 10.0, "sigma": 0.5, "lower": 7.0, "upper": 13.0, "unit": "sccm"},
            "etch_time": {"nominal": 120.0, "sigma": 5.0, "lower": 100.0, "upper": 140.0, "unit": "s"},
        },
    },
    "CVD": {
        "tools": ["CVD-C1", "CVD-C2", "CVD-C3"],
        "chambers": 2,
        "parameters": {
            "temperature": {"nominal": 400.0, "sigma": 5.0, "lower": 380.0, "upper": 420.0, "unit": "C"},
            "pressure": {"nominal": 4.5, "sigma": 0.3, "lower": 3.5, "upper": 5.5, "unit": "Torr"},
            "sih4_flow": {"nominal": 100.0, "sigma": 5.0, "lower": 85.0, "upper": 115.0, "unit": "sccm"},
            "deposition_time": {"nominal": 300.0, "sigma": 10.0, "lower": 270.0, "upper": 330.0, "unit": "s"},
        },
    },
    "CMP": {
        "tools": ["CMP-D1", "CMP-D2", "CMP-D3", "CMP-D4", "CMP-D5"],
        "chambers": 3,
        "parameters": {
            "down_force": {"nominal": 3.0, "sigma": 0.2, "lower": 2.0, "upper": 4.0, "unit": "psi"},
            "platen_speed": {"nominal": 80.0, "sigma": 3.0, "lower": 60.0, "upper": 100.0, "unit": "rpm"},
            "slurry_flow": {"nominal": 200.0, "sigma": 10.0, "lower": 150.0, "upper": 250.0, "unit": "ml/min"},
            "polish_time": {"nominal": 90.0, "sigma": 5.0, "lower": 70.0, "upper": 110.0, "unit": "s"},
        },
    },
    "Implant": {
        "tools": ["IMP-E1", "IMP-E2", "IMP-E3"],
        "chambers": 2,
        "parameters": {
            "beam_energy": {"nominal": 50.0, "sigma": 2.0, "lower": 40.0, "upper": 60.0, "unit": "keV"},
            "dose": {"nominal": 1e15, "sigma": 5e13, "lower": 8e14, "upper": 1.2e15, "unit": "ions/cm2"},
            "tilt_angle": {"nominal": 7.0, "sigma": 0.3, "lower": 5.0, "upper": 9.0, "unit": "deg"},
            "beam_current": {"nominal": 10.0, "sigma": 0.5, "lower": 8.0, "upper": 12.0, "unit": "mA"},
        },
    },
}

# Stage processing order (each wafer goes through all stages)
STAGE_ORDER = ["Litho", "Etch", "CVD", "CMP", "Implant"]


def _load_wafer_ids() -> list[tuple[str, str, str]]:
    """Load unique (wafer_id, lot_id, timestamp) from defect maps."""
    seen = {}
    with open(DEFECT_MAP_PATH) as f:
        reader = csv.DictReader(f)
        for row in reader:
            wid = row["wafer_id"]
            if wid not in seen:
                seen[wid] = (wid, row["lot_id"], row["timestamp"])
    return list(seen.values())


def generate_production_history() -> None:
    """Generate production history CSV matched to existing wafer IDs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    wafers = _load_wafer_ids()
    if not wafers:
        raise RuntimeError(f"No wafer IDs found in {DEFECT_MAP_PATH}. Run defect_map_gen.py first.")

    fieldnames = [
        "wafer_id", "lot_id", "stage_id", "tool_id", "chamber_id",
        "timestamp", "parameter_name", "parameter_value",
        "upper_limit", "lower_limit",
    ]

    all_rows = []
    # Assign each wafer a fixed tool route (same tool per stage for consistency)
    for wafer_id, lot_id, wafer_ts in wafers:
        base_ts = datetime.fromisoformat(wafer_ts)

        for stage_idx, stage_name in enumerate(STAGE_ORDER):
            stage = STAGES[stage_name]
            tool_id = random.choice(stage["tools"])
            chamber_id = f"CH{random.randint(1, stage['chambers'])}"
            # Each stage happens a few hours after the previous
            stage_ts = base_ts + timedelta(hours=stage_idx * 4, minutes=random.randint(0, 60))

            for param_name, spec in stage["parameters"].items():
                # Occasionally inject an out-of-spec value (~5% chance)
                if random.random() < 0.05:
                    # Shift mean toward one of the limits
                    direction = random.choice([-1, 1])
                    shift = direction * spec["sigma"] * np.random.uniform(2.5, 4.0)
                    value = spec["nominal"] + shift
                else:
                    value = np.random.normal(spec["nominal"], spec["sigma"])

                all_rows.append({
                    "wafer_id": wafer_id,
                    "lot_id": lot_id,
                    "stage_id": stage_name,
                    "tool_id": tool_id,
                    "chamber_id": chamber_id,
                    "timestamp": stage_ts.isoformat(),
                    "parameter_name": param_name,
                    "parameter_value": round(value, 6),
                    "upper_limit": spec["upper"],
                    "lower_limit": spec["lower"],
                })

    out_path = OUTPUT_DIR / "production_history.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[production_history_gen] Wrote {len(all_rows)} records for {len(wafers)} wafers to {out_path}")


if __name__ == "__main__":
    generate_production_history()
