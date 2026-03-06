from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd

from paths import BACKEND_ROOT, PROJECT_ROOT, WORKSPACE_ROOT, csv_dir, csv_path


CANONICAL_COLUMNS = ["job_title", "description", "location", "posted_date", "source"]
EXCLUDED_GENERATED_CSV = {
    "jobs.csv",
    "skill_demand.csv",
    "job_ai_vulnerability.csv",
    "jobs_with_ai_vulnerability.csv",
    "dashboard_job_city_metrics.csv",
}


def _pick_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower_map = {c.lower().strip(): c for c in df.columns}
    for name in candidates:
        key = name.lower().strip()
        if key in lower_map:
            return lower_map[key]
    return None


def _normalize_date_to_month(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce", utc=False)
    month = dt.dt.to_period("M").astype(str)

    # Keep best-effort YYYY-MM regex fallback for non-standard strings.
    fallback = series.astype(str).str.extract(r"(\d{4}-\d{2})", expand=False)
    return month.where(month != "NaT", fallback)


def _normalize_frame(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    title_col = _pick_column(df, ["job_title", "title", "position", "role"])
    desc_col = _pick_column(df, ["description", "job_description", "summary", "skills"])
    loc_col = _pick_column(df, ["location", "city", "job_location", "place"])
    date_col = _pick_column(df, ["posted_date", "posting_date", "date_posted", "date", "scraped_at"])

    if not title_col or not loc_col or not date_col:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    out = pd.DataFrame()
    out["job_title"] = df[title_col].astype(str).str.strip()

    if desc_col:
        out["description"] = df[desc_col].astype(str).str.strip()
    else:
        # Preserve shape even when source lacks description.
        out["description"] = out["job_title"].map(lambda t: f"Hiring {t}")

    # Normalize noisy location strings like "Ahmedabad, Gujarat" -> "Ahmedabad".
    out["location"] = (
        df[loc_col]
        .astype(str)
        .str.split(",")
        .str[0]
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    out["posted_date"] = _normalize_date_to_month(df[date_col])
    out["source"] = source_name

    out = out.dropna(subset=["job_title", "location", "posted_date"])
    out = out[(out["job_title"] != "") & (out["location"] != "")]

    # Standardize month text strictly to YYYY-MM format.
    out["posted_date"] = out["posted_date"].astype(str).str.slice(0, 7)
    out = out[out["posted_date"].str.match(r"^\d{4}-\d{2}$", na=False)]

    return out[CANONICAL_COLUMNS]


def _discover_candidate_files(project_root: Path) -> List[Path]:
    data_dir = project_root / "data"
    shared_csv_dir = csv_dir()
    scraper_dirs = [
        BACKEND_ROOT / "scrapper",
        BACKEND_ROOT.parent / "scrapper",
        WORKSPACE_ROOT / "scrapper",
    ]

    candidates: List[Path] = []

    # Primary old scraped dataset.
    old_file = data_dir / "old_scrappe_data.csv"
    if old_file.exists():
        candidates.append(old_file)

    # Additional data files uploaded in data/.
    for p in data_dir.glob("*.csv"):
        if p.name in EXCLUDED_GENERATED_CSV | {"old_scrappe_data.csv"}:
            continue
        candidates.append(p)

    # Shared backend data location is preferred for all generated/required CSV files.
    if shared_csv_dir.exists():
        for p in shared_csv_dir.glob("*.csv"):
            if p.name in EXCLUDED_GENERATED_CSV:
                continue
            candidates.append(p)

    # Scraper-side exported files if any are present.
    for scraper_dir in scraper_dirs:
        if scraper_dir.exists():
            for p in scraper_dir.rglob("*.csv"):
                candidates.append(p)

    # Preserve order while de-duplicating.
    seen = set()
    unique: List[Path] = []
    for p in candidates:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique


def build_jobs_dataset_from_sources() -> Dict[str, object]:
    project_root = PROJECT_ROOT
    output_path = csv_path("jobs.csv")

    candidate_files = _discover_candidate_files(project_root)
    frames = []
    source_summary = []

    for path in candidate_files:
        try:
            raw = pd.read_csv(path)
        except Exception:
            source_summary.append({"source_file": str(path), "rows_read": 0, "rows_used": 0})
            continue

        source_name = "old_scrapped_data" if path.name == "old_scrappe_data.csv" else f"recent_scrapper:{path.stem}"
        normalized = _normalize_frame(raw, source_name=source_name)

        frames.append(normalized)
        source_summary.append(
            {
                "source_file": str(path),
                "rows_read": int(len(raw)),
                "rows_used": int(len(normalized)),
                "source_name": source_name,
            }
        )

    if not frames:
        raise RuntimeError("No valid source datasets were found to build jobs.csv")

    jobs = pd.concat(frames, ignore_index=True)
    jobs = jobs.drop_duplicates(subset=["job_title", "location", "posted_date", "description"])
    jobs = jobs.sort_values(["posted_date", "job_title", "location"]).reset_index(drop=True)

    jobs.to_csv(output_path, index=False)

    return {
        "output_path": str(output_path),
        "total_rows": int(len(jobs)),
        "sources": source_summary,
        "source_tags": jobs["source"].value_counts().to_dict(),
    }


if __name__ == "__main__":
    info = build_jobs_dataset_from_sources()
    print(info)
