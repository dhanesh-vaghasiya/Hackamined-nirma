from pathlib import Path
import re

import pandas as pd

from paths import csv_path, resolve_csv_input

SKILL_SPLIT_RE = re.compile(r"[,/|;]\s*")


def _fast_extract_skills(text: str):
    value = str(text or "").strip()
    if not value:
        return []

    lowered = value.lower()
    marker = "required skills:"
    if marker in lowered:
        idx = lowered.find(marker)
        value = value[idx + len(marker):]

    skills = []
    for token in SKILL_SPLIT_RE.split(value):
        candidate = re.sub(r"\s+", " ", token.strip().lower())
        if not candidate:
            continue
        if len(candidate) > 40:
            continue
        if candidate in {"n/a", "nan", "none"}:
            continue
        skills.append(candidate)

    # Keep unique order.
    seen = set()
    uniq = []
    for s in skills:
        if s not in seen:
            uniq.append(s)
            seen.add(s)
    return uniq[:20]

def build_demand_dataset():
    input_path = resolve_csv_input("jobs.csv")
    output_path = csv_path("skill_demand.csv")

    df = pd.read_csv(input_path)

    df["description"] = df["description"].fillna("").astype(str)
    df["skills"] = df["description"].apply(_fast_extract_skills)

    df = df.explode("skills")
    df = df.dropna(subset=["skills"])
    df = df[df["skills"].astype(str).str.len() > 0]

    demand = (
        df.groupby(["posted_date","location","skills"])
        .size()
        .reset_index(name="demand")
    )

    demand.to_csv(output_path, index=False)

    print("Skill demand dataset created")


if __name__ == "__main__":
    build_demand_dataset()