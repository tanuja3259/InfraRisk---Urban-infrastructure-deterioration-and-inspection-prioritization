"""YOLO-based road/bridge defect detection with heuristic fallback."""

from __future__ import annotations

import json
from pathlib import Path

import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))
from features import DAMAGE_LABELS  # noqa: E402

WEIGHTS = ROOT / "models" / "yolo_road_damage.pt"


class CVService:
    """
    Prefer Ultralytics YOLO when weights exist.
    Otherwise use OpenCV heuristics (dark blobs / edge density) for demo.
    Compatible with RDD classes: D00, D10, D20, D40 (+ corrosion/spalling tags).
    """

    def __init__(self):
        self.model = None
        self.backend = "opencv_heuristic"
        self._try_load_yolo()

    def _try_load_yolo(self):
        if not WEIGHTS.exists():
            return
        try:
            from ultralytics import YOLO

            self.model = YOLO(str(WEIGHTS))
            self.backend = "yolo"
        except Exception:
            self.model = None
            self.backend = "opencv_heuristic"

    def detect(self, image_bytes: bytes, asset_id: int | None = None) -> list[dict]:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            return []
        if self.model is not None:
            return self._yolo_detect(image)
        return self._heuristic_detect(image)

    def _yolo_detect(self, image) -> list[dict]:
        results = self.model.predict(image, verbose=False)
        detections = []
        for r in results:
            names = r.names
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = [float(x) for x in box.xyxy[0].tolist()]
                label = names.get(cls_id, str(cls_id))
                detections.append(
                    {
                        "defect_type": label,
                        "label_name": DAMAGE_LABELS.get(label, label),
                        "confidence": round(conf, 4),
                        "severity": self._severity(conf, xyxy, image.shape),
                        "bbox": xyxy,
                    }
                )
        return detections

    def _heuristic_detect(self, image) -> list[dict]:
        """Demo detector: dark regions ≈ potholes; dense edges ≈ cracks."""
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        detections = []

        # Pothole-like dark blobs
        _, dark = cv2.threshold(blur, 60, 255, cv2.THRESH_BINARY_INV)
        dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (h * w) * 0.002 or area > (h * w) * 0.25:
                continue
            x, y, bw, bh = cv2.boundingRect(cnt)
            conf = float(np.clip(area / (h * w * 0.08), 0.35, 0.92))
            detections.append(
                {
                    "defect_type": "D40",
                    "label_name": DAMAGE_LABELS["D40"],
                    "confidence": round(conf, 4),
                    "severity": self._severity(conf, [x, y, x + bw, y + bh], image.shape),
                    "bbox": [float(x), float(y), float(x + bw), float(y + bh)],
                }
            )

        # Crack-like edge density tiles
        edges = cv2.Canny(blur, 80, 180)
        tile = 64
        for ty in range(0, h - tile, tile):
            for tx in range(0, w - tile, tile):
                patch = edges[ty : ty + tile, tx : tx + tile]
                density = float(np.mean(patch > 0))
                if density < 0.12:
                    continue
                conf = float(np.clip(density * 2.2, 0.4, 0.88))
                label = "D20" if density > 0.22 else "D00"
                detections.append(
                    {
                        "defect_type": label,
                        "label_name": DAMAGE_LABELS[label],
                        "confidence": round(conf, 4),
                        "severity": "High" if density > 0.25 else "Medium",
                        "bbox": [float(tx), float(ty), float(tx + tile), float(ty + tile)],
                    }
                )

        # Keep top detections to avoid noise
        detections.sort(key=lambda d: d["confidence"], reverse=True)
        return detections[:12]

    @staticmethod
    def _severity(conf: float, bbox, shape) -> str:
        h, w = shape[:2]
        x1, y1, x2, y2 = bbox
        area_ratio = abs((x2 - x1) * (y2 - y1)) / float(h * w + 1e-6)
        score = 0.6 * conf + 0.4 * min(area_ratio * 8, 1.0)
        if score >= 0.7:
            return "High"
        if score >= 0.45:
            return "Medium"
        return "Low"

    @staticmethod
    def damage_score(detections: list[dict]) -> float:
        if not detections:
            return 0.0
        sev_w = {"High": 1.0, "Medium": 0.65, "Low": 0.35}
        vals = [d["confidence"] * sev_w.get(d.get("severity", "Low"), 0.4) for d in detections]
        return float(np.clip(max(vals) * 0.7 + (sum(vals) / len(vals)) * 0.3, 0.0, 1.0))

    def annotate(self, image_bytes: bytes, detections: list[dict]) -> bytes:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            return image_bytes
        colors = {
            "D40": (0, 0, 255),
            "D20": (0, 140, 255),
            "D00": (0, 255, 255),
            "D10": (255, 180, 0),
        }
        for d in detections:
            x1, y1, x2, y2 = map(int, d["bbox"])
            color = colors.get(d["defect_type"], (80, 200, 120))
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = f"{d['defect_type']} {d['confidence']:.2f}"
            cv2.putText(image, label, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
        ok, buf = cv2.imencode(".jpg", image)
        return buf.tobytes() if ok else image_bytes


cv_service = CVService()
