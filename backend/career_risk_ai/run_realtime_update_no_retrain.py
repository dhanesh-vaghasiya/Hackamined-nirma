from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from job_suggestion.recommend import recommend_next_roles
from pipeline.demand_dataset import build_demand_dataset
from pipeline.ai_vulnerability_index import build_or_update_ai_vulnerability_index
from pipeline.explainability import explain_prediction
from pipeline.feature_generator import generate_features
from pipeline.job_trends_export import export_job_trends_json
from pipeline.predict_risk import predict_risk
from pipeline.prepare_jobs_dataset import build_jobs_dataset_from_sources
from pipeline.trend_model import compute_trends
from paths import BACKEND_ROOT, WORKSPACE_ROOT, csv_path


def _resolve_scraper_backend_path() -> Path:
    candidates = [
        BACKEND_ROOT / "scrapper" / "backend",
        BACKEND_ROOT.parent / "scrapper" / "backend",
        WORKSPACE_ROOT / "scrapper" / "backend",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "Scraper backend not found in any expected location: "
        + ", ".join(str(p) for p in candidates)
    )


def _run_realtime_scrape(project_root: Path, keywords: list[str], location: str, max_rows: int) -> dict:
    backend_path = _resolve_scraper_backend_path()

    if str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))

    try:
        from app.services.scraper.scraper_service import run_scrape
    except Exception as exc:
        raise RuntimeError(
            "Failed to import scraper service. Install scraper deps first: "
            "selenium webdriver-manager beautifulsoup4 lxml"
        ) from exc

    result = run_scrape(keywords=keywords, location=location, max_rows=max_rows)
    jobs = result.get("jobs", [])
    if not jobs:
        raise RuntimeError("Scraper returned 0 jobs")

    df = pd.DataFrame(jobs)
    df["scraped_at"] = datetime.utcnow().isoformat()

    out_path = csv_path("recent_scrapper_data.csv")
    df.to_csv(out_path, index=False)

    return {
        "saved_csv": str(out_path),
        "scraped_jobs": int(len(df)),
        "run_id": result.get("run_id"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Realtime scrape + update trends + inference (no retraining)")
    parser.add_argument("--max-rows", type=int, default=150)
    parser.add_argument("--location", type=str, default="")
    parser.add_argument("--keywords", type=str, default="developer,analyst,engineer,designer,manager")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    keyword_list = [k.strip() for k in args.keywords.split(",") if k.strip()]

    user = {
        "normalized_job_title": "Junior Python Developer",
        "city": "Bhavnagar",
        "experience_years": 5,
        "skills": ["crm", "analytics", "data analysis"],
        "tasks": ["customer complaint resolution", "team supervision"],
    }

    print("1) Running realtime scraper...")
    scrape_info = _run_realtime_scrape(project_root, keyword_list, args.location, args.max_rows)
    print(json.dumps(scrape_info, indent=2))

    print("2) Rebuilding merged jobs dataset...")
    dataset_info = build_jobs_dataset_from_sources()
    print(json.dumps(dataset_info, indent=2))

    print("2.5) Updating AI vulnerability index for new roles (if GROQ_API_KEY is set)...")
    if os.getenv("GROQ_API_KEY", "").strip():
        vulnerability_info = build_or_update_ai_vulnerability_index()
        print(json.dumps(vulnerability_info, indent=2))
    else:
        print("Skipped: GROQ_API_KEY not set")

    print("3) Rebuilding demand + trends JSON (NO MODEL RETRAIN)...")
    build_demand_dataset()
    trends = compute_trends()
    trend_json_info = export_job_trends_json()
    print(json.dumps(trend_json_info, indent=2))

    print("4) Inference using existing trained models...")
    features = generate_features(user, trends)
    risk = predict_risk(features)
    explanation = explain_prediction(features)

    risk_result = {
        "risk_score": float(risk),
        "risk_level": "HIGH" if risk > 0.6 else "MEDIUM" if risk > 0.4 else "LOW",
        "features_used": features,
        "explainability": explanation,
    }
    print(risk_result)

    suggestion_user = {
        "current_role": user["normalized_job_title"],
        "city": user["city"],
        "skills": user["skills"],
        "experience_years": user["experience_years"],
        "risk_level": risk_result["risk_level"],
    }
    suggestions = recommend_next_roles(
        user_profile=suggestion_user,
        top_k=3,
        use_latest_market_data=True,
    )
    print(json.dumps(suggestions, indent=2))


if __name__ == "__main__":
    main()
