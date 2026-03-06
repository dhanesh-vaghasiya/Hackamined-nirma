from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

import numpy as np
import pandas as pd


SKILL_PATTERN = re.compile(r"Required skills:\s*(.*)$", re.IGNORECASE)


@dataclass
class RoleProfile:
    role: str
    skills: Set[str]
    text: str


def normalize_skill(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().lower())


def parse_required_skills(description: str) -> List[str]:
    text = str(description or "").strip()
    if not text:
        return []

    match = SKILL_PATTERN.search(text)
    payload = match.group(1) if match else text

    skills = [normalize_skill(part) for part in re.split(r"[,/|;]", payload)]
    return [s for s in skills if s and len(s) <= 40 and s not in {"n/a", "none", "nan"}]


def load_jobs_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["posted_date"] = pd.to_datetime(df["posted_date"], format="%Y-%m", errors="coerce")
    df["parsed_skills"] = df["description"].apply(parse_required_skills)
    return df.dropna(subset=["job_title", "location", "posted_date"]).copy()


def build_role_profiles(df: pd.DataFrame) -> Dict[str, RoleProfile]:
    profiles: Dict[str, RoleProfile] = {}

    for role, group in df.groupby("job_title"):
        skills: Set[str] = set()
        for values in group["parsed_skills"]:
            skills.update(values)

        # Keep only a compact text snapshot per role for embedding scalability.
        descriptions = " ".join(group["description"].astype(str).head(8).tolist())
        if len(descriptions) > 3000:
            descriptions = descriptions[:3000]
        text = f"{role}. {descriptions}".strip()
        profiles[role] = RoleProfile(role=role, skills=skills, text=text)

    return profiles


def build_city_role_stats(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["location", "job_title", "posted_date"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
        .sort_values(["location", "job_title", "posted_date"])
    )

    rows = []
    for (city, role), group in monthly.groupby(["location", "job_title"]):
        counts = group["count"].to_numpy(dtype=float)
        first = float(counts[0])
        last = float(counts[-1])
        trend = (last - first) / (abs(first) + 1.0)

        rows.append(
            {
                "city": city,
                "role": role,
                "total_demand": float(counts.sum()),
                "latest_demand": last,
                "trend": trend,
            }
        )

    stats = pd.DataFrame(rows)
    if stats.empty:
        return stats

    # Normalize demand scores to keep features model-friendly.
    stats["demand_score"] = stats["total_demand"] / (stats["total_demand"].max() + 1e-6)
    stats["latest_demand_score"] = stats["latest_demand"] / (stats["latest_demand"].max() + 1e-6)
    return stats


def role_skill_overlap(user_skills: Set[str], role_skills: Set[str]) -> Tuple[float, int, List[str]]:
    if not role_skills:
        return 0.0, 0, []

    overlap = user_skills.intersection(role_skills)
    overlap_ratio = len(overlap) / max(len(role_skills), 1)
    missing = sorted(role_skills.difference(user_skills))
    return overlap_ratio, len(missing), missing


def lookup_city_role_stats(stats_df: pd.DataFrame, city: str, role: str) -> Dict[str, float]:
    row = stats_df[(stats_df["city"] == city) & (stats_df["role"] == role)]
    if row.empty:
        return {
            "total_demand": 0.0,
            "latest_demand": 0.0,
            "trend": 0.0,
            "demand_score": 0.0,
            "latest_demand_score": 0.0,
        }

    data = row.iloc[0]
    return {
        "total_demand": float(data["total_demand"]),
        "latest_demand": float(data["latest_demand"]),
        "trend": float(data["trend"]),
        "demand_score": float(data["demand_score"]),
        "latest_demand_score": float(data["latest_demand_score"]),
    }


def risk_to_numeric(risk_level: str) -> float:
    mapping = {"LOW": 0.2, "MEDIUM": 0.6, "HIGH": 1.0}
    return mapping.get(str(risk_level).upper(), 0.6)


def safe_float(value: float) -> float:
    if np.isnan(value) or np.isinf(value):
        return 0.0
    return float(value)
