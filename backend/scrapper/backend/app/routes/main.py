from flask import Blueprint, jsonify

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    return jsonify({
        "message": "Welcome to the API",
        "status": "running",
        "version": "1.0.0",
    })


@main_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200
