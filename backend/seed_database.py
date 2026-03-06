"""
Seed the PostgreSQL database from existing CSV files.
Run once: python seed_database.py
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app, db
from app.models import (
    AiVulnerabilityScore,
    City,
    Course,
    Job,
    JobSkill,
    SkillTrend,
)

DATA_DIR = Path(__file__).resolve().parent / "data" / "csv"

# Import IT-job filter from normalize script
from normalize_it_jobs import is_it_job

# ── Indian cities with state + tier ─────────────────────────────────
CITY_DATA = [
    ("Bengaluru", "Karnataka", 1), ("Mumbai", "Maharashtra", 1),
    ("Delhi NCR", "Delhi", 1), ("Hyderabad", "Telangana", 1),
    ("Pune", "Maharashtra", 1), ("Chennai", "Tamil Nadu", 1),
    ("Kolkata", "West Bengal", 1), ("Ahmedabad", "Gujarat", 1),
    ("Jaipur", "Rajasthan", 2), ("Indore", "Madhya Pradesh", 2),
    ("Lucknow", "Uttar Pradesh", 2), ("Bhopal", "Madhya Pradesh", 2),
    ("Surat", "Gujarat", 2), ("Nagpur", "Maharashtra", 2),
    ("Coimbatore", "Tamil Nadu", 2), ("Kochi", "Kerala", 2),
    ("Chandigarh", "Chandigarh", 2), ("Patna", "Bihar", 2),
    ("Noida", "Uttar Pradesh", 2), ("Gurgaon", "Haryana", 2),
    ("Thiruvananthapuram", "Kerala", 2), ("Visakhapatnam", "Andhra Pradesh", 2),
    ("Vadodara", "Gujarat", 2), ("Mysuru", "Karnataka", 2),
    ("Ranchi", "Jharkhand", 3), ("Dehradun", "Uttarakhand", 3),
    ("Raipur", "Chhattisgarh", 3), ("Guwahati", "Assam", 3),
    ("Jodhpur", "Rajasthan", 3), ("Vijayawada", "Andhra Pradesh", 3),
]

# ── NPTEL / SWAYAM / PMKVY courses ──────────────────────────────────
COURSES = [
    # NPTEL courses
    ("Data Science for Engineers", "NPTEL", "IIT Madras", "https://nptel.ac.in/courses/106106179", 8, True,
     ["data analysis", "python", "statistics", "machine learning"], "Comprehensive data science course covering Python, statistics, and ML fundamentals."),
    ("Programming in Python", "NPTEL", "IIT Madras", "https://nptel.ac.in/courses/106106182", 8, True,
     ["python", "programming", "software development"], "Learn Python programming from basics to advanced concepts."),
    ("Deep Learning", "NPTEL", "IIT Madras", "https://nptel.ac.in/courses/106106184", 12, True,
     ["deep learning", "neural networks", "AI", "python"], "Advanced deep learning course covering CNNs, RNNs, and Transformers."),
    ("Database Management System", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/106105175", 8, True,
     ["sql", "database", "data management"], "Core DBMS concepts including SQL, normalization, and transaction processing."),
    ("Cloud Computing", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/106105167", 8, True,
     ["cloud computing", "AWS", "DevOps"], "Fundamentals of cloud computing, virtualization, and distributed systems."),
    ("Introduction to Machine Learning", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/106105152", 8, True,
     ["machine learning", "AI", "python", "statistics"], "ML fundamentals: regression, classification, clustering, and evaluation."),
    ("Artificial Intelligence", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/106105077", 12, True,
     ["AI", "search algorithms", "knowledge representation"], "Core AI concepts including search, logic, and planning."),
    ("Cyber Security", "NPTEL", "IIT Madras", "https://nptel.ac.in/courses/106106178", 8, True,
     ["cybersecurity", "network security", "encryption"], "Cybersecurity fundamentals, cryptography, and network security."),
    ("Introduction to Internet of Things", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/106105166", 8, True,
     ["IoT", "embedded systems", "sensors", "networking"], "IoT ecosystems including sensors, networking, and cloud integration."),
    ("Business Analytics", "NPTEL", "IIT Kharagpur", "https://nptel.ac.in/courses/110105089", 8, True,
     ["business analytics", "data analysis", "excel", "statistics"], "Analytics using statistical methods and business intelligence tools."),

    # SWAYAM courses
    ("AI for Everyone", "SWAYAM", "IGNOU", "https://swayam.gov.in/courses/ai-for-everyone", 6, True,
     ["AI", "machine learning", "digital literacy"], "Non-technical introduction to AI concepts and applications."),
    ("Digital Marketing", "SWAYAM", "IIM Bangalore", "https://swayam.gov.in/courses/digital-marketing", 8, True,
     ["digital marketing", "SEO", "social media", "content marketing"], "Complete digital marketing: SEO, SEM, social media, and analytics."),
    ("Communication Skills", "SWAYAM", "CEC", "https://swayam.gov.in/courses/communication-skills", 4, True,
     ["communication", "presentation", "soft skills", "english"], "Effective workplace communication and presentation skills."),
    ("Data Analytics with Python", "SWAYAM", "IIT Roorkee", "https://swayam.gov.in/courses/data-analytics-python", 8, True,
     ["python", "data analysis", "pandas", "visualization"], "Hands-on data analytics using Python, Pandas, and Matplotlib."),
    ("Web Development", "SWAYAM", "CEC", "https://swayam.gov.in/courses/web-development", 8, True,
     ["html", "css", "javascript", "web development"], "Full-stack web development from HTML/CSS to JavaScript frameworks."),
    ("Financial Accounting", "SWAYAM", "IGNOU", "https://swayam.gov.in/courses/financial-accounting", 6, True,
     ["accounting", "finance", "bookkeeping", "excel"], "Fundamentals of financial accounting and reporting."),
    ("Project Management", "SWAYAM", "IIM Bangalore", "https://swayam.gov.in/courses/project-management", 6, True,
     ["project management", "agile", "scrum", "leadership"], "Project management methodologies including Agile and Waterfall."),
    ("Entrepreneurship", "SWAYAM", "IIM Ahmedabad", "https://swayam.gov.in/courses/entrepreneurship", 8, True,
     ["entrepreneurship", "business plan", "strategy", "leadership"], "Starting and managing a new venture, market analysis and fundraising."),

    # PMKVY courses
    ("Domestic Data Entry Operator", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/domestic-data-entry", 4, True,
     ["data entry", "typing", "MS Office", "excel"], "Certified data entry operations with computer fundamentals."),
    ("CRM Domestic Non-Voice", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/crm-domestic", 4, True,
     ["customer service", "CRM", "communication", "problem solving"], "Customer relationship management for non-voice processes."),
    ("AI & Machine Learning Technician", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/ai-ml-technician", 6, True,
     ["AI", "machine learning", "python", "data processing"], "Entry-level AI/ML skills for technology support roles."),
    ("Solar Panel Installation Technician", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/solar-panel", 3, True,
     ["solar energy", "installation", "electrical", "renewable energy"], "Hands-on solar panel installation and maintenance."),
    ("Medical Records Technician", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/medical-records", 4, True,
     ["medical records", "healthcare", "data management", "documentation"], "Managing medical records and healthcare documentation."),
    ("Retail Sales Associate", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/retail-sales", 3, True,
     ["retail", "sales", "customer service", "inventory"], "Professional retail sales and customer engagement skills."),
    ("Beauty Therapist", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/beauty-therapist", 4, True,
     ["beauty", "skincare", "customer service", "wellness"], "Professional beauty therapy and wellness services."),
    ("Digital Marketing Executive", "PMKVY", "NSDC", "https://pmkvyofficial.org/courses/digital-marketing", 4, True,
     ["digital marketing", "social media", "SEO", "content creation"], "Certified digital marketing skills for employment."),
]


def _normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _match_city(location_raw: str, city_map: dict[str, int]) -> int | None:
    if not location_raw:
        return None
    loc = location_raw.strip().lower()
    for city_name, city_id in city_map.items():
        if city_name.lower() in loc:
            return city_id
    return None


def _parse_date(date_str: str) -> date | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  [SKIP] {path.name} not found")
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def seed():
    app = create_app()
    with app.app_context():
        print("Dropping and recreating all tables...")
        db.session.execute(db.text("DROP SCHEMA public CASCADE"))
        db.session.execute(db.text("CREATE SCHEMA public"))
        db.session.commit()
        db.create_all()

        # ── 1. Seed cities ──────────────────────────────────────
        print("Seeding cities...")
        city_map = {}
        for name, state, tier in CITY_DATA:
            c = City(name=name, state=state, tier=tier)
            db.session.add(c)
            db.session.flush()
            city_map[name] = c.id
        db.session.commit()
        print(f"  → {len(city_map)} cities inserted")

        # ── 2. Seed courses ─────────────────────────────────────
        print("Seeding courses...")
        for title, provider, institution, url, weeks, is_free, skills, desc in COURSES:
            db.session.add(Course(
                title=title, provider=provider, institution=institution,
                url=url, duration_weeks=weeks, is_free=is_free,
                skills_covered=skills, description=desc,
            ))
        db.session.commit()
        print(f"  → {len(COURSES)} courses inserted")

        # ── 3. Seed jobs from CSV ───────────────────────────────
        print("Seeding jobs (this may take a few minutes)...")
        rows = _read_csv(DATA_DIR / "jobs.csv")
        batch = []
        skills_batch = []
        count = 0
        for row in rows:
            title = row.get("job_title", "").strip()
            if not title:
                continue
            norm = _normalize_title(title)
            if not is_it_job(norm):
                continue  # Skip non-IT jobs
            location_raw = row.get("location", "").strip()
            city_id = _match_city(location_raw, city_map)
            posted = _parse_date(row.get("posted_date", ""))
            desc = row.get("description", "")

            job = Job(
                title=title,
                title_norm=norm,
                location_raw=location_raw,
                city_id=city_id,
                description=desc[:2000] if desc else None,  # Truncate long descriptions
                source=row.get("source", "naukri"),
                posted_date=posted,
            )
            db.session.add(job)
            count += 1

            if count % 5000 == 0:
                db.session.flush()
                print(f"  ... {count} jobs processed")

            if count >= 150000:  
                break

        db.session.commit()
        print(f"  → {count} jobs inserted")

        # ── 4. Seed AI vulnerability scores ─────────────────────
        print("Seeding AI vulnerability scores...")
        vuln_rows = _read_csv(DATA_DIR / "job_ai_vulnerability.csv")
        vuln_count = 0
        seen = set()
        for row in vuln_rows:
            title_norm = (row.get("job_title_norm") or _normalize_title(row.get("job_title", ""))).strip()
            if not title_norm or title_norm in seen:
                continue
            if not is_it_job(title_norm):
                continue  # Skip non-IT vulnerability entries
            seen.add(title_norm)
            try:
                score = int(float(row.get("ai_vulnerability_score", 50)))
            except (ValueError, TypeError):
                score = 50
            score = max(0, min(100, score))
            try:
                confidence = float(row.get("confidence", 0.5))
            except (ValueError, TypeError):
                confidence = 0.5

            db.session.add(AiVulnerabilityScore(
                job_title_norm=title_norm,
                city_id=None,
                score=score,
                confidence=confidence,
                reason=row.get("reason", ""),
            ))
            vuln_count += 1
            if vuln_count % 5000 == 0:
                db.session.flush()
                print(f"  ... {vuln_count} vulnerability scores processed")

        db.session.commit()
        print(f"  → {vuln_count} vulnerability scores inserted")

        # ── 5. Seed skill trends ────────────────────────────────
        print("Seeding skill trends...")
        skill_rows = _read_csv(DATA_DIR / "skill_demand.csv")
        st_count = 0
        seen_trends = set()
        for row in skill_rows:
            skill = row.get("skills", "").strip()
            if not skill or len(skill) > 100:
                continue
            location = row.get("location", "").strip()
            city_id = _match_city(location, city_map)
            period = _parse_date(row.get("posted_date", ""))
            if not period:
                continue

            key = (skill.lower(), city_id, period.isoformat())
            if key in seen_trends:
                continue
            seen_trends.add(key)

            try:
                demand = int(float(row.get("demand", 0)))
            except (ValueError, TypeError):
                demand = 0

            db.session.add(SkillTrend(
                skill_name=skill.lower(),
                city_id=city_id,
                period=period,
                demand_count=demand,
            ))
            st_count += 1
            if st_count % 10000 == 0:
                db.session.flush()
                print(f"  ... {st_count} skill trends processed")

            if st_count >= 200000:
                break

        db.session.commit()
        print(f"  → {st_count} skill trends inserted")

        # ── 6. Seed recent scraper data ─────────────────────────
        print("Seeding recent scraper data...")
        recent = _read_csv(DATA_DIR / "recent_scrapper_data.csv")
        rc = 0
        for row in recent:
            title = row.get("job_title", "").strip()
            if not title:
                continue
            norm = _normalize_title(title)
            if not is_it_job(norm):
                continue  # Skip non-IT jobs
            location_raw = row.get("location", "").strip()
            city_id = _match_city(location_raw, city_map)
            desc = row.get("job_description", "")
            db.session.add(Job(
                title=title,
                title_norm=norm,
                location_raw=location_raw,
                city_id=city_id,
                description=desc[:2000] if desc else None,
                source="naukri_live",
                posted_date=None,
                scraped_at=datetime.utcnow(),
            ))
            rc += 1
        db.session.commit()
        print(f"  → {rc} recent jobs inserted")

        print("\n✓ Database seeded successfully!")
        print(f"  Cities: {len(city_map)}")
        print(f"  Courses: {len(COURSES)}")
        print(f"  Jobs: {count + rc}")
        print(f"  AI Vulnerability Scores: {vuln_count}")
        print(f"  Skill Trends: {st_count}")


if __name__ == "__main__":
    seed()
