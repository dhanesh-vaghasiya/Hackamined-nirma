from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd

from paths import json_path, resolve_csv_input


def analyze_jobs_data(jobs_csv_path: Path) -> Dict[str, object]:
    df = pd.read_csv(jobs_csv_path)

    total_rows = int(len(df))
    if total_rows == 0:
        raise RuntimeError("jobs.csv is empty after merge")

    missing = {
        c: float(df[c].isna().mean()) if c in df.columns else 1.0
        for c in ["job_title", "description", "location", "posted_date"]
    }

    role_counts = df["job_title"].astype(str).value_counts()
    city_counts = df["location"].astype(str).value_counts()

    unique_roles = int(role_counts.shape[0])
    unique_cities = int(city_counts.shape[0])

    if total_rows >= 120_000:
        sug_max_roles, sug_max_cities, sug_fallback_cities = 45, 10, 4
        risk_max_roles, risk_max_cities = 80, 15
    elif total_rows >= 60_000:
        sug_max_roles, sug_max_cities, sug_fallback_cities = 60, 12, 4
        risk_max_roles, risk_max_cities = 120, 20
    else:
        sug_max_roles, sug_max_cities, sug_fallback_cities = 80, 15, 5
        risk_max_roles, risk_max_cities = 180, 25

    sug_max_roles = min(sug_max_roles, unique_roles)
    sug_max_cities = min(sug_max_cities, unique_cities)
    sug_fallback_cities = min(sug_fallback_cities, sug_max_cities)
    risk_max_roles = min(risk_max_roles, unique_roles)
    risk_max_cities = min(risk_max_cities, unique_cities)

    return {
        "rows": total_rows,
        "unique_roles": unique_roles,
        "unique_cities": unique_cities,
        "missing_ratio": missing,
        "top_roles": role_counts.head(10).to_dict(),
        "top_cities": city_counts.head(10).to_dict(),
        "recommended": {
            "risk": {
                "max_roles": int(risk_max_roles),
                "max_cities": int(risk_max_cities),
            },
            "job_suggestion": {
                "max_roles": int(sug_max_roles),
                "max_cities": int(sug_max_cities),
                "fallback_city_count": int(sug_fallback_cities),
            },
        },
    }


def run_preflight() -> Dict[str, object]:
    jobs_path = resolve_csv_input("jobs.csv")
    out_path = json_path("training_preflight.json")

    summary = analyze_jobs_data(jobs_path)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"summary": summary, "output_path": str(out_path)}


if __name__ == "__main__":
    result = run_preflight()
    print(json.dumps(result, indent=2))
