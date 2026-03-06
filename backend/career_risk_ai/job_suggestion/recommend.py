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

# ---------- Cached artifacts (loaded once) ----------
_cached_artifact = None
_cached_city_role_stats = None


def _load_artifact(artifact_path: Path):
    global _cached_artifact
    if _cached_artifact is None or _cached_artifact["_path"] != str(artifact_path):
        artifact = joblib.load(artifact_path)
        artifact["_path"] = str(artifact_path)
        _cached_artifact = artifact
    return _cached_artifact


def _load_latest_city_stats():
    global _cached_city_role_stats
    if _cached_city_role_stats is None:
        jobs_path = resolve_csv_input("jobs.csv")
        if jobs_path.exists():
            latest_jobs = load_jobs_dataset(str(jobs_path))
            _cached_city_role_stats = build_city_role_stats(latest_jobs)
    return _cached_city_role_stats


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

    artifact = _load_artifact(artifact_path)
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
        latest_city_stats = _load_latest_city_stats()
        if latest_city_stats is not None and not latest_city_stats.empty:
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

            # ---- Feature-based scoring (replaces broken LightGBM models) ----
            # Weighted combination of meaningful signals:
            #   - semantic_similarity: how related is this role to current role (0-1)
            #   - skill_overlap_ratio: how many required skills the user already has (0-1)
            #   - demand signals: is this role actually hiring?
            #   - trend: is demand growing?
            #   - city_switch penalty: prefer same city
            #   - gap penalty: penalize roles requiring many new skills

            demand = candidate_stats["demand_score"]
            latest = candidate_stats["latest_demand_score"]
            trend = candidate_stats["trend"]

            # Normalize gap_count (fewer gaps = better). Cap at 20 for normalization.
            gap_penalty = min(gap_count, 20) / 20.0

            # Composite score with tuned weights
            score = (
                0.30 * semantic_similarity
                + 0.20 * overlap_ratio
                + 0.20 * max(demand, latest)
                + 0.10 * max(0, min(trend, 1.0))
                - 0.10 * gap_penalty
                - 0.05 * city_switch
            )

            # Risk-aware boost: high-risk users get extra push toward in-demand roles
            risk_boost = risk_numeric * 0.10 * max(demand, latest)
            score += risk_boost

            # Clamp to 0-1
            score = max(0.0, min(1.0, score))

            # Confidence: blend of similarity and demand evidence
            confidence = min(1.0, 0.5 * semantic_similarity + 0.3 * overlap_ratio + 0.2 * max(demand, latest))

            # Build reasoning
            reasons = []
            if semantic_similarity >= 0.4:
                reasons.append("Strong role alignment")
            elif semantic_similarity >= 0.25:
                reasons.append("Moderate role alignment")
            if overlap_ratio >= 0.3:
                reasons.append("good skill match")
            if max(demand, latest) >= 0.05:
                reasons.append("active hiring demand")
            if trend > 0.1:
                reasons.append("growing demand trend")
            if city_switch == 0:
                reasons.append("available in your city")
            if not reasons:
                reasons.append("Potential career path")
            reasoning = reasons[0][0].upper() + reasons[0][1:] + (", " + ", ".join(reasons[1:]) if len(reasons) > 1 else "")

            candidates.append(
                {
                    "role": candidate_role,
                    "city": candidate_city,
                    "recommendation_score": round(score, 4),
                    "confidence": round(confidence, 4),
                    "semantic_similarity": round(semantic_similarity, 4),
                    "missing_skills": missing_skills[:5],
                    "reasoning_summary": reasoning,
                }
            )

    candidate_df = pd.DataFrame(candidates)
    if candidate_df.empty:
        raise RuntimeError("No candidate roles could be generated")

    feasible_df = candidate_df[candidate_df["recommendation_score"] >= 0.10].copy()
    if feasible_df.empty:
        feasible_df = candidate_df.sort_values(["recommendation_score", "confidence"], ascending=False).head(top_k * 3)

    feasible_df = feasible_df.sort_values(["recommendation_score", "confidence"], ascending=False)

    # Rescale scores to a user-friendly display range (35%-90%)
    raw_min = feasible_df["recommendation_score"].min()
    raw_max = feasible_df["recommendation_score"].max()
    if raw_max > raw_min:
        feasible_df["recommendation_score"] = (
            0.35 + 0.55 * (feasible_df["recommendation_score"] - raw_min) / (raw_max - raw_min)
        ).round(4)
    else:
        feasible_df["recommendation_score"] = 0.60

    raw_cmin = feasible_df["confidence"].min()
    raw_cmax = feasible_df["confidence"].max()
    if raw_cmax > raw_cmin:
        feasible_df["confidence"] = (
            0.40 + 0.50 * (feasible_df["confidence"] - raw_cmin) / (raw_cmax - raw_cmin)
        ).round(4)
    else:
        feasible_df["confidence"] = 0.65

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
