from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, WorkerProfile, RiskAssessment

user_bp = Blueprint("user", __name__)

@user_bp.route("/api/me", methods=["GET"])
@jwt_required()
def get_profile():

    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))

    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = WorkerProfile.query.filter_by(user_id=user.id).order_by(WorkerProfile.created_at.desc()).first()

    risk = None
    paths_data = []

    if profile:
        risk = RiskAssessment.query.filter_by(worker_profile_id=profile.id).order_by(RiskAssessment.created_at.desc()).first()
        if risk:
            # Fetch reskilling paths
            for p in risk.reskilling_paths:
                steps_data = []
                for s in p.steps:
                    steps_data.append({
                        "step_order": s.step_order,
                        "week_start": s.week_start,
                        "week_end": s.week_end,
                        "title": s.title,
                        "provider": s.provider,
                        "duration_weeks": s.course.duration_weeks if s.course else None,
                        "is_free": s.course.is_free if s.course else None,
                        "url": s.course.url if s.course else None,
                        "skill_focus": s.skill_focus,
                        "description": s.notes or (s.course.description if s.course else "")
                    })
                paths_data.append({
                    "target_role": p.target_role,
                    "target_role_vulnerability": 0,
                    "hiring_count": p.target_role_hiring_count,
                    "total_weeks": p.total_weeks,
                    "hours_per_week": p.hours_per_week,
                    "confidence": p.confidence,
                    "steps": steps_data
                })

    return jsonify({
        "user": user.to_dict(),
        "profile": {
            "id": profile.id if profile else None,
            "job_title": profile.job_title if profile else None,
            "normalized_job_title": profile.job_title_norm if profile else None,
            "city": profile.city.name if profile and profile.city else None,
            "experience_years": profile.experience_years if profile else None,
            "domain": profile.domain if profile else None,
            "skills": profile.extracted_skills if profile else []
        },
        "risk": {
            "score": risk.score if risk else None,
            "level": risk.risk_level if risk else None
        },
        "analysis": {
            "risk_score": risk.score if risk else 50,
            "risk_level": risk.risk_level if risk else "MEDIUM",
            "hiring_trend_pct": risk.hiring_trend_pct if risk else 0,
            "ai_mention_pct": risk.ai_mention_pct if risk else 0,
            "peer_percentile": risk.peer_percentile if risk else 50,
            "factors": risk.factors if risk else [],
            "reskilling_paths": paths_data
        }
    })