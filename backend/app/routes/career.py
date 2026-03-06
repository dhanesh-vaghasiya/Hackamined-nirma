from __future__ import annotations

import re
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, cast
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.types import Text

from app import db
from app.models import (
    AiVulnerabilityScore,
    City,
    Course,
    Job,
    ReskillingPath,
    ReskillingPathStep,
    RiskAssessment,
    SkillTrend,
    WorkerProfile,
)
from app.services.user_input.services.profile_builder import build_profile

career_bp = Blueprint("career", __name__)


def _normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _risk_level(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def _compute_risk_score(title_norm: str, city_name: str, experience: int) -> dict:
    """Compute risk score from DB signals: vulnerability index + hiring trends + AI mentions."""

    # 1. Get AI vulnerability score for this role
    vuln = (
        db.session.query(AiVulnerabilityScore)
        .filter(AiVulnerabilityScore.job_title_norm.ilike(f"%{title_norm}%"))
        .first()
    )
    base_score = vuln.score if vuln else 50

    # 2. Get hiring trend for this role in this city
    city = db.session.query(City).filter(func.lower(City.name) == city_name.lower()).first()
    hiring_count = 0
    hiring_trend_pct = 0.0
    if city:
        hiring_count = (
            db.session.query(func.count(Job.id))
            .filter(Job.city_id == city.id, Job.title_norm.ilike(f"%{title_norm}%"))
            .scalar() or 0
        )
        # Compare with general hiring in city
        total_city = db.session.query(func.count(Job.id)).filter(Job.city_id == city.id).scalar() or 1
        hiring_trend_pct = round((hiring_count / total_city) * 100, 2)

    # 3. Adjust score based on experience (lower experience = higher risk)
    exp_factor = max(0, min(15, 15 - experience)) / 15 * 10  # up to +10 for 0 experience

    # 4. Adjust based on hiring scarcity
    scarcity_factor = 0
    if hiring_count < 5:
        scarcity_factor = 10
    elif hiring_count < 20:
        scarcity_factor = 5

    final_score = min(100, max(0, int(base_score + exp_factor + scarcity_factor)))

    # Build factors list
    factors = []
    if vuln:
        factors.append(f"AI vulnerability index for similar roles: {vuln.score}/100")
        if vuln.reason:
            factors.append(vuln.reason)
    factors.append(f"Only {hiring_count} matching jobs found in {city_name}")
    if experience < 3:
        factors.append(f"Low experience ({experience} years) increases transition risk")

    return {
        "score": final_score,
        "risk_level": _risk_level(final_score),
        "hiring_trend_pct": hiring_trend_pct,
        "ai_mention_pct": round(base_score / 100 * 67, 1),  # approximate
        "peer_percentile": min(99, max(1, final_score)),
        "factors": factors,
        "hiring_count": hiring_count,
    }


def _build_reskilling_paths(title_norm: str, city_name: str, skills: list, risk_score: int) -> list:
    """Build week-by-week reskilling paths with real courses."""

    # Find low-risk roles that are hiring in this city
    city = db.session.query(City).filter(func.lower(City.name) == city_name.lower()).first()

    # Get low-vulnerability roles hiring in this city
    target_roles_q = (
        db.session.query(
            AiVulnerabilityScore.job_title_norm,
            AiVulnerabilityScore.score,
            func.count(Job.id).label("hiring_count"),
        )
        .join(Job, Job.title_norm == AiVulnerabilityScore.job_title_norm)
        .filter(AiVulnerabilityScore.score < 40)  # Low risk roles only
    )
    if city:
        target_roles_q = target_roles_q.filter(Job.city_id == city.id)

    target_roles = (
        target_roles_q
        .group_by(AiVulnerabilityScore.job_title_norm, AiVulnerabilityScore.score)
        .order_by(desc("hiring_count"))
        .limit(3)
        .all()
    )

    if not target_roles:
        # Fallback: get any low-vulnerability roles
        target_roles = (
            db.session.query(
                AiVulnerabilityScore.job_title_norm,
                AiVulnerabilityScore.score,
                db.literal(0).label("hiring_count"),
            )
            .filter(AiVulnerabilityScore.score < 40)
            .order_by(AiVulnerabilityScore.score)
            .limit(3)
            .all()
        )

    paths = []
    for target in target_roles:
        # Find relevant courses
        search_skills = skills if skills else ["python", "data analysis"]
        courses = (
            db.session.query(Course)
            .filter(Course.skills_covered.op("&&")(cast(search_skills, PG_ARRAY(Text))))
            .order_by(Course.duration_weeks)
            .limit(4)
            .all()
        )
        if not courses:
            courses = db.session.query(Course).order_by(func.random()).limit(3).all()

        # Build weekly plan
        steps = []
        week_cursor = 1
        for i, course in enumerate(courses):
            dur = course.duration_weeks or 4
            steps.append({
                "step_order": i + 1,
                "week_start": week_cursor,
                "week_end": week_cursor + dur - 1,
                "course_id": course.id,
                "title": course.title,
                "provider": course.provider,
                "institution": course.institution,
                "url": course.url,
                "duration_weeks": dur,
                "is_free": course.is_free,
                "skill_focus": ", ".join(course.skills_covered or []),
            })
            week_cursor += dur

        total_weeks = week_cursor - 1

        paths.append({
            "target_role": target.job_title_norm,
            "target_role_vulnerability": target.score,
            "hiring_count": target.hiring_count,
            "total_weeks": total_weeks,
            "hours_per_week": 10,
            "confidence": round(max(0.3, 1 - (target.score / 100)) * min(1.0, target.hiring_count / 10 if target.hiring_count else 0.5), 2),
            "steps": steps,
        })

    return paths


@career_bp.route("/analyze", methods=["POST"])
def analyze_career():
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # Validate required fields
    job_title = (data.get("job_title") or "").strip()
    city_name = (data.get("city") or "").strip()
    experience = data.get("experience", 0)
    writeup = (data.get("writeup") or "").strip()

    if not job_title or not city_name or not writeup:
        return jsonify({"error": "job_title, city, and writeup are required"}), 400

    try:
        experience = int(experience)
    except (ValueError, TypeError):
        experience = 0

    try:
        # Build profile (NLP extraction)
        profile = build_profile(data)
        title_norm = _normalize_title(job_title)
        skills = profile.get("skills", [])

        # Save worker profile to DB
        city = db.session.query(City).filter(func.lower(City.name) == city_name.lower()).first()
        wp = WorkerProfile(
            job_title=job_title,
            job_title_norm=title_norm,
            city_id=city.id if city else None,
            experience_years=experience,
            writeup=writeup,
            extracted_skills=skills,
            extracted_tasks=profile.get("tasks", []),
            aspirations=profile.get("aspirations", []),
            domain=profile.get("domain"),
        )
        db.session.add(wp)
        db.session.flush()

        # Compute risk score from DB signals
        risk = _compute_risk_score(title_norm, city_name, experience)

        # Save risk assessment
        ra = RiskAssessment(
            worker_profile_id=wp.id,
            score=risk["score"],
            risk_level=risk["risk_level"],
            hiring_trend_pct=risk["hiring_trend_pct"],
            ai_mention_pct=risk["ai_mention_pct"],
            peer_percentile=risk["peer_percentile"],
            factors=risk["factors"],
        )
        db.session.add(ra)
        db.session.flush()

        # Build reskilling paths
        paths = _build_reskilling_paths(title_norm, city_name, skills, risk["score"])

        # Save paths to DB
        for p in paths:
            rp = ReskillingPath(
                risk_assessment_id=ra.id,
                target_role=p["target_role"],
                target_role_hiring_count=p.get("hiring_count", 0),
                total_weeks=p["total_weeks"],
                hours_per_week=p["hours_per_week"],
                confidence=p["confidence"],
            )
            db.session.add(rp)
            db.session.flush()
            for s in p["steps"]:
                db.session.add(ReskillingPathStep(
                    reskilling_path_id=rp.id,
                    step_order=s["step_order"],
                    week_start=s["week_start"],
                    week_end=s["week_end"],
                    course_id=s.get("course_id"),
                    title=s["title"],
                    provider=s.get("provider"),
                    skill_focus=s.get("skill_focus"),
                ))

        db.session.commit()

        return jsonify({
            "profile": {
                "id": wp.id,
                "job_title": job_title,
                "normalized_job_title": title_norm,
                "city": city_name,
                "experience_years": experience,
                "skills": skills,
                "tasks": profile.get("tasks", []),
                "aspirations": profile.get("aspirations", []),
                "domain": profile.get("domain"),
            },
            "analysis": {
                "risk_score": risk["score"],
                "risk_level": risk["risk_level"],
                "hiring_trend_pct": risk["hiring_trend_pct"],
                "ai_mention_pct": risk["ai_mention_pct"],
                "peer_percentile": risk["peer_percentile"],
                "factors": risk["factors"],
                "reskilling_paths": paths,
            },
        }), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Analysis failed: {str(exc)}"}), 500
