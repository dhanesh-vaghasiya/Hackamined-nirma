"""
Routes for the AI roadmap generation pipeline.
"""

from flask import Blueprint, jsonify, request

from app.services.agent.agent import run_roadmap_pipeline
from app.services.agent.tools.db_tools import (
    get_skill_trends,
    get_ai_vulnerability,
    get_skill_intel,
    get_related_skills,
    get_processed_output,
    get_all_skill_intel,
)
from app.services.agent.tools.nptel_tools import search_nptel_courses

roadmap_bp = Blueprint("roadmap", __name__)


@roadmap_bp.route("/generate", methods=["POST"])
def generate_roadmap():
    """
    Main endpoint: run the full AI roadmap pipeline.
    Expects JSON body:
    {
        "job_title": "Data Entry Operator",
        "city": "Ahmedabad",
        "experience": 3,
        "description": "I do data entry in Excel and some basic Tally work.",
        "user_id": 1  (optional)
    }
    """
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    required = ["job_title", "city", "experience", "description"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        result = run_roadmap_pipeline(data)
        return jsonify({"success": True, "data": result}), 200
    except Exception as exc:
        return jsonify({"error": f"Pipeline failed: {str(exc)}"}), 500


@roadmap_bp.route("/skill-trends", methods=["GET"])
def skill_trends():
    """Return current skill demand trends."""
    return jsonify(get_skill_trends())


@roadmap_bp.route("/ai-vulnerability", methods=["GET"])
def ai_vulnerability():
    """Return AI vulnerability for a role. Query params: role, city (optional)."""
    role = request.args.get("role", "")
    city = request.args.get("city", "")
    if not role:
        return jsonify({"error": "Missing 'role' query parameter"}), 400
    return jsonify(get_ai_vulnerability(role, city))


@roadmap_bp.route("/skill-intel", methods=["GET"])
def skill_intel():
    """Return intel for a specific skill. Query param: skill."""
    skill = request.args.get("skill", "")
    if not skill:
        return jsonify({"error": "Missing 'skill' query parameter"}), 400
    return jsonify(get_skill_intel(skill))


@roadmap_bp.route("/skill-intel/all", methods=["GET"])
def all_skill_intel():
    """Return intel for all tracked skills."""
    return jsonify(get_all_skill_intel())


@roadmap_bp.route("/related-skills", methods=["GET"])
def related_skills():
    """Return related skills. Query param: query."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    return jsonify(get_related_skills(query))


@roadmap_bp.route("/nptel-courses", methods=["GET"])
def nptel_courses():
    """Search NPTEL courses. Query param: query."""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400
    return jsonify(search_nptel_courses(query))


@roadmap_bp.route("/processed-output/<int:user_id>", methods=["GET"])
def processed_output(user_id):
    """Return processed output for a user."""
    return jsonify(get_processed_output(user_id))
