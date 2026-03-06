from flask import Blueprint, jsonify, request
import json

from app.data_paths import JSON_DIR
from app.services.user_input.services.profile_builder import build_profile

user_input_bp = Blueprint("user_input", __name__)


def _store_profile_output(_profile_data):
    output_path = JSON_DIR / "processed_output.json"
    output_path.write_text(json.dumps(_profile_data, indent=2), encoding="utf-8")
    return str(output_path)


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
