"""REST API routes for the Urban Infrastructure Risk platform."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Asset, Detection, InspectionReview, Prediction
from app.schemas.schemas import (
    AssetOut,
    DashboardStats,
    DetectionOut,
    InspectionReviewCreate,
    InspectionReviewOut,
    PredictionOut,
    RiskMapFeature,
    ShapExplanation,
)
from app.services.cv_service import cv_service
from app.services.ml_service import ml_service
from app.services.seed import seed_from_csv

router = APIRouter()
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _latest_prediction(db: Session, asset_id: int) -> Prediction | None:
    return (
        db.query(Prediction)
        .filter(Prediction.asset_id == asset_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )


def _asset_out(db: Session, asset: Asset) -> AssetOut:
    pred = _latest_prediction(db, asset.id)
    data = AssetOut.model_validate(asset)
    if pred:
        data.latest_risk_score = pred.risk_score
        data.latest_priority = pred.priority
        data.deterioration_prob = pred.deterioration_prob
    return data


@router.get("/health")
def health():
    return {
        "status": "ok",
        "ml_model": ml_service.model_name,
        "cv_backend": cv_service.backend,
    }


@router.post("/admin/seed")
def seed(force: bool = False, db: Session = Depends(get_db)):
    return seed_from_csv(db, force=force)


@router.get("/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)):
    assets = db.query(Asset).all()
    preds = {
        p.asset_id: p
        for p in db.query(Prediction).order_by(Prediction.created_at.desc()).all()
    }
    # keep latest only
    latest = {}
    for aid, p in preds.items():
        if aid not in latest:
            latest[aid] = p

    counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    scores = []
    for a in assets:
        p = latest.get(a.id)
        if p:
            counts[p.priority] = counts.get(p.priority, 0) + 1
            scores.append(p.risk_score)
    pending = db.query(InspectionReview).filter(InspectionReview.status == "pending").count()
    return DashboardStats(
        total_assets=len(assets),
        roads=sum(1 for a in assets if a.asset_type == "road"),
        bridges=sum(1 for a in assets if a.asset_type == "bridge"),
        critical=counts["Critical"],
        high=counts["High"],
        medium=counts["Medium"],
        low=counts["Low"],
        pending_reviews=pending,
        avg_risk_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
    )


@router.get("/assets", response_model=list[AssetOut])
def list_assets(
    asset_type: Optional[str] = None,
    priority: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Asset)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if q:
        like = f"%{q}%"
        query = query.filter((Asset.name.ilike(like)) | (Asset.asset_code.ilike(like)))
    assets = query.all()
    out = [_asset_out(db, a) for a in assets]
    if priority:
        out = [a for a in out if a.latest_priority == priority]
    out.sort(key=lambda a: -(a.latest_risk_score or 0))
    return out


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    return _asset_out(db, asset)


@router.get("/assets/{asset_id}/prediction", response_model=PredictionOut)
def get_prediction(asset_id: int, db: Session = Depends(get_db)):
    pred = _latest_prediction(db, asset_id)
    if not pred:
        raise HTTPException(404, "No prediction for asset")
    return pred


@router.get("/assets/{asset_id}/shap", response_model=ShapExplanation)
def get_shap(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    pred = _latest_prediction(db, asset_id)
    if pred and pred.shap_json:
        data = json.loads(pred.shap_json)
        return ShapExplanation(**data)
    return ShapExplanation(**ml_service.shap_for_asset(asset))


@router.post("/assets/{asset_id}/rescore", response_model=PredictionOut)
def rescore(asset_id: int, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    dets = db.query(Detection).filter(Detection.asset_id == asset_id).all()
    cv_score = cv_service.damage_score(
        [
            {
                "confidence": d.confidence,
                "severity": d.severity or "Low",
            }
            for d in dets
        ]
    ) if dets else min(1.0, (asset.damage_history_count or 0) * 0.18)
    result = ml_service.score_asset(asset, cv_damage_score=cv_score)
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
    db.commit()
    db.refresh(pred)
    return pred


@router.get("/map", response_model=list[RiskMapFeature])
def risk_map(
    priority: Optional[str] = None,
    asset_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    assets = db.query(Asset).all()
    features = []
    for a in assets:
        pred = _latest_prediction(db, a.id)
        if not pred:
            continue
        if priority and pred.priority != priority:
            continue
        if asset_type and a.asset_type != asset_type:
            continue
        features.append(
            RiskMapFeature(
                id=a.id,
                asset_code=a.asset_code,
                name=a.name,
                asset_type=a.asset_type,
                lat=a.lat,
                lon=a.lon,
                risk_score=pred.risk_score,
                priority=pred.priority,
                deterioration_prob=pred.deterioration_prob,
                cv_damage_score=pred.cv_damage_score,
            )
        )
    features.sort(key=lambda f: -f.risk_score)
    return features


@router.get("/priority", response_model=list[RiskMapFeature])
def priority_queue(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    return risk_map(db=db)[:limit]


@router.post("/detect", response_model=list[DetectionOut])
async def detect_damage(
    file: UploadFile = File(...),
    asset_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    content = await file.read()
    detections = cv_service.detect(content, asset_id=asset_id)
    saved = []
    fname = file.filename or "upload.jpg"
    save_path = UPLOAD_DIR / fname
    save_path.write_bytes(content)
    for d in detections:
        row = Detection(
            asset_id=asset_id,
            image_path=str(save_path),
            defect_type=d["defect_type"],
            confidence=d["confidence"],
            severity=d.get("severity"),
            bbox_json=json.dumps(d.get("bbox")),
        )
        db.add(row)
        saved.append(row)
    db.commit()
    for row in saved:
        db.refresh(row)

    if asset_id:
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if asset:
            cv_score = cv_service.damage_score(detections)
            result = ml_service.score_asset(asset, cv_damage_score=cv_score)
            shap = ml_service.shap_for_asset(asset)
            db.add(
                Prediction(
                    asset_id=asset.id,
                    model_name=result["model_name"],
                    deterioration_prob=result["deterioration_prob"],
                    risk_score=result["risk_score"],
                    priority=result["priority"],
                    shap_json=json.dumps(shap),
                    cv_damage_score=result["cv_damage_score"],
                )
            )
            db.commit()
    return saved


@router.post("/detect/annotate")
async def detect_annotate(file: UploadFile = File(...)):
    content = await file.read()
    detections = cv_service.detect(content)
    annotated = cv_service.annotate(content, detections)
    return Response(
        content=annotated,
        media_type="image/jpeg",
        headers={"X-Detection-Count": str(len(detections))},
    )


@router.get("/reviews", response_model=list[InspectionReviewOut])
def list_reviews(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(InspectionReview)
    if status:
        query = query.filter(InspectionReview.status == status)
    rows = query.order_by(InspectionReview.created_at.desc()).all()
    out = []
    for r in rows:
        item = InspectionReviewOut.model_validate(r)
        if r.asset:
            item.asset_code = r.asset.asset_code
            item.asset_name = r.asset.name
        out.append(item)
    return out


@router.post("/reviews", response_model=InspectionReviewOut)
def create_review(payload: InspectionReviewCreate, db: Session = Depends(get_db)):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(404, "Asset not found")
    row = InspectionReview(**payload.model_dump())
    if not row.notice_draft:
        pred = _latest_prediction(db, asset.id)
        risk = pred.risk_score if pred else 0
        priority = pred.priority if pred else "Medium"
        row.notice_draft = (
            f"INSPECTION NOTICE DRAFT\nAsset: {asset.asset_code} — {asset.name}\n"
            f"Risk: {risk} ({priority})\nAwaiting authorized review."
        )
    db.add(row)
    db.commit()
    db.refresh(row)
    item = InspectionReviewOut.model_validate(row)
    item.asset_code = asset.asset_code
    item.asset_name = asset.name
    return item


@router.patch("/reviews/{review_id}", response_model=InspectionReviewOut)
def update_review(review_id: int, payload: InspectionReviewCreate, db: Session = Depends(get_db)):
    row = db.query(InspectionReview).filter(InspectionReview.id == review_id).first()
    if not row:
        raise HTTPException(404, "Review not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        if k == "asset_id":
            continue
        setattr(row, k, v)
    if payload.status == "verified":
        row.used_for_retrain = True
        asset = db.query(Asset).filter(Asset.id == row.asset_id).first()
        if asset and payload.verified_condition:
            asset.condition_label = 1 if payload.verified_condition.lower() in ("poor", "critical", "damaged") else 0
    db.commit()
    db.refresh(row)
    item = InspectionReviewOut.model_validate(row)
    if row.asset:
        item.asset_code = row.asset.asset_code
        item.asset_name = row.asset.name
    return item


@router.get("/models/metrics")
def model_metrics():
    return ml_service.metrics()
