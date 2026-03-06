from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor

from paths import model_path, resolve_csv_input

def train_model(max_roles: int = 120, max_cities: int = 20):
    jobs_path = resolve_csv_input("jobs.csv")
    demand_path = resolve_csv_input("skill_demand.csv")

    jobs = pd.read_csv(jobs_path)
    demand = pd.read_csv(demand_path)

    if jobs.empty or demand.empty:
        raise RuntimeError("jobs.csv and skill_demand.csv must contain data for risk training")

    # Keep training volume stable on very large scraped datasets.
    top_roles = jobs["job_title"].astype(str).value_counts().head(max_roles).index.tolist()
    top_cities = jobs["location"].astype(str).value_counts().head(max_cities).index.tolist()
    jobs = jobs[jobs["job_title"].astype(str).isin(top_roles)].copy()
    jobs = jobs[jobs["location"].astype(str).isin(top_cities)].copy()

    # Build market trend lookup from latest skill demand deltas.
    demand["posted_date"] = pd.to_datetime(demand["posted_date"], errors="coerce")
    demand = demand.dropna(subset=["posted_date", "skills", "demand"]).copy()

    trend_lookup = {}
    for skill, part in demand.groupby("skills"):
        series = part.sort_values("posted_date")["demand"].astype(float).to_numpy()
        if len(series) < 2:
            trend_lookup[str(skill).lower()] = 0.0
            continue
        trend_lookup[str(skill).lower()] = float((series[-1] - series[0]) / (abs(series[0]) + 1.0))

    jobs["location"] = jobs["location"].astype(str)
    total_jobs = max(len(jobs), 1)

    # Infer role-level skill lists from descriptions.
    role_skills = {}
    for role, part in jobs.groupby("job_title"):
        skills = set()
        for desc in part["description"].astype(str):
            text = desc
            if "Required skills:" in text:
                text = text.split("Required skills:", 1)[1]

            # Best-effort extraction from comma-delimited scraped descriptions.
            for s in text.replace("|", ",").split(","):
                value = s.strip().lower()
                if value and len(value) <= 40:
                    skills.add(value)
        role_skills[str(role)] = sorted(skills)

    X_rows = []
    y_rows = []

    role_city_counts = (
        jobs.groupby(["job_title", "location"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    role_city_map = {
        role: list(zip(part["location"].tolist(), part["count"].tolist()))
        for role, part in role_city_counts.groupby("job_title")
    }

    for role, skills in role_skills.items():
        if not skills:
            continue

        role_counts = role_city_map.get(role, [])
        if not role_counts:
            continue

        for _, count_value in role_counts:
            count = int(count_value)
            avg_trend = float(np.mean([trend_lookup.get(s, 0.0) for s in skills]))
            location_score = float(count / total_jobs)

            # Weak supervision from market signals: low trend + low location demand = higher risk.
            automation_risk = float(
                0.75 if any(s in {"data entry", "copy paste"} for s in skills)
                else 0.55 if any(s in {"support", "customer support"} for s in skills)
                else 0.30
            )

            # Use multiple experience buckets so model learns shape of experience effect.
            for experience_years in (1, 3, 5, 8, 12):
                feature_row = [
                    avg_trend,
                    location_score,
                    automation_risk,
                    float(experience_years),
                ]

                risk_target = (
                    0.42 * (1.0 - avg_trend)
                    + 0.30 * (1.0 - location_score)
                    + 0.20 * automation_risk
                    + 0.08 * (1.0 / (experience_years + 1.0))
                )

                X_rows.append(feature_row)
                y_rows.append(float(np.clip(risk_target, 0.0, 1.0)))

    X = np.asarray(X_rows, dtype=float)
    y = np.asarray(y_rows, dtype=float)

    model = RandomForestRegressor(random_state=42)
    model.fit(X, y)

    risk_model_path = model_path("risk_model.pkl")
    risk_model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, risk_model_path)

    print(
        f"Risk model trained on {len(X_rows)} real-data-derived samples "
        f"(roles={len(top_roles)}, cities={len(top_cities)})"
    )