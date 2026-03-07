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

    profile = WorkerProfile.query.filter_by(user_id=user.id).first()

    risk = None
    if profile:
        risk = RiskAssessment.query.filter_by(worker_profile_id=profile.id).first()

    return jsonify({
        "user": user.to_dict(),
        "profile": {
            "job_title": profile.job_title if profile else None,
            "experience_years": profile.experience_years if profile else None,
            "domain": profile.domain if profile else None,
            "skills": profile.extracted_skills if profile else []
        },
        "risk": {
            "score": risk.score if risk else None,
            "level": risk.risk_level if risk else None
        }
    })