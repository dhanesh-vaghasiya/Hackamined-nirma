from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Dict


def _ensure_career_module_on_path() -> None:
    backend_root = Path(__file__).resolve().parents[3]
    career_root = backend_root / "career_risk_ai"
    if str(career_root) not in sys.path:
        sys.path.insert(0, str(career_root))


def _risk_level(score: float) -> str:
    if score > 0.6:
        return "HIGH"
    if score > 0.4:
        return "MEDIUM"
    return "LOW"


def analyze_profile_career_risk(profile: Dict[str, object]) -> Dict[str, object]:
    _ensure_career_module_on_path()

    recommend_next_roles = importlib.import_module("job_suggestion.recommend").recommend_next_roles
    explain_prediction = importlib.import_module("pipeline.explainability").explain_prediction
    generate_features = importlib.import_module("pipeline.feature_generator").generate_features
    predict_risk = importlib.import_module("pipeline.predict_risk").predict_risk
    compute_trends = importlib.import_module("pipeline.trend_model").compute_trends

    trends = compute_trends()
    features = generate_features(profile, trends)

    risk_score = float(predict_risk(features))
    risk_level = _risk_level(risk_score)

    explanation = explain_prediction(features)
    suggestion_user = {
        "current_role": profile.get("normalized_job_title", ""),
        "city": profile.get("city", ""),
        "skills": profile.get("skills", []),
        "experience_years": profile.get("experience_years", 0),
        "risk_level": risk_level,
    }
    suggestions = recommend_next_roles(user_profile=suggestion_user, top_k=3, use_latest_market_data=True)

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "features_used": features,
        "explainability": explanation,
        "job_suggestions": suggestions,
    }
