from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd

from job_suggestion.data_utils import (
    build_city_role_stats,
    build_role_profiles,
    load_jobs_dataset,
    lookup_city_role_stats,
    role_skill_overlap,
)
from job_suggestion.models import RoleEmbedder, build_ranker, build_transition_classifier, cosine_similarity_matrix
from paths import model_path, resolve_csv_input

FEATURE_COLUMNS = [
    "semantic_similarity",
    "skill_overlap_ratio",
    "skill_gap_count",
    "candidate_demand_score",
    "candidate_latest_demand_score",
    "candidate_trend",
    "demand_lift_vs_current",
    "trend_lift_vs_current",
    "city_switch",
]


def _build_training_rows(
    roles: List[str],
    cities: List[str],
    fallback_cities: List[str],
    role_profiles: Dict[str, object],
    city_role_stats: pd.DataFrame,
    sim_matrix: np.ndarray,
    role_index: Dict[str, int],
) -> pd.DataFrame:
    rows = []

    for current_role in roles:
        for candidate_role in roles:
            if current_role == candidate_role:
                continue

            current_skills = role_profiles[current_role].skills
            candidate_skills = role_profiles[candidate_role].skills
            overlap_ratio, gap_count, _ = role_skill_overlap(current_skills, candidate_skills)
            semantic_similarity = float(
                sim_matrix[role_index[current_role], role_index[candidate_role]]
            )

            for current_city in cities:
                current_city_stats = lookup_city_role_stats(city_role_stats, current_city, current_role)

                candidate_city_pool = [current_city] + [c for c in fallback_cities if c != current_city]
                for candidate_city in candidate_city_pool:
                    candidate_city_stats = lookup_city_role_stats(city_role_stats, candidate_city, candidate_role)
                    city_switch = 1.0 if candidate_city != current_city else 0.0

                    demand_lift = (
                        candidate_city_stats["demand_score"] - current_city_stats["demand_score"]
                    )
                    trend_lift = (
                        candidate_city_stats["trend"] - current_city_stats["trend"]
                    )

                    # Weak supervision score for realistic next-step transitions.
                    feasible_signal = (
                        0.55 * max(semantic_similarity, 0.0)
                        + 0.35 * overlap_ratio
                        - 0.08 * float(gap_count)
                        - 0.10 * city_switch
                    )
                    feasible_label = int(feasible_signal >= 0.05)

                    target_score = (
                        0.32 * semantic_similarity
                        + 0.26 * overlap_ratio
                        + 0.22 * candidate_city_stats["demand_score"]
                        + 0.10 * candidate_city_stats["latest_demand_score"]
                        + 0.10 * candidate_city_stats["trend"]
                        + 0.15 * demand_lift
                        + 0.12 * trend_lift
                        - 0.06 * gap_count
                        - 0.12 * city_switch
                    )
                    if feasible_label:
                        target_score += 0.20

                    rows.append(
                        {
                            "current_role": current_role,
                            "candidate_role": candidate_role,
                            "current_city": current_city,
                            "candidate_city": candidate_city,
                            "semantic_similarity": semantic_similarity,
                            "skill_overlap_ratio": overlap_ratio,
                            "skill_gap_count": float(gap_count),
                            "candidate_demand_score": candidate_city_stats["demand_score"],
                            "candidate_latest_demand_score": candidate_city_stats["latest_demand_score"],
                            "candidate_trend": candidate_city_stats["trend"],
                            "demand_lift_vs_current": demand_lift,
                            "trend_lift_vs_current": trend_lift,
                            "city_switch": city_switch,
                            "feasible_label": feasible_label,
                            "target_score": target_score,
                        }
                    )

    return pd.DataFrame(rows)


def train_job_suggestion_models(
    jobs_csv_path: str | None = None,
    model_output_dir: str | None = None,
    max_roles: int = 60,
    max_cities: int = 12,
    fallback_city_count: int = 4,
    random_state: int = 42,
) -> Dict[str, str]:
    jobs_path = Path(jobs_csv_path) if jobs_csv_path else resolve_csv_input("jobs.csv")
    output_dir = Path(model_output_dir) if model_output_dir else model_path("job_suggestion")
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs_df = load_jobs_dataset(str(jobs_path))
    # Restrict to high-signal roles for tractable pairwise training on very large datasets.
    top_roles = (
        jobs_df["job_title"].value_counts().head(max_roles).index.tolist()
        if max_roles and max_roles > 0
        else jobs_df["job_title"].value_counts().index.tolist()
    )
    jobs_df = jobs_df[jobs_df["job_title"].isin(top_roles)].copy()

    role_profiles = build_role_profiles(jobs_df)
    city_role_stats = build_city_role_stats(jobs_df)

    roles = sorted(role_profiles.keys())
    city_counts = jobs_df["location"].value_counts()
    cities = city_counts.head(max_cities).index.tolist() if max_cities > 0 else city_counts.index.tolist()
    jobs_df = jobs_df[jobs_df["location"].isin(cities)].copy()
    fallback_cities = cities[:fallback_city_count]

    role_texts = [role_profiles[r].text for r in roles]
    embedder = RoleEmbedder()
    embedder.fit(role_texts)
    role_vectors = embedder.encode(role_texts)

    role_index = {role: idx for idx, role in enumerate(roles)}
    sim_matrix = cosine_similarity_matrix(role_vectors, role_vectors)

    train_df = _build_training_rows(
        roles=roles,
        cities=cities,
        fallback_cities=fallback_cities,
        role_profiles=role_profiles,
        city_role_stats=city_role_stats,
        sim_matrix=sim_matrix,
        role_index=role_index,
    )

    x = train_df[FEATURE_COLUMNS]
    y_feasible = train_df["feasible_label"]
    y_score = train_df["target_score"]

    transition_model, transition_model_name = build_transition_classifier(random_state=random_state)
    transition_model.fit(x, y_feasible)

    rank_model, rank_model_name = build_ranker(random_state=random_state)
    rank_model.fit(x, y_score)

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "embedding_model": embedder.backend.name if embedder.backend else "unknown",
        "transition_model": transition_model_name,
        "rank_model": rank_model_name,
    }

    artifact = {
        "metadata": metadata,
        "roles": roles,
        "cities": cities,
        "role_profiles": {
            role: {
                "skills": sorted(list(role_profiles[role].skills)),
                "text": role_profiles[role].text,
            }
            for role in roles
        },
        "city_role_stats": city_role_stats,
        "role_vectors": role_vectors,
        "embedder": embedder,
        "transition_model": transition_model,
        "rank_model": rank_model,
    }

    model_path = output_dir / "job_suggestion_models.pkl"
    joblib.dump(artifact, model_path)

    return {
        "model_path": str(model_path),
        "embedding_model": metadata["embedding_model"],
        "transition_model": metadata["transition_model"],
        "rank_model": metadata["rank_model"],
        "roles_used": str(len(roles)),
        "cities_used": str(len(cities)),
        "training_rows": str(len(train_df)),
    }


if __name__ == "__main__":
    info = train_job_suggestion_models()
    print(info)
