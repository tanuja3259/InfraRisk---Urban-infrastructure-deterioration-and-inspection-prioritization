"""Seed database from sample CSV and run initial predictions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.db.models import Asset, Detection, InspectionReview, Prediction
from app.services.cv_service import cv_service
from app.services.ml_service import ml_service


def seed_from_csv(db: Session, csv_path: Path | None = None, force: bool = False) -> dict:
    path = csv_path or (ROOT / "data" / "sample_assets.csv")
    if not path.exists():
        sys.path.insert(0, str(ROOT / "ml"))
        from generate_sample_data import generate

        df = generate(120)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
    else:
        df = pd.read_csv(path)

    existing = db.query(Asset).count()
    if existing and not force:
        return {"status": "skipped", "assets": existing}

    if force:
        db.query(InspectionReview).delete()
        db.query(Detection).delete()
        db.query(Prediction).delete()
        db.query(Asset).delete()
        db.commit()

    ml_service.reload()

    assets = []
    for _, row in df.iterrows():
        asset = Asset(
            asset_code=str(row["asset_code"]),
            name=str(row["name"]),
            asset_type=str(row["asset_type"]),
            material=str(row.get("material", "")),
            age_years=float(row["age_years"]),
            length_m=float(row.get("length_m") or 0),
            lanes=int(row.get("lanes") or 2),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            traffic_aadt=float(row.get("traffic_aadt") or 0),
            last_inspection_score=float(row.get("last_inspection_score") or 5),
            years_since_inspection=float(row.get("years_since_inspection") or 0),
            years_since_maintenance=float(row.get("years_since_maintenance") or 0),
            rainfall_mm=float(row.get("rainfall_mm") or 0),
            temp_avg_c=float(row.get("temp_avg_c") or 20),
            damage_history_count=int(row.get("damage_history_count") or 0),
            condition_label=int(row.get("condition_label") or 0),
        )
        db.add(asset)
        assets.append(asset)
    db.commit()

    for asset in assets:
        db.refresh(asset)
        # Synthetic CV damage proxy from history + inspection score
        cv_proxy = min(
            0.85,
            (asset.damage_history_count * 0.12)
            + max(0, 5 - (asset.last_inspection_score or 5)) * 0.08,
        )
        result = ml_service.score_asset(asset, cv_damage_score=cv_proxy)
        shap = ml_service.shap_for_asset(asset)
        pred = Prediction(
            asset_id=asset.id,
            model_name=result["model_name"],
            deterioration_prob=result["deterioration_prob"],
            risk_score=result["risk_score"],
            priority=result["priority"],
            shap_json=json.dumps(shap),
            cv_damage_score=result["cv_damage_score"],
        )
        db.add(pred)
        if result["priority"] in ("Critical", "High"):
            db.add(
                InspectionReview(
                    asset_id=asset.id,
                    status="pending",
                    notice_draft=(
                        f"INSPECTION NOTICE DRAFT\n"
                        f"Asset: {asset.asset_code} — {asset.name}\n"
                        f"Type: {asset.asset_type}\n"
                        f"Risk Score: {result['risk_score']} ({result['priority']})\n"
                        f"Deterioration Probability: {result['deterioration_prob']:.2%}\n"
                        f"Recommended Action: {result['recommended_action']}\n"
                        f"Status: Pending human verification before any official notice."
                    ),
                )
            )
    db.commit()
    return {"status": "seeded", "assets": len(assets)}
