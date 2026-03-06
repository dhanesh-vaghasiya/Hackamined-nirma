from pathlib import Path

import pandas as pd

from paths import resolve_csv_input


def compute_trends(horizon_months=1):
    """Compute normalized skill demand trends from monthly demand history."""
    demand_path = resolve_csv_input("skill_demand.csv")

    df = pd.read_csv(demand_path)
    df = (
        df.groupby(["posted_date", "skills"], as_index=False)["demand"]
        .sum()
        .sort_values(["skills", "posted_date"])
    )
    df["posted_date"] = pd.to_datetime(df["posted_date"], format="%Y-%m", errors="coerce")
    df = df.dropna(subset=["posted_date", "skills", "demand"])

    trends = {}

    for skill, group in df.groupby("skills"):
        ts = group.sort_values("posted_date")["demand"].astype(float).to_numpy()
        if len(ts) < 2:
            trends[skill] = 0.0
            continue

        # Use recent window growth for stable and fast trend scoring.
        first = float(ts[max(0, len(ts) - 4)])
        last = float(ts[-1])
        trends[skill] = (last - first) / (abs(first) + 1.0)

    return trends