from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_code = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=False)
    asset_type = Column(String(32), nullable=False)  # road | bridge
    material = Column(String(64), nullable=True)
    age_years = Column(Float, nullable=False)
    length_m = Column(Float, nullable=True)
    lanes = Column(Integer, nullable=True)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    traffic_aadt = Column(Float, nullable=True)
    last_inspection_score = Column(Float, nullable=True)
    years_since_inspection = Column(Float, nullable=True)
    years_since_maintenance = Column(Float, nullable=True)
    rainfall_mm = Column(Float, nullable=True)
    temp_avg_c = Column(Float, nullable=True)
    damage_history_count = Column(Integer, default=0)
    condition_label = Column(Integer, nullable=True)  # 0 good, 1 poor (training)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("Prediction", back_populates="asset")
    detections = relationship("Detection", back_populates="asset")
    reviews = relationship("InspectionReview", back_populates="asset")


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    model_name = Column(String(64), nullable=False)
    deterioration_prob = Column(Float, nullable=False)
    risk_score = Column(Float, nullable=False)
    priority = Column(String(16), nullable=False)  # Critical|High|Medium|Low
    shap_json = Column(Text, nullable=True)
    cv_damage_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="predictions")


class Detection(Base):
    __tablename__ = "detections"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=True)
    image_path = Column(String(512), nullable=False)
    defect_type = Column(String(64), nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(16), nullable=True)
    bbox_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="detections")


class InspectionReview(Base):
    __tablename__ = "inspection_reviews"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    status = Column(String(32), default="pending")  # pending|verified|rejected
    reviewer_notes = Column(Text, nullable=True)
    verified_condition = Column(String(32), nullable=True)
    notice_draft = Column(Text, nullable=True)
    used_for_retrain = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    asset = relationship("Asset", back_populates="reviews")
