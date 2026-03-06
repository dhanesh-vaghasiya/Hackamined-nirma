"""
seed_data.py – Clean, comprehensive data seeder for OASIS platform.

Reads every CSV & JSON file in data/, normalises the values, deduplicates
on unique-constraint keys, and inserts into the database via SQLAlchemy.

Tables seeded (in FK-safe order):
    1. cities
    2. courses
    3. jobs               ← jobs.csv + old_scrappe_data.csv + recent_scrapper_data.csv
    4. job_skills          ← skills extracted from skill_demand.csv per-job linkage
    5. ai_vulnerability_scores ← job_ai_vulnerability.csv + dashboard_job_city_metrics.csv
    6. skill_trends        ← skill_demand.csv + skill_market_2020_present.json

Usage
─────
    cd backend
    source .venv/bin/activate
    python seed_data.py              # seed into existing tables
    python seed_data.py --reset      # DROP + recreate all tables first
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

# ── ensure backend root is on sys.path ──────────────────────────────
BACKEND_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app, db
from app.models import (
    AiVulnerabilityScore,
    City,
    Course,
    Job,
    JobSkill,
    SkillTrend,
)

# ── paths ────────────────────────────────────────────────────────────
CSV_DIR  = BACKEND_ROOT / "data" / "csv"
JSON_DIR = BACKEND_ROOT / "data" / "json"

# ── limits (tune down for dev, remove for prod) ─────────────────────
MAX_JOBS   = 200_000      # across all CSV sources
MAX_VULN   = 100_000
MAX_TRENDS = 300_000
BATCH_SIZE = 5_000        # flush every N rows

# =====================================================================
# STATIC DATA
# =====================================================================

CITY_DATA: list[tuple[str, str, int]] = [
    # Tier-1
    ("Bengaluru",   "Karnataka",       1),
    ("Mumbai",      "Maharashtra",     1),
    ("Delhi NCR",   "Delhi",           1),
    ("Hyderabad",   "Telangana",       1),
    ("Pune",        "Maharashtra",     1),
    ("Chennai",     "Tamil Nadu",      1),
    ("Kolkata",     "West Bengal",     1),
    ("Ahmedabad",   "Gujarat",         1),
    # Tier-2
    ("Jaipur",      "Rajasthan",       2),
    ("Indore",      "Madhya Pradesh",  2),
    ("Lucknow",     "Uttar Pradesh",   2),
    ("Bhopal",      "Madhya Pradesh",  2),
    ("Surat",       "Gujarat",         2),
    ("Nagpur",      "Maharashtra",     2),
    ("Coimbatore",  "Tamil Nadu",      2),
    ("Kochi",       "Kerala",          2),
    ("Chandigarh",  "Chandigarh",      2),
    ("Patna",       "Bihar",           2),
    ("Noida",       "Uttar Pradesh",   2),
    ("Gurgaon",     "Haryana",         2),
    ("Thiruvananthapuram", "Kerala",   2),
    ("Visakhapatnam", "Andhra Pradesh", 2),
    ("Vadodara",    "Gujarat",         2),
    ("Mysuru",      "Karnataka",       2),
    # Tier-3
    ("Ranchi",      "Jharkhand",       3),
    ("Dehradun",    "Uttarakhand",     3),
    ("Raipur",      "Chhattisgarh",    3),
    ("Guwahati",    "Assam",           3),
    ("Jodhpur",     "Rajasthan",       3),
    ("Vijayawada",  "Andhra Pradesh",  3),
]

# Alternate / misspelled city names → canonical name
CITY_ALIASES: dict[str, str] = {
    "bangalore":     "Bengaluru",
    "bengaluru":     "Bengaluru",
    "banglore":      "Bengaluru",
    "bombay":        "Mumbai",
    "mumbai":        "Mumbai",
    "new delhi":     "Delhi NCR",
    "delhi":         "Delhi NCR",
    "delhi ncr":     "Delhi NCR",
    "gurgaon":       "Gurgaon",
    "gurugram":      "Gurgaon",
    "noida":         "Noida",
    "greater noida": "Noida",
    "pune":          "Pune",
    "hyderabad":     "Hyderabad",
    "chennai":       "Chennai",
    "kolkata":       "Kolkata",
    "calcutta":      "Kolkata",
    "ahmedabad":     "Ahmedabad",
    "jaipur":        "Jaipur",
    "indore":        "Indore",
    "lucknow":       "Lucknow",
    "bhopal":        "Bhopal",
    "surat":         "Surat",
    "nagpur":        "Nagpur",
    "coimbatore":    "Coimbatore",
    "kochi":         "Kochi",
    "cochin":        "Kochi",
    "chandigarh":    "Chandigarh",
    "patna":         "Patna",
    "thiruvananthapuram": "Thiruvananthapuram",
    "trivandrum":    "Thiruvananthapuram",
    "visakhapatnam": "Visakhapatnam",
    "vizag":         "Visakhapatnam",
    "vadodara":      "Vadodara",
    "baroda":        "Vadodara",
    "mysuru":        "Mysuru",
    "mysore":        "Mysuru",
    "ranchi":        "Ranchi",
    "dehradun":      "Dehradun",
    "raipur":        "Raipur",
    "guwahati":      "Guwahati",
    "jodhpur":       "Jodhpur",
    "vijayawada":    "Vijayawada",
}

COURSES_DATA: list[dict] = [
    # ─── NPTEL ───
    dict(title="Data Science for Engineers", provider="NPTEL", institution="IIT Madras",
         url="https://nptel.ac.in/courses/106106179", duration_weeks=8, is_free=True,
         skills_covered=["data analysis","python","statistics","machine learning"],
         description="Comprehensive data science course covering Python, statistics, and ML fundamentals."),
    dict(title="Programming in Python", provider="NPTEL", institution="IIT Madras",
         url="https://nptel.ac.in/courses/106106182", duration_weeks=8, is_free=True,
         skills_covered=["python","programming","software development"],
         description="Learn Python programming from basics to advanced concepts."),
    dict(title="Deep Learning", provider="NPTEL", institution="IIT Madras",
         url="https://nptel.ac.in/courses/106106184", duration_weeks=12, is_free=True,
         skills_covered=["deep learning","neural networks","AI","python"],
         description="Advanced deep learning course covering CNNs, RNNs, and Transformers."),
    dict(title="Database Management System", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/106105175", duration_weeks=8, is_free=True,
         skills_covered=["sql","database","data management"],
         description="Core DBMS concepts including SQL, normalization, and transaction processing."),
    dict(title="Cloud Computing", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/106105167", duration_weeks=8, is_free=True,
         skills_covered=["cloud computing","AWS","DevOps"],
         description="Fundamentals of cloud computing, virtualization, and distributed systems."),
    dict(title="Introduction to Machine Learning", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/106105152", duration_weeks=8, is_free=True,
         skills_covered=["machine learning","AI","python","statistics"],
         description="ML fundamentals: regression, classification, clustering, and evaluation."),
    dict(title="Artificial Intelligence", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/106105077", duration_weeks=12, is_free=True,
         skills_covered=["AI","search algorithms","knowledge representation"],
         description="Core AI concepts including search, logic, and planning."),
    dict(title="Cyber Security", provider="NPTEL", institution="IIT Madras",
         url="https://nptel.ac.in/courses/106106178", duration_weeks=8, is_free=True,
         skills_covered=["cybersecurity","network security","encryption"],
         description="Cybersecurity fundamentals, cryptography, and network security."),
    dict(title="Introduction to Internet of Things", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/106105166", duration_weeks=8, is_free=True,
         skills_covered=["IoT","embedded systems","sensors","networking"],
         description="IoT ecosystems including sensors, networking, and cloud integration."),
    dict(title="Business Analytics", provider="NPTEL", institution="IIT Kharagpur",
         url="https://nptel.ac.in/courses/110105089", duration_weeks=8, is_free=True,
         skills_covered=["business analytics","data analysis","excel","statistics"],
         description="Analytics using statistical methods and business intelligence tools."),
    # ─── SWAYAM ───
    dict(title="AI for Everyone", provider="SWAYAM", institution="IGNOU",
         url="https://swayam.gov.in/courses/ai-for-everyone", duration_weeks=6, is_free=True,
         skills_covered=["AI","machine learning","digital literacy"],
         description="Non-technical introduction to AI concepts and applications."),
    dict(title="Digital Marketing", provider="SWAYAM", institution="IIM Bangalore",
         url="https://swayam.gov.in/courses/digital-marketing", duration_weeks=8, is_free=True,
         skills_covered=["digital marketing","SEO","social media","content marketing"],
         description="Complete digital marketing: SEO, SEM, social media, and analytics."),
    dict(title="Communication Skills", provider="SWAYAM", institution="CEC",
         url="https://swayam.gov.in/courses/communication-skills", duration_weeks=4, is_free=True,
         skills_covered=["communication","presentation","soft skills","english"],
         description="Effective workplace communication and presentation skills."),
    dict(title="Data Analytics with Python", provider="SWAYAM", institution="IIT Roorkee",
         url="https://swayam.gov.in/courses/data-analytics-python", duration_weeks=8, is_free=True,
         skills_covered=["python","data analysis","pandas","visualization"],
         description="Hands-on data analytics using Python, Pandas, and Matplotlib."),
    dict(title="Web Development", provider="SWAYAM", institution="CEC",
         url="https://swayam.gov.in/courses/web-development", duration_weeks=8, is_free=True,
         skills_covered=["html","css","javascript","web development"],
         description="Full-stack web development from HTML/CSS to JavaScript frameworks."),
    dict(title="Financial Accounting", provider="SWAYAM", institution="IGNOU",
         url="https://swayam.gov.in/courses/financial-accounting", duration_weeks=6, is_free=True,
         skills_covered=["accounting","finance","bookkeeping","excel"],
         description="Fundamentals of financial accounting and reporting."),
    dict(title="Project Management", provider="SWAYAM", institution="IIM Bangalore",
         url="https://swayam.gov.in/courses/project-management", duration_weeks=6, is_free=True,
         skills_covered=["project management","agile","scrum","leadership"],
         description="Project management methodologies including Agile and Waterfall."),
    dict(title="Entrepreneurship", provider="SWAYAM", institution="IIM Ahmedabad",
         url="https://swayam.gov.in/courses/entrepreneurship", duration_weeks=8, is_free=True,
         skills_covered=["entrepreneurship","business plan","strategy","leadership"],
         description="Starting and managing a new venture, market analysis and fundraising."),
    # ─── PMKVY ───
    dict(title="Domestic Data Entry Operator", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/domestic-data-entry", duration_weeks=4, is_free=True,
         skills_covered=["data entry","typing","MS Office","excel"],
         description="Certified data entry operations with computer fundamentals."),
    dict(title="CRM Domestic Non-Voice", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/crm-domestic", duration_weeks=4, is_free=True,
         skills_covered=["customer service","CRM","communication","problem solving"],
         description="Customer relationship management for non-voice processes."),
    dict(title="AI & Machine Learning Technician", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/ai-ml-technician", duration_weeks=6, is_free=True,
         skills_covered=["AI","machine learning","python","data processing"],
         description="Entry-level AI/ML skills for technology support roles."),
    dict(title="Solar Panel Installation Technician", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/solar-panel", duration_weeks=3, is_free=True,
         skills_covered=["solar energy","installation","electrical","renewable energy"],
         description="Hands-on solar panel installation and maintenance."),
    dict(title="Medical Records Technician", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/medical-records", duration_weeks=4, is_free=True,
         skills_covered=["medical records","healthcare","data management","documentation"],
         description="Managing medical records and healthcare documentation."),
    dict(title="Retail Sales Associate", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/retail-sales", duration_weeks=3, is_free=True,
         skills_covered=["retail","sales","customer service","inventory"],
         description="Professional retail sales and customer engagement skills."),
    dict(title="Beauty Therapist", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/beauty-therapist", duration_weeks=4, is_free=True,
         skills_covered=["beauty","skincare","customer service","wellness"],
         description="Professional beauty therapy and wellness services."),
    dict(title="Digital Marketing Executive", provider="PMKVY", institution="NSDC",
         url="https://pmkvyofficial.org/courses/digital-marketing", duration_weeks=4, is_free=True,
         skills_covered=["digital marketing","social media","SEO","content creation"],
         description="Certified digital marketing skills for employment."),
]


# =====================================================================
# HELPERS  — normalisation, parsing, cleaning
# =====================================================================

def normalize_title(raw: str) -> str:
    """Lowercase, strip special chars, collapse whitespace."""
    t = raw.strip().lower()
    t = re.sub(r"[^a-z0-9\s/+#.\-]", " ", t)   # keep /, +, #, ., -
    t = re.sub(r"\s+", " ", t).strip()
    return t


def clean_skill(raw: str) -> str | None:
    """Return a clean, lowercase skill string or None if garbage."""
    s = raw.strip().lower()
    s = re.sub(r"\s+", " ", s)
    # reject obviously bad skills
    if not s or len(s) < 2 or len(s) > 100:
        return None
    # reject if it's just punctuation / numbers
    if re.fullmatch(r"[^a-z]+", s):
        return None
    # strip leading/trailing quotes
    s = s.strip("\"'")
    if not s:
        return None
    return s


def parse_date(raw: str | None) -> date | None:
    """Try several date formats; return None on failure."""
    if not raw:
        return None
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def safe_int(raw, default: int = 0) -> int:
    try:
        return int(float(raw))
    except (ValueError, TypeError):
        return default


def safe_float(raw, default: float = 0.0) -> float:
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default


def read_csv(path: Path) -> list[dict]:
    """Read CSV into list[dict]; skip missing files."""
    if not path.exists():
        print(f"  ⚠  {path.name} not found – skipping")
        return []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path):
    """Read JSON file; return None if missing."""
    if not path.exists():
        print(f"  ⚠  {path.name} not found – skipping")
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# =====================================================================
# CITY RESOLVER
# =====================================================================

class CityResolver:
    """Maps raw location strings to a city_id using aliases + fuzzy substring."""

    def __init__(self, city_map: dict[str, int]):
        self._id_map = city_map                          # canonical_name → id
        self._alias: dict[str, int] = {}                 # lowercase alias  → id
        for alias, canonical in CITY_ALIASES.items():
            cid = city_map.get(canonical)
            if cid:
                self._alias[alias] = cid

    def resolve(self, location_raw: str | None) -> int | None:
        if not location_raw:
            return None
        loc = location_raw.strip().lower()
        # 1) exact alias hit
        if loc in self._alias:
            return self._alias[loc]
        # 2) substring match (city name appears inside the raw string)
        for alias, cid in self._alias.items():
            if alias in loc:
                return cid
        return None


# =====================================================================
# SEEDER
# =====================================================================

def seed(reset: bool = False) -> None:
    app = create_app()
    with app.app_context():

        # ── optional full reset ──────────────────────────────────
        if reset:
            print("🔄 Dropping and recreating all tables …")
            db.drop_all()
            db.create_all()
            print("   ✓ Tables recreated\n")
        else:
            db.create_all()

        # ─────────────────────────────────────────────────────────
        # 1. CITIES
        # ─────────────────────────────────────────────────────────
        print("🏙  Seeding cities …")
        city_map: dict[str, int] = {}
        for name, state, tier in CITY_DATA:
            existing = City.query.filter_by(name=name).first()
            if existing:
                city_map[name] = existing.id
                continue
            c = City(name=name, state=state, tier=tier)
            db.session.add(c)
            db.session.flush()
            city_map[name] = c.id
        db.session.commit()
        resolver = CityResolver(city_map)
        print(f"   → {len(city_map)} cities ready\n")

        # ─────────────────────────────────────────────────────────
        # 2. COURSES
        # ─────────────────────────────────────────────────────────
        print("📚 Seeding courses …")
        courses_added = 0
        for cd in COURSES_DATA:
            exists = Course.query.filter_by(title=cd["title"], provider=cd["provider"]).first()
            if exists:
                continue
            db.session.add(Course(**cd))
            courses_added += 1
        db.session.commit()
        print(f"   → {courses_added} new courses inserted\n")

        # ─────────────────────────────────────────────────────────
        # 3. JOBS  (three CSV sources, deduplicated by title_norm + location)
        # ─────────────────────────────────────────────────────────
        print("💼 Seeding jobs …")
        job_count = 0
        seen_jobs: set[tuple[str, int | None]] = set()   # (title_norm, city_id)
        job_id_by_norm: dict[str, int] = {}               # title_norm → job.id  (for skill linking)

        def _insert_job(title: str, desc: str | None, loc: str | None,
                        posted: date | None, source: str) -> bool:
            nonlocal job_count
            if job_count >= MAX_JOBS:
                return False
            title = title.strip()
            if not title:
                return True               # skip blanks but keep going
            norm = normalize_title(title)
            if not norm:
                return True
            city_id = resolver.resolve(loc)
            key = (norm, city_id)
            if key in seen_jobs:
                return True                # deduplicate
            seen_jobs.add(key)

            job = Job(
                title=title[:300],
                title_norm=norm[:300],
                company=None,
                city_id=city_id,
                location_raw=(loc or "")[:200],
                description=(desc[:2000] if desc else None),
                source=source[:50],
                posted_date=posted,
            )
            db.session.add(job)
            db.session.flush()             # get job.id
            job_id_by_norm[norm] = job.id
            job_count += 1

            if job_count % BATCH_SIZE == 0:
                db.session.commit()
                print(f"      … {job_count:,} jobs committed")
            return True

        # 3a) jobs.csv  (main dataset – ~744K rows)
        print("   • jobs.csv")
        for row in read_csv(CSV_DIR / "jobs.csv"):
            ok = _insert_job(
                title=row.get("job_title", ""),
                desc=row.get("description", ""),
                loc=row.get("location", ""),
                posted=parse_date(row.get("posted_date")),
                source=row.get("source", "naukri"),
            )
            if not ok:
                break

        # 3b) old_scrappe_data.csv  (~799K rows)
        if job_count < MAX_JOBS:
            print("   • old_scrappe_data.csv")
            for row in read_csv(CSV_DIR / "old_scrappe_data.csv"):
                ok = _insert_job(
                    title=row.get("job_title", ""),
                    desc=row.get("job_description", ""),
                    loc=row.get("location", ""),
                    posted=parse_date(row.get("posting_date")),
                    source="naukri_old",
                )
                if not ok:
                    break

        # 3c) recent_scrapper_data.csv  (few rows)
        if job_count < MAX_JOBS:
            print("   • recent_scrapper_data.csv")
            for row in read_csv(CSV_DIR / "recent_scrapper_data.csv"):
                _insert_job(
                    title=row.get("job_title", ""),
                    desc=row.get("job_description", ""),
                    loc=row.get("location", ""),
                    posted=parse_date(row.get("date_posted")),
                    source="naukri_live",
                )

        db.session.commit()
        print(f"   → {job_count:,} unique jobs inserted\n")

        # ─────────────────────────────────────────────────────────
        # 4. JOB_SKILLS  (link skills from skill_demand.csv to jobs)
        #    skill_demand has: posted_date, location, skills, demand
        #    Strategy: build city→[job_ids] index from the in-memory
        #    data we already have, then round-robin assign skills.
        # ─────────────────────────────────────────────────────────
        print("🔧 Seeding job_skills …")

        # Build a norm→city_id lookup from seen_jobs (already in memory)
        norm_to_city: dict[str, int | None] = {n: c for n, c in seen_jobs}

        # Build city_id→[job_id, …] index from in-memory dicts (no DB query)
        city_jobs: dict[int | None, list[int]] = {}
        for norm, jid in job_id_by_norm.items():
            cid = norm_to_city.get(norm)
            city_jobs.setdefault(cid, []).append(jid)
        print(f"   • Built city→jobs index: {sum(len(v) for v in city_jobs.values()):,} jobs across {len(city_jobs)} city groups")

        # Free ORM identity map – the 200K Job objects are no longer needed
        db.session.expunge_all()

        skills_added = 0
        seen_job_skills: set[tuple[int, str]] = set()
        rr_idx: dict[int | None, int] = {}  # round-robin pointer per city

        # Stream the CSV instead of loading all 359K rows into memory
        sd_path = CSV_DIR / "skill_demand.csv"
        if sd_path.exists():
            print(f"   • Streaming {sd_path.name} …")
            with sd_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
                for row in csv.DictReader(f):
                    raw_skill = row.get("skills", "")
                    skill = clean_skill(raw_skill)
                    if not skill:
                        continue
                    loc = row.get("location", "")
                    city_id = resolver.resolve(loc)
                    job_list = city_jobs.get(city_id) or city_jobs.get(None, [])
                    if not job_list:
                        continue
                    idx = rr_idx.get(city_id, 0) % len(job_list)
                    rr_idx[city_id] = idx + 1
                    jid = job_list[idx]

                    key = (jid, skill)
                    if key in seen_job_skills:
                        continue
                    seen_job_skills.add(key)

                    db.session.add(JobSkill(job_id=jid, skill_name=skill[:100]))
                    skills_added += 1

                    if skills_added % BATCH_SIZE == 0:
                        db.session.commit()
                        db.session.expunge_all()
                        print(f"      … {skills_added:,} job_skills committed")

                    if skills_added >= MAX_TRENDS:
                        break
        else:
            print(f"   ⚠  {sd_path.name} not found – skipping")

        db.session.commit()
        db.session.expunge_all()
        print(f"   → {skills_added:,} job_skills inserted\n")

        # ─────────────────────────────────────────────────────────
        # 5. AI_VULNERABILITY_SCORES
        #    Sources:
        #       a) job_ai_vulnerability.csv   → global (city_id=NULL)
        #       b) dashboard_job_city_metrics.csv → per city
        # ─────────────────────────────────────────────────────────
        print("🤖 Seeding ai_vulnerability_scores …")
        vuln_count = 0
        seen_vuln: set[tuple[str, int | None]] = set()

        def _insert_vuln(title_norm: str, city_id: int | None,
                         score_raw, conf_raw, reason: str) -> None:
            nonlocal vuln_count
            if vuln_count >= MAX_VULN:
                return
            title_norm = title_norm.strip()
            if not title_norm:
                return
            key = (title_norm, city_id)
            if key in seen_vuln:
                return
            seen_vuln.add(key)

            score = safe_int(score_raw, 50)
            score = int(clamp(score, 0, 100))
            confidence = safe_float(conf_raw, 0.5)
            confidence = round(clamp(confidence, 0.0, 1.0), 4)

            db.session.add(AiVulnerabilityScore(
                job_title_norm=title_norm[:300],
                city_id=city_id,
                score=score,
                confidence=confidence,
                reason=(reason or "")[:2000] if reason else None,
            ))
            vuln_count += 1
            if vuln_count % BATCH_SIZE == 0:
                db.session.commit()
                db.session.expunge_all()
                print(f"      … {vuln_count:,} vulnerability scores committed")

        # 5a) job_ai_vulnerability.csv  (~27K rows, no city) — streamed
        vuln_a = CSV_DIR / "job_ai_vulnerability.csv"
        if vuln_a.exists():
            print(f"   • {vuln_a.name}")
            with vuln_a.open("r", encoding="utf-8", errors="replace", newline="") as f:
                for row in csv.DictReader(f):
                    tn = row.get("job_title_norm") or normalize_title(row.get("job_title", ""))
                    _insert_vuln(tn, None, row.get("ai_vulnerability_score"),
                                 row.get("confidence"), row.get("reason", ""))

        # 5b) dashboard_job_city_metrics.csv  (~85K rows, has location) — streamed
        vuln_b = CSV_DIR / "dashboard_job_city_metrics.csv"
        if vuln_b.exists():
            print(f"   • {vuln_b.name}")
            with vuln_b.open("r", encoding="utf-8", errors="replace", newline="") as f:
                for row in csv.DictReader(f):
                    score_raw = row.get("role_ai_vulnerability_score", "")
                    if not score_raw:
                        continue
                    tn = row.get("job_title_norm") or normalize_title(row.get("job_title", ""))
                    city_id = resolver.resolve(row.get("location", ""))
                    _insert_vuln(tn, city_id, score_raw,
                                 row.get("role_ai_vulnerability_confidence"),
                                 row.get("role_ai_vulnerability_reason", ""))

        db.session.commit()
        db.session.expunge_all()
        print(f"   → {vuln_count:,} vulnerability scores inserted\n")

        # ─────────────────────────────────────────────────────────
        # 6. SKILL_TRENDS
        #    Sources:
        #       a) skill_demand.csv            → per skill + location + period
        #       b) skill_market_2020_present.json → global aggregates
        # ─────────────────────────────────────────────────────────
        print("📈 Seeding skill_trends …")
        trend_count = 0
        seen_trends: set[tuple[str, int | None, str]] = set()  # (skill, city_id, period_iso)

        # 6a) skill_demand.csv  (~359K rows) — streamed
        sd_trends_path = CSV_DIR / "skill_demand.csv"
        if sd_trends_path.exists():
            print(f"   • {sd_trends_path.name}")
            with sd_trends_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
                for row in csv.DictReader(f):
                    if trend_count >= MAX_TRENDS:
                        break
                    skill = clean_skill(row.get("skills", ""))
                    if not skill:
                        continue
                    period = parse_date(row.get("posted_date"))
                    if not period:
                        continue
                    city_id = resolver.resolve(row.get("location", ""))
                    key = (skill, city_id, period.isoformat())
                    if key in seen_trends:
                        continue
                    seen_trends.add(key)

                    demand = safe_int(row.get("demand"), 0)
                    if demand < 0:
                        demand = 0

                    db.session.add(SkillTrend(
                        skill_name=skill[:100],
                        city_id=city_id,
                        period=period,
                        demand_count=demand,
                        change_pct=0.0,
                    ))
                    trend_count += 1

                    if trend_count % BATCH_SIZE == 0:
                        db.session.commit()
                        db.session.expunge_all()
                        print(f"      … {trend_count:,} skill_trends committed")

        # 6b) skill_market_2020_present.json  (~193K items)
        if trend_count < MAX_TRENDS:
            print("   • skill_market_2020_present.json")
            sm_data = read_json(JSON_DIR / "skill_market_2020_present.json")
            if sm_data and isinstance(sm_data.get("items"), list):
                for item in sm_data["items"]:
                    if trend_count >= MAX_TRENDS:
                        break
                    skill = clean_skill(item.get("skill", ""))
                    if not skill:
                        continue
                    # Use latest_month as period; city_id = None (global)
                    period = parse_date(item.get("latest_month") or item.get("first_month"))
                    if not period:
                        continue
                    key = (skill, None, period.isoformat())
                    if key in seen_trends:
                        continue
                    seen_trends.add(key)

                    demand = safe_int(item.get("total_demand"), 0)
                    pct = safe_float(item.get("percent_change"), 0.0)

                    db.session.add(SkillTrend(
                        skill_name=skill[:100],
                        city_id=None,
                        period=period,
                        demand_count=max(0, demand),
                        change_pct=round(pct, 2),
                    ))
                    trend_count += 1

                    if trend_count % BATCH_SIZE == 0:
                        db.session.commit()
                        db.session.expunge_all()
                        print(f"      … {trend_count:,} skill_trends committed")

        db.session.commit()
        db.session.expunge_all()
        print(f"   → {trend_count:,} skill_trends inserted\n")

        # ─────────────────────────────────────────────────────────
        # SUMMARY
        # ─────────────────────────────────────────────────────────
        print("=" * 55)
        print("✅  Database seeded successfully!")
        print(f"    Cities                    : {len(city_map)}")
        print(f"    Courses                   : {courses_added}")
        print(f"    Jobs                      : {job_count:,}")
        print(f"    Job Skills                : {skills_added:,}")
        print(f"    AI Vulnerability Scores   : {vuln_count:,}")
        print(f"    Skill Trends              : {trend_count:,}")
        print("=" * 55)


# =====================================================================
# CLI
# =====================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the OASIS database from CSV/JSON data files.")
    parser.add_argument("--reset", action="store_true",
                        help="Drop ALL tables and recreate before seeding (⚠ destructive)")
    args = parser.parse_args()
    seed(reset=args.reset)
