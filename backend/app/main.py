"""FastAPI entrypoint for Urban Infrastructure Risk Prediction."""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.api.routes import router
from app.db.database import SessionLocal, init_db
from app.services.seed import seed_from_csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_from_csv(db, force=False)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Urban Infrastructure Risk Prediction API",
    description=(
        "AI-based urban infrastructure deterioration prediction & inspection "
        "prioritization: ML + YOLO CV + SHAP + GIS decision support."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "project": "AI Based Urban Infrastructure Deterioration Prediction & Inspection Prioritization System",
        "docs": "/docs",
        "api": "/api/health",
    }
