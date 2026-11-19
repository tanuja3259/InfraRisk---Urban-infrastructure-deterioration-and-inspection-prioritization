from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AssetCreate(BaseModel):
    asset_code: str
    name: str
    asset_type: str
    material: Optional[str] = None
    age_years: float
    length_m: Optional[float] = None
    lanes: Optional[int] = None
    lat: float
    lon: float
    traffic_aadt: Optional[float] = None
    last_inspection_score: Optional[float] = None
    years_since_inspection: Optional[float] = None
    years_since_maintenance: Optional[float] = None
    rainfall_mm: Optional[float] = None
    temp_avg_c: Optional[float] = None
    damage_history_count: int = 0


class AssetOut(AssetCreate):
    id: int
    condition_label: Optional[int] = None
    created_at: Optional[datetime] = None
    latest_risk_score: Optional[float] = None
    latest_priority: Optional[str] = None
    deterioration_prob: Optional[float] = None

    class Config:
        from_attributes = True


class PredictionOut(BaseModel):
    id: int
    asset_id: int
    model_name: str
    deterioration_prob: float
    risk_score: float
    priority: str
    shap_json: Optional[str] = None
    cv_damage_score: float = 0.0
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DetectionOut(BaseModel):
    id: int
    asset_id: Optional[int] = None
    image_path: str
    defect_type: str
    confidence: float
    severity: Optional[str] = None
    bbox_json: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InspectionReviewCreate(BaseModel):
    asset_id: int
    status: str = "pending"
    reviewer_notes: Optional[str] = None
    verified_condition: Optional[str] = None
    notice_draft: Optional[str] = None


class InspectionReviewOut(InspectionReviewCreate):
    id: int
    used_for_retrain: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    class Config:
        from_attributes = True


class RiskMapFeature(BaseModel):
    id: int
    asset_code: str
    name: str
    asset_type: str
    lat: float
    lon: float
    risk_score: float
    priority: str
    deterioration_prob: float
    cv_damage_score: float = 0.0


class DashboardStats(BaseModel):
    total_assets: int
    roads: int
    bridges: int
    critical: int
    high: int
    medium: int
    low: int
    pending_reviews: int
    avg_risk_score: float


class ShapExplanation(BaseModel):
    asset_id: int
    feature_contributions: list[dict[str, Any]] = Field(default_factory=list)
    base_value: float = 0.0
    model_name: str = "xgboost"
