"""
Scraper API endpoints
---------------------
Blueprint prefix: /api/scraper  (registered in app/__init__.py)

Endpoints:
    POST   /scrape          – Trigger a real-time Naukri.com scrape
    GET    /jobs             – List stored jobs (paginated + filterable)
    GET    /jobs/<job_id>    – Get a single job by ID
    DELETE /jobs             – Clear all stored jobs
    GET    /history          – List past scrape runs
    GET    /stats            – Quick counts
"""

from flask import Blueprint, jsonify, request

from app.services.scraper.scraper_service import run_scrape
from app.services.scraper.intelligence import update_skill_trends, update_ai_vulnerability
from app.services.scraper.store import (
    delete_all_jobs,
    get_all_jobs,
    get_job_by_id,
    get_scrape_history,
    get_stats,
)
from app.utils.responses import error_response, success_response

scraper_bp = Blueprint("scraper", __name__)


# ── Trigger scrape ────────────────────────────────────────

@scraper_bp.route("/scrape", methods=["POST"])
def scrape():
    """
    Start a real-time scrape of Naukri.com.

    Optional JSON body:
        {
            "keywords": ["developer", "analyst"],
            "location": "Mumbai",
            "max_rows": 50
        }
    """
    data = request.get_json(silent=True) or {}

    keywords = data.get("keywords")
    location = data.get("location")
    max_rows = data.get("max_rows")

    if keywords is not None:
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            return error_response("'keywords' must be a list of strings", 400)

    if max_rows is not None:
        try:
            max_rows = int(max_rows)
            if max_rows < 1:
                raise ValueError
        except (TypeError, ValueError):
            return error_response("'max_rows' must be a positive integer", 400)

    try:
        result = run_scrape(
            keywords=keywords,
            location=location,
            max_rows=max_rows,
        )
        return success_response(
            data={
                "run_id": result["run_id"],
                "keyword": result["keyword"],
                "jobs_added": result["jobs_added"],
                "total_jobs_in_store": result["total_jobs_in_store"],
                "sample_jobs": result["jobs"][:5],
            },
            message=f"Scrape complete – {result['jobs_added']} jobs added",
        )
    except Exception as exc:
        return error_response(f"Scrape failed: {exc}", 500)


# ── Unified: scrape + normalize + update intelligence ─────

@scraper_bp.route("/scrape-and-update", methods=["POST"])
def scrape_and_update():
    """
    Full pipeline: scrape Naukri → store in DB → update skill trends
    → update AI vulnerability scores.

    Optional JSON body (same as /scrape):
        {
            "keywords": ["developer", "analyst"],
            "location": "Mumbai",
            "max_rows": 50
        }
    """
    data = request.get_json(silent=True) or {}

    keywords = data.get("keywords")
    location = data.get("location")
    max_rows = data.get("max_rows")

    if keywords is not None:
        if not isinstance(keywords, list) or not all(isinstance(k, str) for k in keywords):
            return error_response("'keywords' must be a list of strings", 400)

    if max_rows is not None:
        try:
            max_rows = int(max_rows)
            if max_rows < 1:
                raise ValueError
        except (TypeError, ValueError):
            return error_response("'max_rows' must be a positive integer", 400)

    try:
        # Step 1: Scrape + normalize (run_scrape already calls normalize_and_store)
        result = run_scrape(
            keywords=keywords,
            location=location,
            max_rows=max_rows,
        )
        db_summary = result.get("db_summary", {})
        new_job_ids = db_summary.get("job_ids", [])

        # Step 2: Update skill trends for new jobs
        skill_result = {}
        if new_job_ids:
            skill_result = update_skill_trends(job_ids=new_job_ids)

        # Step 3: Update AI vulnerability scores for new jobs
        vuln_result = {}
        if new_job_ids:
            vuln_result = update_ai_vulnerability(job_ids=new_job_ids)

        return success_response(
            data={
                "run_id": result["run_id"],
                "jobs_scraped": result["jobs_added"],
                "jobs_stored": db_summary.get("jobs_created", 0),
                "cities_created": db_summary.get("cities_created", 0),
                "skill_trends_upserted": skill_result.get("skill_trends_upserted", 0),
                "vuln_scores_upserted": vuln_result.get("vuln_scores_upserted", 0),
                "sample_jobs": result["jobs"][:5],
            },
            message=(
                f"Pipeline complete – {result['jobs_added']} scraped, "
                f"{db_summary.get('jobs_created', 0)} stored, "
                f"{skill_result.get('skill_trends_upserted', 0)} skill trends updated, "
                f"{vuln_result.get('vuln_scores_upserted', 0)} vuln scores updated"
            ),
        )
    except Exception as exc:
        return error_response(f"Scrape pipeline failed: {exc}", 500)


# ── List / search jobs ────────────────────────────────────

@scraper_bp.route("/jobs", methods=["GET"])
def list_jobs():
    """
    Query params:
        page      (int, default 1)
        per_page  (int, default 20, max 100)
        keyword   (str, filters title + description)
        location  (str, filters location)
    """
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (TypeError, ValueError):
        per_page = 20

    keyword = request.args.get("keyword")
    location = request.args.get("location")

    result = get_all_jobs(
        page=page,
        per_page=per_page,
        keyword=keyword,
        location=location,
    )
    return success_response(data=result)


# ── Single job ────────────────────────────────────────────

@scraper_bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    job = get_job_by_id(job_id)
    if job is None:
        return error_response("Job not found", 404)
    return success_response(data=job)


# ── Delete all jobs ───────────────────────────────────────

@scraper_bp.route("/jobs", methods=["DELETE"])
def clear_jobs():
    count = delete_all_jobs()
    return success_response(message=f"Deleted {count} jobs")


# ── Scrape history ────────────────────────────────────────

@scraper_bp.route("/history", methods=["GET"])
def history():
    return success_response(data=get_scrape_history())


# ── Stats ─────────────────────────────────────────────────

@scraper_bp.route("/stats", methods=["GET"])
def stats():
    return success_response(data=get_stats())
