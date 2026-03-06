"""
In-memory job store – simulates a database for scraped jobs.
Provides CRUD helpers used by the route layer.
"""

import threading
import uuid
from datetime import datetime

_lock = threading.Lock()
_jobs: dict[str, dict] = {}          # id -> job dict
_scrape_runs: list[dict] = []        # history of scrape invocations


def _next_id() -> str:
    return uuid.uuid4().hex[:12]


# ── write helpers ──────────────────────────────────────────

def save_jobs(jobs: list[dict], keyword: str | None = None) -> dict:
    """Persist a batch of scraped jobs. Returns a run summary."""
    run_id = _next_id()
    added = 0
    with _lock:
        for job in jobs:
            job_id = _next_id()
            record = {
                "id": job_id,
                "job_title": job.get("job_title", "N/A"),
                "location": job.get("location", "N/A"),
                "job_description": job.get("job_description", "N/A"),
                "date_posted": job.get("date_posted", "N/A"),
                "scraped_at": datetime.utcnow().isoformat(),
                "run_id": run_id,
                "keyword": keyword,
            }
            _jobs[job_id] = record
            added += 1

        run_summary = {
            "run_id": run_id,
            "keyword": keyword,
            "jobs_added": added,
            "total_jobs_in_store": len(_jobs),
            "timestamp": datetime.utcnow().isoformat(),
        }
        _scrape_runs.append(run_summary)

    return run_summary


# ── read helpers ───────────────────────────────────────────

def get_all_jobs(
    page: int = 1,
    per_page: int = 20,
    keyword: str | None = None,
    location: str | None = None,
) -> dict:
    """Return paginated + filtered jobs from the store."""
    with _lock:
        items = list(_jobs.values())

    # optional filters
    if keyword:
        kw = keyword.lower()
        items = [
            j for j in items
            if kw in j["job_title"].lower() or kw in j["job_description"].lower()
        ]
    if location:
        loc = location.lower()
        items = [j for j in items if loc in j["location"].lower()]

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = items[start:end]

    return {
        "jobs": page_items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page if per_page else 0,
    }


def get_job_by_id(job_id: str) -> dict | None:
    with _lock:
        return _jobs.get(job_id)


def delete_all_jobs() -> int:
    """Clear the store. Returns count of removed jobs."""
    with _lock:
        count = len(_jobs)
        _jobs.clear()
        return count


def get_scrape_history() -> list[dict]:
    with _lock:
        return list(_scrape_runs)


def get_stats() -> dict:
    with _lock:
        return {
            "total_jobs": len(_jobs),
            "total_scrape_runs": len(_scrape_runs),
        }
