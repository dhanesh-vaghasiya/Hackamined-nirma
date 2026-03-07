from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

from app import db
from app.data_paths import JSON_DIR
from app.models import City, WorkerProfile
from app.services.user_input.services.profile_builder import build_profile

user_input_bp = Blueprint("user_input", __name__)


# ── helpers ──────────────────────────────────────────────────
def _store_profile_output(_profile_data):
    output_path = JSON_DIR / "processed_output.json"
    output_path.write_text(json.dumps(_profile_data, indent=2), encoding="utf-8")
    return str(output_path)


def _resolve_city_id(city_name: str):
    """Return the city ID for the given name, or None if not found."""
    if not city_name:
        return None
    city = City.query.filter(
        db.func.lower(City.name) == city_name.strip().lower()
    ).first()
    return city.id if city else None


# ── 1. Analyze only (no DB save) ────────────────────────────
@user_input_bp.route("/analyze-profile", methods=["GET", "POST"])
def analyze_profile():
    if request.method == "GET":
        return jsonify({"message": "Use POST request with JSON body"}), 200

    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        profile = build_profile(data)
        saved_path = _store_profile_output(profile)
        return jsonify({"profile": profile, "saved_json": saved_path}), 200
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to process profile"}), 500


# ── 2. Submit profile → process + save to DB ────────────────
@user_input_bp.route("/submit-profile", methods=["POST"])
@jwt_required()
def submit_profile():
    """
    Accepts user details, processes them through the profile builder,
    and persists a WorkerProfile row in the database.

    Expected JSON body:
    {
        "job_title": "Senior Executive BPO",
        "city": "Bengaluru",
        "experience": 3,
        "writeup": "I handle daily customer escalations …"
    }
    """
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    # ── Process through the existing profile builder ─────────
    try:
        profile = build_profile(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to process profile"}), 500

    # ── Resolve foreign keys ─────────────────────────────────
    user_id = int(get_jwt_identity())
    city_id = _resolve_city_id(data.get("city", ""))

    # ── Persist to database ──────────────────────────────────
    try:
        worker_profile = WorkerProfile(
            user_id=user_id,
            job_title=data.get("job_title", "").strip(),
            job_title_norm=profile["normalized_job_title"],
            city_id=city_id,
            experience_years=profile["experience_years"],
            writeup=data.get("writeup", ""),
            extracted_skills=profile["skills"] + profile.get("tools", []),
            extracted_tasks=profile["tasks"],
            aspirations=profile["aspirations"],
            domain=profile["domain"],
        )
        db.session.add(worker_profile)
        db.session.commit()

        # Also store the JSON output for downstream pipelines
        _store_profile_output(profile)

        return jsonify({
            "message": "Profile saved successfully",
            "worker_profile_id": worker_profile.id,
            "profile": profile,
        }), 201

    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(exc)}"}), 500


# ── 3. Get current user's profiles ──────────────────────────
@user_input_bp.route("/my-profiles", methods=["GET"])
@jwt_required()
def get_my_profiles():
    """Return all worker profiles belonging to the authenticated user."""
    user_id = int(get_jwt_identity())
    profiles = WorkerProfile.query.filter_by(user_id=user_id).order_by(
        WorkerProfile.created_at.desc()
    ).all()

    results = []
    for wp in profiles:
        results.append({
            "id": wp.id,
            "job_title": wp.job_title,
            "job_title_norm": wp.job_title_norm,
            "city": wp.city.name if wp.city else None,
            "experience_years": wp.experience_years,
            "extracted_skills": wp.extracted_skills or [],
            "extracted_tasks": wp.extracted_tasks or [],
            "aspirations": wp.aspirations or [],
            "domain": wp.domain,
            "created_at": wp.created_at.isoformat() if wp.created_at else None,
        })

    return jsonify({"profiles": results}), 200
