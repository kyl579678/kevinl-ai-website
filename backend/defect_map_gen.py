#!/usr/bin/env python3
"""Generate synthetic wafer defect map data.

Produces CSV files with realistic defect distributions across 300mm wafers,
including random scatter, cluster, ring, scratch, and edge patterns.
"""

import csv
import math
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

SEED = 42
WAFER_RADIUS = 150.0  # mm, 300mm wafer
NUM_WAFERS = 100
DEFECTS_MIN = 50
DEFECTS_MAX = 500
TIMESPAN_DAYS = 30
OUTPUT_DIR = Path(__file__).parent / "static" / "datasets" / "defect_maps"

PATTERNS = ["random", "cluster", "ring", "scratch", "edge"]

np.random.seed(SEED)
random.seed(SEED)


def _point_in_wafer(x: float, y: float) -> bool:
    return x**2 + y**2 <= WAFER_RADIUS**2


def _generate_random(n: int) -> list[tuple[float, float]]:
    """Uniform random scatter across the wafer."""
    points = []
    while len(points) < n:
        x = np.random.uniform(-WAFER_RADIUS, WAFER_RADIUS)
        y = np.random.uniform(-WAFER_RADIUS, WAFER_RADIUS)
        if _point_in_wafer(x, y):
            points.append((round(x, 2), round(y, 2)))
    return points


def _generate_cluster(n: int) -> list[tuple[float, float]]:
    """Localized cluster of defects around 1-3 center points."""
    num_clusters = random.randint(1, 3)
    points = []
    for _ in range(num_clusters):
        # Pick a cluster center inside the wafer
        cx = np.random.uniform(-WAFER_RADIUS * 0.7, WAFER_RADIUS * 0.7)
        cy = np.random.uniform(-WAFER_RADIUS * 0.7, WAFER_RADIUS * 0.7)
        cluster_size = n // num_clusters
        sigma = np.random.uniform(5, 25)  # mm spread
        for _ in range(cluster_size):
            attempts = 0
            while attempts < 50:
                x = np.random.normal(cx, sigma)
                y = np.random.normal(cy, sigma)
                if _point_in_wafer(x, y):
                    points.append((round(x, 2), round(y, 2)))
                    break
                attempts += 1
    # Fill remainder with random
    while len(points) < n:
        x = np.random.uniform(-WAFER_RADIUS, WAFER_RADIUS)
        y = np.random.uniform(-WAFER_RADIUS, WAFER_RADIUS)
        if _point_in_wafer(x, y):
            points.append((round(x, 2), round(y, 2)))
    return points[:n]


def _generate_ring(n: int) -> list[tuple[float, float]]:
    """Ring pattern — defects concentrated along a circular band."""
    ring_radius = np.random.uniform(40, 120)  # mm from center
    ring_width = np.random.uniform(5, 15)  # mm band width
    points = []
    while len(points) < n:
        angle = np.random.uniform(0, 2 * math.pi)
        r = np.random.normal(ring_radius, ring_width / 2)
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        if _point_in_wafer(x, y):
            points.append((round(x, 2), round(y, 2)))
    return points


def _generate_scratch(n: int) -> list[tuple[float, float]]:
    """Linear scratch pattern across the wafer."""
    angle = np.random.uniform(0, math.pi)
    scratch_width = np.random.uniform(2, 8)  # mm
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    points = []
    while len(points) < n:
        t = np.random.uniform(-WAFER_RADIUS, WAFER_RADIUS)
        offset = np.random.normal(0, scratch_width / 2)
        x = t * cos_a + offset * sin_a
        y = t * sin_a - offset * cos_a
        if _point_in_wafer(x, y):
            points.append((round(x, 2), round(y, 2)))
    return points


def _generate_edge(n: int) -> list[tuple[float, float]]:
    """Edge-concentrated defects near the wafer perimeter."""
    edge_band = np.random.uniform(5, 20)  # mm from edge
    points = []
    while len(points) < n:
        angle = np.random.uniform(0, 2 * math.pi)
        r = np.random.uniform(WAFER_RADIUS - edge_band, WAFER_RADIUS)
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        if _point_in_wafer(x, y):
            points.append((round(x, 2), round(y, 2)))
    return points


PATTERN_FUNCS = {
    "random": _generate_random,
    "cluster": _generate_cluster,
    "ring": _generate_ring,
    "scratch": _generate_scratch,
    "edge": _generate_edge,
}


def generate_defect_maps() -> list[dict]:
    """Generate defect map CSVs for all wafers. Returns wafer metadata."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base_time = datetime.now() - timedelta(days=TIMESPAN_DAYS)
    wafer_meta = []

    all_rows = []
    for i in range(NUM_WAFERS):
        wafer_id = f"W{i + 1:04d}"
        lot_id = f"LOT{(i // 25) + 1:03d}"
        pattern = PATTERNS[i % len(PATTERNS)]
        n_defects = random.randint(DEFECTS_MIN, DEFECTS_MAX)

        # Timestamp for this wafer within the 30-day span
        wafer_time = base_time + timedelta(
            seconds=random.randint(0, TIMESPAN_DAYS * 86400)
        )

        points = PATTERN_FUNCS[pattern](n_defects)
        for x, y in points:
            defect_code = random.randint(1, 99)
            ts = wafer_time + timedelta(seconds=random.randint(0, 3600))
            all_rows.append({
                "wafer_id": wafer_id,
                "x": x,
                "y": y,
                "defect_code": defect_code,
                "timestamp": ts.isoformat(),
                "lot_id": lot_id,
            })

        wafer_meta.append({
            "wafer_id": wafer_id,
            "lot_id": lot_id,
            "pattern": pattern,
            "n_defects": len(points),
            "timestamp": wafer_time.isoformat(),
        })

    # Write single consolidated CSV
    out_path = OUTPUT_DIR / "defect_maps.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["wafer_id", "x", "y", "defect_code", "timestamp", "lot_id"]
        )
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"[defect_map_gen] Wrote {len(all_rows)} defect records for {NUM_WAFERS} wafers to {out_path}")
    return wafer_meta


if __name__ == "__main__":
    generate_defect_maps()
