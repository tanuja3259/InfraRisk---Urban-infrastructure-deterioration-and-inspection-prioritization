"""Deterioration model loading, inference, and SHAP explanations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ML_DIR = ROOT / "ml"
MODEL_DIR = ROOT / "models"
sys.path.insert(0, str(ML_DIR))

from features import FEATURE_COLUMNS, asset_to_feature_row  # noqa: E402
from risk_score import compute_risk_score, priority_band, recommended_action  # noqa: E402


class MLService:
    def __init__(self):
        self.bundle = None
        self.model_name = "heuristic"
        self._shap_explainer = None
        self.reload()

    def reload(self):
        best = MODEL_DIR / "best_model.txt"
        name = best.read_text().strip() if best.exists() else "xgboost"
        path = MODEL_DIR / f"{name}.joblib"
        if not path.exists():
            # fallback order
            for candidate in ("xgboost", "lightgbm", "random_forest", "neural_net"):
                p = MODEL_DIR / f"{candidate}.joblib"
                if p.exists():
                    path, name = p, candidate
                    break
        if path.exists():
            self.bundle = joblib.load(path)
            self.model_name = name
            self._shap_explainer = None
        else:
            self.bundle = None
            self.model_name = "heuristic"

    def _matrix(self, assets) -> pd.DataFrame:
        rows = [asset_to_feature_row(a) for a in assets]
        return pd.DataFrame(rows)[FEATURE_COLUMNS].astype(float)

    def predict_proba(self, asset) -> float:
        if self.bundle is None:
            # Transparent heuristic when models are not trained yet
            f = asset_to_feature_row(asset)
            score = (
                max(0, f["age_years"] - 15) * 0.02
                + max(0, 6 - f["last_inspection_score"]) * 0.08
                + f["years_since_inspection"] * 0.05
                + f["years_since_maintenance"] * 0.03
                + (f["traffic_aadt"] / 40000) * 0.15
                + f["damage_history_count"] * 0.06
            )
            return float(np.clip(score, 0.05, 0.95))

        X = self._matrix([asset])
        model = self.bundle["model"]
        if self.bundle.get("scaled") and self.bundle.get("scaler") is not None:
            X_in = self.bundle["scaler"].transform(X)
        else:
            X_in = X
        return float(model.predict_proba(X_in)[0][1])

    def score_asset(self, asset, cv_damage_score: float = 0.0) -> dict:
        prob = self.predict_proba(asset)
        risk = compute_risk_score(
            deterioration_prob=prob,
            cv_damage_score=cv_damage_score,
            years_since_inspection=float(asset.years_since_inspection or 0),
            traffic_aadt=float(asset.traffic_aadt or 0),
            last_inspection_score=float(asset.last_inspection_score or 7),
        )
        priority = priority_band(risk)
        return {
            "model_name": self.model_name,
            "deterioration_prob": round(prob, 4),
            "risk_score": risk,
            "priority": priority,
            "cv_damage_score": round(cv_damage_score, 4),
            "recommended_action": recommended_action(priority),
        }

    def shap_for_asset(self, asset) -> dict:
        if self.bundle is None or self.bundle.get("scaled"):
            # Approximate contributions from feature magnitudes for heuristic / NN
            f = asset_to_feature_row(asset)
            contribs = [
                {"feature": k, "value": float(v), "contribution": float(v) * 0.01}
                for k, v in sorted(f.items(), key=lambda x: -abs(x[1]))[:8]
            ]
            return {
                "asset_id": asset.id,
                "model_name": self.model_name,
                "base_value": 0.3,
                "feature_contributions": contribs,
            }

        try:
            import shap

            model = self.bundle["model"]
            X = self._matrix([asset])
            if self._shap_explainer is None:
                self._shap_explainer = shap.TreeExplainer(model)
            sv = self._shap_explainer.shap_values(X)
            if isinstance(sv, list):
                values = np.array(sv[1][0])
                base = float(self._shap_explainer.expected_value[1])
            else:
                values = np.array(sv[0])
                base = float(
                    self._shap_explainer.expected_value
                    if np.isscalar(self._shap_explainer.expected_value)
                    else self._shap_explainer.expected_value[1]
                )
            contribs = [
                {
                    "feature": FEATURE_COLUMNS[i],
                    "value": float(X.iloc[0, i]),
                    "contribution": float(values[i]),
                }
                for i in range(len(FEATURE_COLUMNS))
            ]
            contribs.sort(key=lambda c: abs(c["contribution"]), reverse=True)
            return {
                "asset_id": asset.id,
                "model_name": self.model_name,
                "base_value": base,
                "feature_contributions": contribs[:12],
            }
        except Exception as exc:  # pragma: no cover
            return {
                "asset_id": asset.id,
                "model_name": self.model_name,
                "base_value": 0.0,
                "feature_contributions": [],
                "error": str(exc),
            }

    def metrics(self) -> dict:
        path = MODEL_DIR / "metrics.json"
        if path.exists():
            return json.loads(path.read_text())
        return {"best_model": self.model_name, "metrics": {}, "note": "Models not trained yet"}


ml_service = MLService()
