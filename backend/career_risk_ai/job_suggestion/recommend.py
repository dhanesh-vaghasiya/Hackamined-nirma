from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set

import joblib
import numpy as np
import pandas as pd

from job_suggestion.data_utils import (
    build_city_role_stats,
    load_jobs_dataset,
    lookup_city_role_stats,
    risk_to_numeric,
    role_skill_overlap,
    safe_float,
)
from paths import model_path as get_model_path, resolve_csv_input


def _make_feature_row(
    semantic_similarity: float,
    overlap_ratio: float,
    gap_count: int,
    candidate_stats: Dict[str, float],
    current_stats: Dict[str, float],
    city_switch: float,
) -> Dict[str, float]:
    return {
        "semantic_similarity": safe_float(semantic_similarity),
        "skill_overlap_ratio": safe_float(overlap_ratio),
        "skill_gap_count": safe_float(float(gap_count)),
        "candidate_demand_score": safe_float(candidate_stats["demand_score"]),
        "candidate_latest_demand_score": safe_float(candidate_stats["latest_demand_score"]),
        "candidate_trend": safe_float(candidate_stats["trend"]),
        "demand_lift_vs_current": safe_float(candidate_stats["demand_score"] - current_stats["demand_score"]),
        "trend_lift_vs_current": safe_float(candidate_stats["trend"] - current_stats["trend"]),
        "city_switch": safe_float(city_switch),
    }


def _transition_confidence(model, x_df: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(x_df)
        if probs.ndim == 2 and probs.shape[1] >= 2:
            return probs[:, 1]
    preds = model.predict(x_df)
    return np.asarray(preds, dtype=float)


def recommend_next_roles(
    user_profile: Dict[str, object],
    model_path: str | None = None,
    top_k: int = 3,
    min_confidence: float = 0.45,
    use_latest_market_data: bool = True,
) -> Dict[str, object]:
    artifact_path = (
        Path(model_path)
        if model_path
        else get_model_path("job_suggestion", "job_suggestion_models.pkl")
    )

    artifact = joblib.load(artifact_path)
    feature_columns = artifact["metadata"]["feature_columns"]
    roles: List[str] = artifact["roles"]
    cities: List[str] = artifact["cities"]
    role_profiles = artifact["role_profiles"]
    city_role_stats: pd.DataFrame = artifact["city_role_stats"]
    role_vectors: np.ndarray = artifact["role_vectors"]
    embedder = artifact["embedder"]
    transition_model = artifact["transition_model"]
    rank_model = artifact["rank_model"]

    if use_latest_market_data:
        jobs_path = resolve_csv_input("jobs.csv")
        if jobs_path.exists():
            latest_jobs = load_jobs_dataset(str(jobs_path))
            latest_city_stats = build_city_role_stats(latest_jobs)
            if not latest_city_stats.empty:
                city_role_stats = latest_city_stats

    current_role = str(user_profile.get("current_role", "")).strip()
    current_city = str(user_profile.get("city", "")).strip()
    user_skills: Set[str] = set([str(s).strip().lower() for s in user_profile.get("skills", []) if str(s).strip()])
    risk_level = str(user_profile.get("risk_level", "MEDIUM"))
    risk_numeric = risk_to_numeric(risk_level)

    if not current_role:
        raise ValueError("user_profile.current_role is required")
    if not current_city:
        raise ValueError("user_profile.city is required")

    user_text = f"{current_role}. Skills: {', '.join(sorted(user_skills))}"
    user_vector = embedder.encode([user_text])[0]

    role_norm = np.linalg.norm(role_vectors, axis=1) + 1e-9
    user_norm = np.linalg.norm(user_vector) + 1e-9
    role_sims = (role_vectors @ user_vector) / (role_norm * user_norm)

    current_stats = lookup_city_role_stats(city_role_stats, current_city, current_role)
    if current_city not in cities:
        cities = sorted(set(cities + [current_city]))

    candidates = []
    for role_idx, candidate_role in enumerate(roles):
        if candidate_role == current_role:
            continue

        candidate_skills = set(role_profiles[candidate_role]["skills"])
        overlap_ratio, gap_count, missing_skills = role_skill_overlap(user_skills, candidate_skills)
        semantic_similarity = float(role_sims[role_idx])

        for candidate_city in cities:
            candidate_stats = lookup_city_role_stats(city_role_stats, candidate_city, candidate_role)
            city_switch = 1.0 if candidate_city != current_city else 0.0

            feature_row = _make_feature_row(
                semantic_similarity=semantic_similarity,
                overlap_ratio=overlap_ratio,
                gap_count=gap_count,
                candidate_stats=candidate_stats,
                current_stats=current_stats,
                city_switch=city_switch,
            )

            x_row = pd.DataFrame([feature_row])[feature_columns]
            confidence = float(_transition_confidence(transition_model, x_row)[0])
            base_score = float(rank_model.predict(x_row)[0])

            # Risk-aware preference: for high-risk users, bias toward stronger demand and lower move friction.
            risk_boost = risk_numeric * (0.15 * feature_row["candidate_demand_score"] + 0.1 * (1.0 - city_switch))
            final_score = base_score + (0.25 * confidence) + risk_boost

            candidates.append(
                {
                    "role": candidate_role,
                    "city": candidate_city,
                    "recommendation_score": round(float(final_score), 4),
                    "confidence": round(confidence, 4),
                    "semantic_similarity": round(semantic_similarity, 4),
                    "missing_skills": missing_skills[:5],
                    "reasoning_summary": (
                        "High transition feasibility with good demand trend"
                        if confidence >= 0.65
                        else "Moderate transition feasibility with demand support"
                    ),
                }
            )

    candidate_df = pd.DataFrame(candidates)
    if candidate_df.empty:
        raise RuntimeError("No candidate roles could be generated")

    feasible_df = candidate_df[candidate_df["confidence"] >= min_confidence].copy()
    if feasible_df.empty:
        feasible_df = candidate_df.sort_values(["confidence", "recommendation_score"], ascending=False).head(8)

    feasible_df = feasible_df.sort_values(["recommendation_score", "confidence"], ascending=False)

    city_df = feasible_df[feasible_df["city"] == current_city].copy()
    other_df = feasible_df[feasible_df["city"] != current_city].copy()

    best_current_city_role = city_df.head(1)
    best_overall_role = feasible_df.head(1)

    # Build role-diverse top next-step roles.
    next_step_roles = []
    seen_roles = set()
    for _, row in feasible_df.iterrows():
        if row["role"] in seen_roles:
            continue
        next_step_roles.append(
            {
                "role": row["role"],
                "city": row["city"],
                "recommendation_score": float(row["recommendation_score"]),
                "confidence": float(row["confidence"]),
                "missing_skills": list(row["missing_skills"]),
                "reasoning_summary": row["reasoning_summary"],
            }
        )
        seen_roles.add(row["role"])
        if len(next_step_roles) >= top_k:
            break

    current_city_recommendations = []
    for _, row in city_df.head(top_k).iterrows():
        current_city_recommendations.append(
            {
                "role": row["role"],
                "city": row["city"],
                "recommendation_score": float(row["recommendation_score"]),
                "confidence": float(row["confidence"]),
                "missing_skills": list(row["missing_skills"]),
                "reasoning_summary": row["reasoning_summary"],
            }
        )

    fallback_city_recommendations = []
    if len(current_city_recommendations) < 2:
        for _, row in other_df.head(top_k).iterrows():
            fallback_city_recommendations.append(
                {
                    "role": row["role"],
                    "city": row["city"],
                    "recommendation_score": float(row["recommendation_score"]),
                    "confidence": float(row["confidence"]),
                    "missing_skills": list(row["missing_skills"]),
                    "reasoning_summary": row["reasoning_summary"],
                }
            )

    def _first_or_empty(df: pd.DataFrame) -> Dict[str, object]:
        if df.empty:
            return {
                "role": "",
                "city": "",
                "recommendation_score": 0.0,
                "confidence": 0.0,
                "missing_skills": [],
                "reasoning_summary": "No role passed feasibility threshold",
            }
        row = df.iloc[0]
        return {
            "role": row["role"],
            "city": row["city"],
            "recommendation_score": float(row["recommendation_score"]),
            "confidence": float(row["confidence"]),
            "missing_skills": list(row["missing_skills"]),
            "reasoning_summary": row["reasoning_summary"],
        }

    return {
        "best_current_city_role": _first_or_empty(best_current_city_role),
        "best_overall_role": _first_or_empty(best_overall_role),
        "next_step_roles": next_step_roles,
        "current_city_recommendations": current_city_recommendations,
        "fallback_city_recommendations": fallback_city_recommendations,
        "model_info": artifact["metadata"],
    }
