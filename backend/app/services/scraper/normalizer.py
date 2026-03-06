"""
Normalizer – transforms raw scraped job data into normalized City/Job DB rows.

Handles:
  - Multi-city location splitting (one Job row per city)
  - Relative date resolution ("1 week ago" -> exact date)
  - City deduplication via get-or-create
  - Prefix stripping ("Hybrid - ", "Remote - ", etc.)
"""

import re
from datetime import date, datetime, timedelta

from app import db
from app.models import City, Job


# ── date normalization ─────────────────────────────────────

def normalize_date(raw: str, reference_date: date | None = None) -> date | None:
    """
    Convert a raw date string to a Python date.
    Supports: 'YYYY-MM-DD', 'X week(s) ago', 'X day(s) ago',
              'X month(s) ago', 'just now', 'today', 'yesterday'.
    """
    if not raw or raw.strip().upper() == "N/A":
        return None

    ref = reference_date or date.today()
    text = raw.strip().lower()

    # relative: weeks
    m = re.search(r"(\d+)\s*week", text)
    if m:
        return ref - timedelta(weeks=int(m.group(1)))

    # relative: days
    m = re.search(r"(\d+)\s*day", text)
    if m:
        return ref - timedelta(days=int(m.group(1)))

    # relative: months (approximate)
    m = re.search(r"(\d+)\s*month", text)
    if m:
        return ref - timedelta(days=int(m.group(1)) * 30)

    if any(w in text for w in ("just now", "today", "few hours", "hour ago", "hours ago")):
        return ref

    if "yesterday" in text:
        return ref - timedelta(days=1)

    # absolute formats
    for fmt in ("%Y-%m-%d", "%d %b %Y", "%b %d, %Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    return None


# ── location normalization ─────────────────────────────────

_LOCATION_PREFIXES = re.compile(
    r"^(hybrid\s*-\s*|remote\s*-\s*|work\s*from\s*home\s*-\s*)",
    re.IGNORECASE,
)

_PAREN_SUFFIX = re.compile(r"\s*\([^)]*\)\s*$")


def _clean_city_name(raw_city: str) -> str:
    """Strip prefixes, parenthetical notes, and whitespace from a single city token."""
    city = _LOCATION_PREFIXES.sub("", raw_city).strip()
    city = _PAREN_SUFFIX.sub("", city).strip()
    city = city.strip(" ,;-")
    return city


def split_cities(location_cell: str) -> list[str]:
    """
    Split a multi-city location string into distinct cleaned city names.
    E.g. "Hybrid - Pune, Chennai, Mumbai (All Areas)" -> ["Pune", "Chennai", "Mumbai"]
    """
    if not location_cell or location_cell.strip().upper() in ("N/A", ""):
        return []

    stripped = _LOCATION_PREFIXES.sub("", location_cell).strip()
    parts = stripped.split(",")

    cities: list[str] = []
    for part in parts:
        cleaned = _clean_city_name(part)
        if cleaned and cleaned.lower() not in ("india", "remote", "n/a", ""):
            cities.append(cleaned)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for c in cities:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return unique


# ── DB helpers ─────────────────────────────────────────────

def _get_or_create_city(city_name: str) -> City:
    """Return existing City row or create a new one."""
    normalized = city_name.strip().title()
    city = City.query.filter(db.func.lower(City.name) == normalized.lower()).first()
    if city is None:
        city = City(name=normalized)
        db.session.add(city)
        db.session.flush()
    return city


# ── main entry point ───────────────────────────────────────

def normalize_and_store(
    raw_jobs: list[dict],
    reference_date: date | None = None,
) -> dict:
    """
    Normalize a list of raw scraped job dicts and store into the DB.

    Each raw dict has keys: job_title, location, job_description, date_posted.
    Returns a summary dict with counts.
    """
    ref = reference_date or date.today()
    jobs_created = 0
    cities_created_count = 0
    rows_skipped = 0
    existing_cities_before = {c.name.lower() for c in City.query.all()}

    for raw in raw_jobs:
        title = (raw.get("job_title") or "").strip()
        location_raw = raw.get("location") or ""
        description = (raw.get("job_description") or "").strip() or None
        date_raw = raw.get("date_posted") or ""

        if not title:
            rows_skipped += 1
            continue

        posted_date = normalize_date(date_raw, ref)
        cities = split_cities(location_raw)

        if not cities:
            job = Job(
                title=title,
                city_id=None,
                description=description,
                posted_date=posted_date,
            )
            db.session.add(job)
            jobs_created += 1
            continue

        for city_name in cities:
            city = _get_or_create_city(city_name)
            if city.name.lower() not in existing_cities_before:
                cities_created_count += 1
                existing_cities_before.add(city.name.lower())

            job = Job(
                title=title,
                city_id=city.id,
                description=description,
                posted_date=posted_date,
            )
            db.session.add(job)
            jobs_created += 1

    db.session.commit()

    return {
        "jobs_created": jobs_created,
        "cities_created": cities_created_count,
        "rows_skipped": rows_skipped,
        "raw_rows_processed": len(raw_jobs),
    }


def normalize_and_store_csv(csv_path: str, reference_date: date | None = None) -> dict:
    """
    Read a raw scraper CSV and normalize + store all rows.
    CSV columns: job_title, location, job_description, date_posted
    """
    import csv

    raw_jobs: list[dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_jobs.append({
                "job_title": row.get("job_title", ""),
                "location": row.get("location", ""),
                "job_description": row.get("job_description", ""),
                "date_posted": row.get("date_posted", ""),
            })

    return normalize_and_store(raw_jobs, reference_date)
