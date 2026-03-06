from __future__ import annotations

from flask import Blueprint, jsonify, request
import json

from app.data_paths import JSON_DIR
from app.services.career_risk.service import analyze_profile_career_risk
from app.services.user_input.services.profile_builder import build_profile

career_bp = Blueprint("career", __name__)


@career_bp.route("/analyze", methods=["POST"])
def analyze_career():
    if not request.is_json:
        return jsonify({"error": "Request content-type must be application/json"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        profile = build_profile(data)
        result = analyze_profile_career_risk(profile)
        output_path = JSON_DIR / "career_analysis.json"
        output_path.write_text(json.dumps({"profile": profile, "analysis": result}, indent=2), encoding="utf-8")
        return jsonify({"profile": profile, "analysis": result, "saved_json": str(output_path)}), 200
    except FileNotFoundError as exc:
        return jsonify({"error": f"Required file missing: {exc}"}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "Failed to run career analysis"}), 500
