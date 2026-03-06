"""
Database tools for the AI agent.
Real DB queries against the app's PostgreSQL database for skill trends,
AI vulnerability scores, and worker intelligence.
"""

from __future__ import annotations

from sqlalchemy import func, desc

from app import db
from app.models import (
    AiVulnerabilityScore,
    City,
    Job,
    SkillTrend,
    WorkerProfile,
)


# ═══════════════════════════════════════════════════════════
# Tool Functions (called by the agent)
# ═══════════════════════════════════════════════════════════


def get_skill_trends() -> dict:
    """Return current skill demand trends (growing and declining) from the DB."""
    all_periods = [
        r[0]
        for r in db.session.query(SkillTrend.period)
        .distinct()
        .order_by(desc(SkillTrend.period))
        .all()
    ]
    if len(all_periods) < 4:
        return {"top_growing_skills": {}, "declining_skills": {}}

    recent = all_periods[:3]
    prev = all_periods[3:6]

    def _demand(periods):
        rows = (
            db.session.query(
                SkillTrend.skill_name,
                func.sum(SkillTrend.demand_count).label("d"),
            )
            .filter(SkillTrend.period.in_(periods))
            .group_by(SkillTrend.skill_name)
            .all()
        )
        return {r.skill_name: r.d for r in rows}

    cur = _demand(recent)
    pre = _demand(prev)

    growing = {}
    declining = {}
    for skill, demand in cur.items():
        prev_d = pre.get(skill, 0)
        if prev_d > 0:
            pct = round(((demand - prev_d) / prev_d) * 100, 1)
        elif demand > 0:
            pct = 100.0
        else:
            continue
        if demand < 20:
            continue
        if pct > 5:
            growing[skill] = pct
        elif pct < -5:
            declining[skill] = pct

    top_growing = dict(sorted(growing.items(), key=lambda x: x[1], reverse=True)[:15])
    top_declining = dict(sorted(declining.items(), key=lambda x: x[1])[:10])

    return {"top_growing_skills": top_growing, "declining_skills": top_declining}


def get_ai_vulnerability(role: str, city: str = "") -> dict:
    """Return AI automation vulnerability for a given job role from DB."""
    q = db.session.query(AiVulnerabilityScore).filter(
        AiVulnerabilityScore.job_title_norm.ilike(f"%{role}%")
    )
    if city and city.lower() != "all-india":
        q = q.join(City, AiVulnerabilityScore.city_id == City.id).filter(
            func.lower(City.name) == city.lower()
        )
    vuln = q.order_by(desc(AiVulnerabilityScore.score)).first()

    if vuln:
        city_name = vuln.city.name if vuln.city else "All India"
        return {
            "job_role": vuln.job_title_norm,
            "vulnerability_score": vuln.score / 100,
            "risk_level": (
                "critical" if vuln.score >= 75
                else "high" if vuln.score >= 50
                else "medium" if vuln.score >= 25
                else "low"
            ),
            "city": city_name,
            "explanation": vuln.reason or "No detailed explanation available.",
            "confidence": vuln.confidence,
        }

    return {
        "job_role": role,
        "vulnerability_score": 0.50,
        "risk_level": "medium",
        "city": city or "All India",
        "explanation": f"No specific data for '{role}'. Estimated medium risk.",
    }


def get_skill_intel(skill: str) -> dict:
    """Return intelligence data for a specific skill from DB."""
    all_periods = [
        r[0]
        for r in db.session.query(SkillTrend.period)
        .distinct()
        .order_by(desc(SkillTrend.period))
        .all()
    ]
    recent = all_periods[:3] if len(all_periods) >= 3 else all_periods
    prev = all_periods[3:6] if len(all_periods) >= 6 else []

    cur_demand = (
        db.session.query(func.sum(SkillTrend.demand_count))
        .filter(
            func.lower(SkillTrend.skill_name) == skill.lower(),
            SkillTrend.period.in_(recent),
        )
        .scalar()
    ) or 0

    prev_demand = 0
    if prev:
        prev_demand = (
            db.session.query(func.sum(SkillTrend.demand_count))
            .filter(
                func.lower(SkillTrend.skill_name) == skill.lower(),
                SkillTrend.period.in_(prev),
            )
            .scalar()
        ) or 0

    if prev_demand > 0:
        growth_rate = round(((cur_demand - prev_demand) / prev_demand) * 100, 1)
    elif cur_demand > 0:
        growth_rate = 100.0
    else:
        growth_rate = 0.0

    job_count = (
        db.session.query(func.count(Job.id))
        .filter(Job.title_norm.ilike(f"%{skill}%"))
        .scalar()
    ) or 0

    top_cities = (
        db.session.query(City.name, func.sum(SkillTrend.demand_count).label("d"))
        .join(City, SkillTrend.city_id == City.id)
        .filter(func.lower(SkillTrend.skill_name) == skill.lower())
        .group_by(City.name)
        .order_by(desc("d"))
        .limit(5)
        .all()
    )

    return {
        "skill_name": skill,
        "current_demand": cur_demand,
        "growth_rate": growth_rate,
        "job_postings_count": job_count,
        "top_cities": [{"city": c, "demand": int(d)} for c, d in top_cities],
    }


def get_related_skills(skill_or_role: str) -> dict:
    """Return skills related to a given role using co-occurring skill trends."""
    # Find cities where jobs matching this role exist
    city_ids = [
        r[0]
        for r in db.session.query(Job.city_id)
        .filter(Job.title_norm.ilike(f"%{skill_or_role}%"))
        .distinct()
        .limit(10)
        .all()
        if r[0]
    ]

    if not city_ids:
        # Fallback: top trending skills overall
        rows = (
            db.session.query(SkillTrend.skill_name)
            .group_by(SkillTrend.skill_name)
            .order_by(desc(func.sum(SkillTrend.demand_count)))
            .limit(10)
            .all()
        )
        return {
            "query": skill_or_role,
            "related_skills": [r.skill_name for r in rows],
        }

    # Skills trending in the same cities as this role
    rows = (
        db.session.query(
            SkillTrend.skill_name,
            func.sum(SkillTrend.demand_count).label("d"),
        )
        .filter(SkillTrend.city_id.in_(city_ids))
        .group_by(SkillTrend.skill_name)
        .order_by(desc("d"))
        .limit(10)
        .all()
    )

    return {
        "query": skill_or_role,
        "related_skills": [r.skill_name for r in rows],
        "cities_sampled": len(city_ids),
    }


def get_processed_output(user_id: int) -> dict:
    """Return processed profile data for a user from the DB."""
    profile = (
        db.session.query(WorkerProfile)
        .filter(
            (WorkerProfile.id == user_id) | (WorkerProfile.user_id == user_id)
        )
        .order_by(WorkerProfile.created_at.desc())
        .first()
    )

    if profile:
        return {
            "skills": profile.extracted_skills or [],
            "tools": [],
            "tasks": profile.extracted_tasks or [],
            "aspirations": profile.aspirations or [],
            "domain": profile.domain,
            "job_title": profile.job_title,
        }

    return {
        "skills": [], "tools": [], "tasks": [], "aspirations": [],
        "message": "No processed data for this user",
    }


def get_all_skill_intel() -> list:
    """Return intelligence data for top tracked skills."""
    all_periods = [
        r[0]
        for r in db.session.query(SkillTrend.period)
        .distinct()
        .order_by(desc(SkillTrend.period))
        .all()
    ]
    recent = all_periods[:3] if all_periods else []

    if not recent:
        return []

    rows = (
        db.session.query(
            SkillTrend.skill_name,
            func.sum(SkillTrend.demand_count).label("demand"),
        )
        .filter(SkillTrend.period.in_(recent))
        .group_by(SkillTrend.skill_name)
        .order_by(desc("demand"))
        .limit(30)
        .all()
    )

    return [
        {"skill_name": r.skill_name, "current_demand": int(r.demand)}
        for r in rows
    ]
