"""Generate synthetic Dehradun-area road/bridge assets for demo & training."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Rough bounding box around Dehradun urban area
LAT_MIN, LAT_MAX = 30.28, 30.38
LON_MIN, LON_MAX = 77.95, 78.10

ROAD_NAMES = [
    "Rajpur Road",
    "Chakrata Road",
    "Haridwar Bypass",
    "Saharanpur Road",
    "Premnagar Stretch",
    "Ballupur Road",
    "ISBT Corridor",
    "Clock Tower Link",
    "Raipur Road",
    "Mussoorie Road Approach",
]

BRIDGE_NAMES = [
    "Rispana Bridge",
    "Bindal Bridge",
    "Song River Culvert",
    "Tons Flyover",
    "Saharanpur ROB",
    "ISBT Overpass",
]


def _poor_probability(row: dict) -> float:
    score = 0.08
    score += max(0, row["age_years"] - 20) * 0.012
    score += max(0, 5 - row["last_inspection_score"]) * 0.07
    score += max(0, row["years_since_inspection"] - 2) * 0.04
    score += max(0, row["years_since_maintenance"] - 3) * 0.025
    score += (row["traffic_aadt"] / 60000) * 0.12
    score += (row["rainfall_mm"] / 3000) * 0.06
    score += row["damage_history_count"] * 0.045
    if row["asset_type"] == "bridge":
        score += 0.03
    return float(np.clip(score, 0.05, 0.85))


def generate(n_assets: int = 120, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_assets):
        is_bridge = rng.random() < 0.28
        asset_type = "bridge" if is_bridge else "road"
        if is_bridge:
            name = f"{rng.choice(BRIDGE_NAMES)} #{i + 1}"
            material = rng.choice(["concrete", "steel", "concrete-steel"])
            length_m = float(rng.uniform(25, 280))
            lanes = int(rng.choice([2, 4]))
        else:
            name = f"{rng.choice(ROAD_NAMES)} Segment {i + 1}"
            material = rng.choice(["asphalt", "concrete", "asphalt"])
            length_m = float(rng.uniform(200, 3500))
            lanes = int(rng.choice([2, 3, 4]))

        age = float(rng.uniform(2, 40))
        inspection = float(rng.uniform(3.0, 9.2))
        years_insp = float(rng.uniform(0.2, 5.0))
        years_maint = float(rng.uniform(0.5, 10.0))
        traffic = float(rng.uniform(2500, 45000))
        rainfall = float(rng.uniform(900, 2200))
        temp = float(rng.uniform(14, 28))
        damage_hist = int(rng.poisson(0.9))

        row = {
            "asset_code": f"{'BR' if is_bridge else 'RD'}-{1000 + i}",
            "name": name,
            "asset_type": asset_type,
            "material": material,
            "age_years": round(age, 1),
            "length_m": round(length_m, 1),
            "lanes": lanes,
            "lat": float(rng.uniform(LAT_MIN, LAT_MAX)),
            "lon": float(rng.uniform(LON_MIN, LON_MAX)),
            "traffic_aadt": round(traffic, 0),
            "last_inspection_score": round(inspection, 2),
            "years_since_inspection": round(years_insp, 2),
            "years_since_maintenance": round(years_maint, 2),
            "rainfall_mm": round(rainfall, 1),
            "temp_avg_c": round(temp, 1),
            "damage_history_count": damage_hist,
        }
        p = _poor_probability(row)
        row["condition_label"] = int(rng.random() < p)
        rows.append(row)

    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=120)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--out",
        type=str,
        default=str(Path(__file__).resolve().parents[1] / "data" / "sample_assets.csv"),
    )
    args = parser.parse_args()
    df = generate(args.n, args.seed)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} assets -> {out}")
    print(df["condition_label"].value_counts().to_dict())


if __name__ == "__main__":
    main()
