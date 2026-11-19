"""Train RF / XGBoost / LightGBM / NN baselines for deterioration prediction."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

from features import FEATURE_COLUMNS

try:
    from xgboost import XGBClassifier
except ImportError:  # pragma: no cover
    XGBClassifier = None

try:
    from lightgbm import LGBMClassifier
except ImportError:  # pragma: no cover
    LGBMClassifier = None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "sample_assets.csv"
MODEL_DIR = ROOT / "models"


def encode_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    work = df.copy()
    work["asset_type_bridge"] = (work["asset_type"] == "bridge").astype(float)
    material = work["material"].fillna("").str.lower()
    work["material_concrete"] = material.str.contains("concrete").astype(float)
    work["material_asphalt"] = material.str.contains("asphalt").astype(float)
    work["material_steel"] = material.str.contains("steel").astype(float)
    for col in FEATURE_COLUMNS:
        if col not in work.columns:
            work[col] = 0.0
    X = work[FEATURE_COLUMNS].astype(float).fillna(0.0)
    y = work["condition_label"].astype(int).values
    return X, y


def train_all(data_path: Path, model_dir: Path) -> dict:
    df = pd.read_csv(data_path)
    X, y = encode_dataframe(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model_dir.mkdir(parents=True, exist_ok=True)
    metrics: dict = {}

    models = {
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, random_state=42, class_weight="balanced"
        ),
    }
    if XGBClassifier is not None:
        models["xgboost"] = XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )
    if LGBMClassifier is not None:
        models["lightgbm"] = LGBMClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.08,
            random_state=42,
            verbose=-1,
        )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    nn = MLPClassifier(
        hidden_layer_sizes=(64, 32),
        max_iter=400,
        random_state=42,
        early_stopping=True,
    )
    nn.fit(X_train_s, y_train)
    models["neural_net"] = ("scaled", nn, scaler)

    best_name, best_auc = None, -1.0
    for name, model in models.items():
        if isinstance(model, tuple):
            _, clf, scl = model
            proba = clf.predict_proba(scl.transform(X_test))[:, 1]
            pred = (proba >= 0.5).astype(int)
            joblib.dump({"model": clf, "scaler": scl, "scaled": True}, model_dir / f"{name}.joblib")
        else:
            model.fit(X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
            pred = model.predict(X_test)
            joblib.dump({"model": model, "scaler": None, "scaled": False}, model_dir / f"{name}.joblib")

        auc = float(roc_auc_score(y_test, proba)) if len(np.unique(y_test)) > 1 else 0.0
        report = classification_report(y_test, pred, output_dict=True, zero_division=0)
        metrics[name] = {
            "roc_auc": auc,
            "precision": report["1"]["precision"] if "1" in report else 0.0,
            "recall": report["1"]["recall"] if "1" in report else 0.0,
            "f1": report["1"]["f1-score"] if "1" in report else 0.0,
        }
        if auc > best_auc:
            best_auc, best_name = auc, name

    meta = {
        "feature_columns": FEATURE_COLUMNS,
        "best_model": best_name,
        "metrics": metrics,
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    (model_dir / "metrics.json").write_text(json.dumps(meta, indent=2))
    (model_dir / "best_model.txt").write_text(best_name or "random_forest")
    print(json.dumps(meta, indent=2))
    return meta


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATA))
    parser.add_argument("--model-dir", type=str, default=str(MODEL_DIR))
    args = parser.parse_args()
    train_all(Path(args.data), Path(args.model_dir))


if __name__ == "__main__":
    main()
