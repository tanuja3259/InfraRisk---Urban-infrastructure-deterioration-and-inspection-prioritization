# AI Based Urban Infrastructure Deterioration Prediction & Inspection Prioritization System

College PBL implementation of **InfraRisk** — an AI decision-support platform that predicts road/bridge deterioration, detects visible defects, fuses evidence into an explainable **Infrastructure Risk Score**, and ranks assets for inspection on a GIS dashboard.

Aligned with the project synopsis, presentation, and system architecture:

```
Data Ingestion → ML deterioration models + YOLO CV → Infrastructure Risk Score (SHAP)
  → Inspection Priority (Critical/High/Medium/Low) → GIS Web Dashboard → Human Review
  ↺ feedback loop retrains models
```

## Team

Sharayu Bodkhe · Tanuja Bhatt · Isha Rajput · Anshika Arkvanshi  
Guide: Dr. Shailendra Narayan Singh · Graphic Era Deemed to be University

## Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, Tailwind CSS, Leaflet + OpenStreetMap, Recharts |
| Backend | Python FastAPI |
| ML | scikit-learn, XGBoost, LightGBM, MLP |
| CV | Ultralytics YOLO (optional weights) + OpenCV heuristic fallback |
| Explainability | SHAP |
| DB | SQLite (demo) — swap to PostgreSQL + PostGIS for production |

## Quick start

### 1. Backend

```bash
cd urban-infra-risk/backend
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
python ml/generate_sample_data.py
python ml/train_deterioration.py
uvicorn app.main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd urban-infra-risk/frontend
npm install
npm run dev
```

Dashboard: http://127.0.0.1:5173

## Modules

1. **Asset data management** — roads/bridges with age, material, traffic, inspection & maintenance history, weather.
2. **Deterioration prediction** — RF / XGBoost / LightGBM / neural net; best model selected by ROC-AUC.
3. **Computer vision** — defect detection (D00/D10/D20/D40 + severity). Place trained YOLO weights at `backend/models/yolo_road_damage.pt` to enable YOLO; otherwise OpenCV demo detector runs.
4. **Risk fusion** — transparent weighted Infrastructure Risk Score + priority bands.
5. **SHAP explanations** — per-asset feature contributions on the asset detail page.
6. **GIS dashboard** — risk-coded map + priority queue (Dehradun-area sample coordinates).
7. **Human review** — pending Critical/High cases with notice drafts; verified outcomes stored for feedback.

## Optional: YOLO on RDD2022

Train Ultralytics YOLO on [RDD2022](https://github.com/sekilab/RoadDamageDetector) (classes D00, D10, D20, D40) and copy the best weights to:

```
backend/models/yolo_road_damage.pt
```

## Evaluation metrics (as in synopsis)

- ML: ROC-AUC, precision, recall, F1 → written to `backend/models/metrics.json`
- CV: precision / recall / mAP when using trained YOLO
- Priority quality: concentration of verified poor assets near top of ranking

## Project layout

```
urban-infra-risk/
  backend/
    app/           # FastAPI, DB, services, routes
    ml/            # sample data, training, risk score
    models/        # trained joblib + metrics
    data/          # CSV + SQLite
  frontend/        # React GIS dashboard
```

## Disclaimer

This system is **decision support only**. It does not replace qualified engineering inspection or legal/administrative decisions.
