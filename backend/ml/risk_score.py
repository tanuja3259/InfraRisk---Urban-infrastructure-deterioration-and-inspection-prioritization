"""Infrastructure Risk Score fusion and priority banding."""

from __future__ import annotations

PRIORITY_THRESHOLDS = {
    "Critical": 48.0,
    "High": 36.0,
    "Medium": 24.0,
}


def compute_risk_score(
    deterioration_prob: float,
    cv_damage_score: float = 0.0,
    years_since_inspection: float = 0.0,
    traffic_aadt: float = 0.0,
    last_inspection_score: float = 7.0,
) -> float:
    """
    Transparent weighted fusion (0-100).
    Weights are configurable for municipal policy tuning.
    """
    insp_penalty = min(years_since_inspection / 6.0, 1.0) * 12.0
    traffic_factor = min(traffic_aadt / 50000.0, 1.0) * 8.0
    condition_penalty = max(0.0, (6.0 - last_inspection_score) / 6.0) * 8.0
    score = (
        deterioration_prob * 45.0
        + min(cv_damage_score, 1.0) * 20.0
        + insp_penalty
        + traffic_factor
        + condition_penalty
    )
    return float(round(min(max(score, 0.0), 100.0), 2))


def priority_band(risk_score: float) -> str:
    if risk_score >= PRIORITY_THRESHOLDS["Critical"]:
        return "Critical"
    if risk_score >= PRIORITY_THRESHOLDS["High"]:
        return "High"
    if risk_score >= PRIORITY_THRESHOLDS["Medium"]:
        return "Medium"
    return "Low"


def recommended_action(priority: str) -> str:
    return {
        "Critical": "Schedule immediate field inspection within 7 days; draft emergency notice.",
        "High": "Prioritize inspection within 30 days; prepare maintenance assessment.",
        "Medium": "Include in next quarterly inspection cycle; monitor after rainfall events.",
        "Low": "Continue routine scheduled inspection; no urgent action required.",
    }.get(priority, "Review manually.")
