from __future__ import annotations

import logging
import re

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, cast, or_
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
from app.services.groq_career import (
    assess_ai_vulnerability, 
    suggest_next_roles, 
    build_role_roadmap, 
    build_detailed_roadmap_groq, 
    get_topic_subconcepts,
    generate_topic_flashcards
)
from app.services.roadmap_sh import get_detailed_roadmap, match_role_to_slug

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


def _compute_risk_score(title_norm: str, city_name: str, experience: int, skills: list | None = None) -> dict:
    """Compute skill-demand risk from DB signals: skill trends + hiring data + vulnerability index."""

    skills = skills or []

    # 1. Get AI vulnerability score for this role
    vuln = (
        db.session.query(AiVulnerabilityScore)
        .filter(AiVulnerabilityScore.job_title_norm.ilike(f"%{title_norm}%"))
        .first()
    )
    base_vuln = vuln.score if vuln else 50

    # 2. City lookup
    city = db.session.query(City).filter(func.lower(City.name) == city_name.lower()).first()

    # 3. Skill demand trends — check each user skill in SkillTrend
    skill_trends = []
    declining_skills = []
    growing_skills = []
    if skills and city:
        for sk in skills:
            # Get most recent trend entries for this skill in this city
            recent = (
                db.session.query(SkillTrend)
                .filter(
                    func.lower(SkillTrend.skill_name) == sk.lower(),
                    SkillTrend.city_id == city.id,
                )
                .order_by(desc(SkillTrend.period))
                .limit(3)
                .all()
            )
            if not recent:
                # Try broader match (any city) as fallback
                recent = (
                    db.session.query(SkillTrend)
                    .filter(func.lower(SkillTrend.skill_name) == sk.lower())
                    .order_by(desc(SkillTrend.period))
                    .limit(3)
                    .all()
                )
            if recent:
                avg_change = sum(t.change_pct or 0 for t in recent) / len(recent)
                avg_demand = sum(t.demand_count or 0 for t in recent) / len(recent)
                skill_trends.append({"skill": sk, "avg_change": avg_change, "avg_demand": avg_demand})
                if avg_change < -5:
                    declining_skills.append(sk)
                elif avg_change > 5:
                    growing_skills.append(sk)

    # 4. Broader job matching — match ANY keyword from title in this city
    title_words = [w for w in title_norm.split() if len(w) > 2]
    hiring_count = 0
    if city and title_words:
        conditions = [Job.title_norm.ilike(f"%{w}%") for w in title_words]
        hiring_count = (
            db.session.query(func.count(Job.id))
            .filter(Job.city_id == city.id, or_(*conditions))
            .scalar() or 0
        )

    total_city = (db.session.query(func.count(Job.id)).filter(Job.city_id == city.id).scalar() or 1) if city else 1
    hiring_trend_pct = round((hiring_count / total_city) * 100, 2)

    # 5. Compute skill demand score (0 = safe, 100 = high risk)
    # Factor A: avg skill trend (negative change = more risk)
    if skill_trends:
        avg_skill_change = sum(s["avg_change"] for s in skill_trends) / len(skill_trends)
        # Map: +30% growth → 0 risk, -30% decline → 100 risk
        trend_risk = max(0, min(100, int(50 - avg_skill_change * 1.67)))
    else:
        trend_risk = 60  # Unknown skills = moderate risk

    # Factor B: hiring scarcity
    if hiring_count > 100:
        hiring_risk = 10
    elif hiring_count > 50:
        hiring_risk = 25
    elif hiring_count > 20:
        hiring_risk = 40
    elif hiring_count > 5:
        hiring_risk = 60
    else:
        hiring_risk = 80

    # Factor C: experience buffer
    exp_risk = max(0, min(20, int((10 - experience) * 2)))

    # Weighted combination
    final_score = min(100, max(0, int(trend_risk * 0.45 + hiring_risk * 0.35 + exp_risk * 0.20)))

    # Build factors
    factors = []
    if declining_skills:
        factors.append(f"Declining demand for: {', '.join(declining_skills)}")
    if growing_skills:
        factors.append(f"Growing demand for: {', '.join(growing_skills)}")
    factors.append(f"{hiring_count} relevant jobs found in {city_name} ({hiring_trend_pct}% of city market)")
    if skill_trends:
        avg_ch = sum(s["avg_change"] for s in skill_trends) / len(skill_trends)
        direction = "growing" if avg_ch > 0 else "declining"
        factors.append(f"Your skills are {direction} at avg {abs(avg_ch):.1f}% per quarter")
    if experience < 3:
        factors.append(f"Low experience ({experience} years) increases transition risk")

    return {
        "score": final_score,
        "risk_level": _risk_level(final_score),
        "hiring_trend_pct": hiring_trend_pct,
        "ai_mention_pct": round(base_vuln / 100 * 67, 1),
        "peer_percentile": min(99, max(1, final_score)),
        "factors": factors,
        "hiring_count": hiring_count,
        "skill_trends": skill_trends,
        "declining_skills": declining_skills,
        "growing_skills": growing_skills,
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
@jwt_required(optional=True)
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
        user_id = get_jwt_identity()
        wp = WorkerProfile(
            user_id=int(user_id) if user_id else None,
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
        risk = _compute_risk_score(title_norm, city_name, experience, skills)

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

        # --- Groq calls: AI vulnerability + job suggestions ---
        profile_ctx = {
            "job_title": job_title,
            "city": city_name,
            "experience_years": experience,
            "skills": skills,
            "tasks": profile.get("tasks", []),
            "aspirations": profile.get("aspirations", []),
            "domain": profile.get("domain"),
        }

        # 1) AI vulnerability risk via Groq
        ai_vuln = None
        try:
            ai_vuln = assess_ai_vulnerability(profile_ctx)
        except Exception as e:
            logging.exception("Groq AI vulnerability assessment failed: %s", e)

        # 2) Job suggestions via Groq
        job_suggestions = None
        try:
            job_suggestions = suggest_next_roles(
                profile=profile_ctx,
                risk_data=risk,
            )
        except Exception as e:
            logging.exception("Groq role suggestion failed: %s", e)

        response_data = {
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
                "hiring_count": risk["hiring_count"],
                "growing_skills": risk.get("growing_skills", []),
                "declining_skills": risk.get("declining_skills", []),
                "skill_trends": risk.get("skill_trends", []),
                "reskilling_paths": paths,
                "ai_vulnerability": ai_vuln or {
                    "automation_risk": 50,
                    "automation_reason": "Unable to assess — using default estimate.",
                    "ai_takeover_risk": 50,
                    "ai_takeover_reason": "Unable to assess — using default estimate.",
                    "combined_ai_vulnerability": 50,
                },
            },
        }

        if job_suggestions:
            response_data["analysis"]["job_suggestions"] = job_suggestions

        return jsonify(response_data), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Analysis failed: {str(exc)}"}), 500


@career_bp.route("/roadmap", methods=["POST"])
def generate_roadmap():
    """Generate a week-by-week reskilling roadmap for a chosen target role via Groq."""
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    profile_id = data.get("profile_id")
    chosen_role = (data.get("chosen_role") or "").strip()

    if not profile_id or not chosen_role:
        return jsonify({"error": "profile_id and chosen_role are required"}), 400

    try:
        wp = db.session.query(WorkerProfile).get(int(profile_id))
        if not wp:
            return jsonify({"error": "Worker profile not found"}), 404

        city_name = wp.city.name if wp.city else "Unknown"

        # Get latest risk assessment
        ra = (
            db.session.query(RiskAssessment)
            .filter(RiskAssessment.worker_profile_id == wp.id)
            .order_by(desc(RiskAssessment.created_at))
            .first()
        )

        profile_ctx = {
            "job_title": wp.job_title,
            "city": city_name,
            "experience_years": wp.experience_years,
            "skills": wp.extracted_skills or [],
            "domain": wp.domain,
        }
        risk_ctx = {
            "score": ra.score if ra else 50,
            "risk_level": ra.risk_level if ra else "MEDIUM",
        }

        roadmap = build_role_roadmap(
            profile=profile_ctx,
            risk_data=risk_ctx,
            chosen_role=chosen_role,
        )

        if not roadmap:
            return jsonify({"error": "Could not generate roadmap. Please try again."}), 500

        return jsonify({"roadmap": roadmap}), 200

    except Exception as exc:
        logging.exception("Roadmap generation failed: %s", exc)
        return jsonify({"error": f"Roadmap generation failed: {str(exc)}"}), 500


@career_bp.route("/detailed-roadmap", methods=["POST"])
def detailed_roadmap():
    """Fetch a detailed topic-tree roadmap: roadmap.sh first, Groq fallback."""
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    role = (data.get("role") or "").strip()
    if not role:
        return jsonify({"error": "role is required"}), 400

    try:
        # 1. Try roadmap.sh
        result = get_detailed_roadmap(role)
        if result:
            return jsonify({"detailed_roadmap": result}), 200

        # 2. Fallback to Groq
        logging.info("No roadmap.sh match for '%s', falling back to Groq", role)
        result = build_detailed_roadmap_groq(role)
        if result:
            return jsonify({"detailed_roadmap": result}), 200

        return jsonify({"error": "Could not generate detailed roadmap. Please try again."}), 500

    except Exception as exc:
        logging.exception("Detailed roadmap failed: %s", exc)
        return jsonify({"error": f"Detailed roadmap generation failed: {str(exc)}"}), 500


@career_bp.route("/topic-graph", methods=["POST"])
def topic_graph():
    """Get a sub-concept learning graph for a specific topic within a role."""
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    role = (data.get("role") or "").strip()
    topic = (data.get("topic") or "").strip()
    if not role or not topic:
        return jsonify({"error": "role and topic are required"}), 400

    try:
        result = get_topic_subconcepts(role, topic)
        if result:
            return jsonify({"graph": result}), 200
        return jsonify({"error": "Could not generate sub-concept graph."}), 500
    except Exception as exc:
        logging.exception("Topic graph failed: %s", exc)
        return jsonify({"error": f"Topic graph generation failed: {str(exc)}"}), 500


@career_bp.route("/topic-flashcards", methods=["POST"])
def topic_flashcards():
    """Generate 8 study flashcards for a specific topic within a role."""
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    role = (data.get("role") or "").strip()
    topic = (data.get("topic") or "").strip()
    subtopics = data.get("subtopics", [])
    
    if not role or not topic:
        return jsonify({"error": "role and topic are required"}), 400

    try:
        cards = generate_topic_flashcards(role, topic, subtopics)
        if cards:
            return jsonify({"flashcards": cards}), 200
        return jsonify({"error": "Could not generate flashcards."}), 500
    except Exception as exc:
        logging.exception("Flashcard generation failed: %s", exc)
        return jsonify({"error": f"Flashcard generation failed: {str(exc)}"}), 500
