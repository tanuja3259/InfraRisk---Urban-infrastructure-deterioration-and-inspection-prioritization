"""Shared feature definitions for deterioration models."""

FEATURE_COLUMNS = [
    "age_years",
    "traffic_aadt",
    "last_inspection_score",
    "years_since_inspection",
    "years_since_maintenance",
    "rainfall_mm",
    "temp_avg_c",
    "damage_history_count",
    "length_m",
    "lanes",
    "asset_type_bridge",
    "material_concrete",
    "material_asphalt",
    "material_steel",
]

DAMAGE_LABELS = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
    "CORROSION": "Corrosion",
    "SPALLING": "Spalling",
}


def asset_to_feature_row(asset) -> dict:
    material = (asset.material or "").lower()
    return {
        "age_years": float(asset.age_years or 0),
        "traffic_aadt": float(asset.traffic_aadt or 0),
        "last_inspection_score": float(asset.last_inspection_score or 5),
        "years_since_inspection": float(asset.years_since_inspection or 0),
        "years_since_maintenance": float(asset.years_since_maintenance or 0),
        "rainfall_mm": float(asset.rainfall_mm or 0),
        "temp_avg_c": float(asset.temp_avg_c or 20),
        "damage_history_count": float(asset.damage_history_count or 0),
        "length_m": float(asset.length_m or 0),
        "lanes": float(asset.lanes or 2),
        "asset_type_bridge": 1.0 if asset.asset_type == "bridge" else 0.0,
        "material_concrete": 1.0 if "concrete" in material else 0.0,
        "material_asphalt": 1.0 if "asphalt" in material else 0.0,
        "material_steel": 1.0 if "steel" in material else 0.0,
    }
