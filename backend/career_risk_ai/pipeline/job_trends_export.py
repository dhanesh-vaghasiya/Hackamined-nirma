from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd

from paths import csv_path, json_path, resolve_csv_input


def _job_trend_payload(df: pd.DataFrame) -> Dict[str, object]:
    if df.empty:
        return {"jobs": {}, "summary": {"rows": 0, "roles": 0}}

    base = df.copy()
    base["posted_date"] = pd.to_datetime(base["posted_date"], errors="coerce")
    base = base.dropna(subset=["posted_date", "job_title"])
    base["posted_month"] = base["posted_date"].dt.to_period("M").astype(str)

    grouped = (
        base.groupby(["job_title", "posted_month"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values(["job_title", "posted_month"])
    )

    jobs = {}
    for role, part in grouped.groupby("job_title"):
        points = [
            {"month": row["posted_month"], "count": int(row["count"])}
            for _, row in part.iterrows()
        ]

        first = points[0]["count"] if points else 0
        last = points[-1]["count"] if points else 0
        slope = (last - first) / (abs(first) + 1.0)

        jobs[role] = {
            "series": points,
            "trend_score": float(slope),
            "latest_count": int(last),
            "total_count": int(part["count"].sum()),
        }

    return {
        "jobs": jobs,
        "summary": {
            "rows": int(len(base)),
            "roles": int(len(jobs)),
            "months": sorted(base["posted_month"].unique().tolist()),
        },
    }


def _city_role_trend_payload(df: pd.DataFrame) -> Dict[str, object]:
    if df.empty:
        return {"city_roles": {}, "summary": {"rows": 0, "city_role_pairs": 0}}

    base = df.copy()
    base["posted_date"] = pd.to_datetime(base["posted_date"], errors="coerce")
    base = base.dropna(subset=["posted_date", "job_title", "location"])
    base["posted_month"] = base["posted_date"].dt.to_period("M").astype(str)

    grouped = (
        base.groupby(["location", "job_title", "posted_month"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values(["location", "job_title", "posted_month"])
    )

    city_roles = {}
    for (city, role), part in grouped.groupby(["location", "job_title"]):
        points = [
            {"month": row["posted_month"], "count": int(row["count"])}
            for _, row in part.iterrows()
        ]

        first = points[0]["count"] if points else 0
        last = points[-1]["count"] if points else 0
        slope = (last - first) / (abs(first) + 1.0)

        key = f"{role}||{city}"
        city_roles[key] = {
            "job_title": role,
            "location": city,
            "series": points,
            "trend_score": float(slope),
            "latest_count": int(last),
            "total_count": int(part["count"].sum()),
        }

    return {
        "city_roles": city_roles,
        "summary": {
            "rows": int(len(base)),
            "city_role_pairs": int(len(city_roles)),
            "months": sorted(base["posted_month"].unique().tolist()),
        },
    }


def _export_dashboard_city_role_metrics(jobs_df: pd.DataFrame) -> str:
    base = jobs_df.copy()
    base["posted_date"] = pd.to_datetime(base["posted_date"], errors="coerce")
    base = base.dropna(subset=["posted_date", "job_title", "location"])
    base["posted_month"] = base["posted_date"].dt.to_period("M").astype(str)

    monthly = (
        base.groupby(["location", "job_title", "posted_month"], as_index=False)
        .size()
        .rename(columns={"size": "demand"})
    )

    rows = []
    for (city, role), part in monthly.groupby(["location", "job_title"]):
        ordered = part.sort_values("posted_month")
        first = float(ordered.iloc[0]["demand"])
        last = float(ordered.iloc[-1]["demand"])
        trend_score = (last - first) / (abs(first) + 1.0)

        rows.append(
            {
                "job_title": role,
                "location": city,
                "latest_month": ordered.iloc[-1]["posted_month"],
                "latest_demand": int(last),
                "total_demand": int(ordered["demand"].sum()),
                "trend_score": float(trend_score),
            }
        )

    metrics = pd.DataFrame(rows)

    vuln_path = resolve_csv_input("job_ai_vulnerability.csv")
    if vuln_path.exists() and not metrics.empty:
        vuln = pd.read_csv(vuln_path)
        if "job_title_norm" not in vuln.columns:
            vuln["job_title_norm"] = vuln["job_title"].astype(str).str.lower().str.strip()

        metrics["job_title_norm"] = metrics["job_title"].astype(str).str.lower().str.strip()
        metrics = metrics.merge(
            vuln[["job_title_norm", "ai_vulnerability_score", "confidence", "reason"]],
            on="job_title_norm",
            how="left",
        )
        metrics = metrics.rename(
            columns={
                "ai_vulnerability_score": "role_ai_vulnerability_score",
                "confidence": "role_ai_vulnerability_confidence",
                "reason": "role_ai_vulnerability_reason",
            }
        )

    out_csv = csv_path("dashboard_job_city_metrics.csv")
    metrics.to_csv(out_csv, index=False)
    return str(out_csv)


def export_job_trends_json() -> Dict[str, object]:
    jobs_path = resolve_csv_input("jobs.csv")
    old_path = resolve_csv_input("old_scrappe_data.csv")
    out_path = json_path("job_trends.json")

    jobs_df = pd.read_csv(jobs_path)
    old_df = pd.read_csv(old_path)

    # Bring old dataset into common schema.
    old_norm = pd.DataFrame(
        {
            "job_title": old_df.get("job_title", pd.Series(dtype=str)),
            "posted_date": old_df.get("posting_date", pd.Series(dtype=str)),
        }
    )

    # Extract rows that came from recent scraper sources after merging.
    recent_df = jobs_df[jobs_df.get("source", "").astype(str).str.startswith("recent_scrapper:")].copy()

    payload = {
        "old_scrapped_data": _job_trend_payload(old_norm),
        "recent_scrapper_data": _job_trend_payload(recent_df[["job_title", "posted_date"]] if not recent_df.empty else pd.DataFrame(columns=["job_title", "posted_date"])),
        "combined_training_data": _job_trend_payload(jobs_df[["job_title", "posted_date"]]),
        "combined_city_role_trends": _city_role_trend_payload(jobs_df[["job_title", "location", "posted_date"]]),
    }

    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    dashboard_csv_path = _export_dashboard_city_role_metrics(jobs_df)

    return {
        "output_path": str(out_path),
        "dashboard_csv_path": dashboard_csv_path,
        "combined_roles": payload["combined_training_data"]["summary"]["roles"],
        "combined_rows": payload["combined_training_data"]["summary"]["rows"],
        "combined_city_role_pairs": payload["combined_city_role_trends"]["summary"]["city_role_pairs"],
    }


if __name__ == "__main__":
    info = export_job_trends_json()
    print(info)
