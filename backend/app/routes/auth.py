from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    unset_jwt_cookies,
)
import bcrypt

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validate input
    if not data:
        return jsonify({"message": "No data provided"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400

    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Invalid credentials"}), 409

    # Hash password and create user
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user = User(
        name=name,
        email=email,
        password_hash=hashed.decode("utf-8"),
    )

    db.session.add(user)
    db.session.commit()

    # Generate token and set as httpOnly cookie
    token = create_access_token(identity=str(user.id))
    response = jsonify({"user": user.to_dict()})
    response.status_code = 201
    set_access_cookies(response, token)
    return response


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"message": "No data provided"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Find user
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Verify password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
        return jsonify({"message": "Invalid email or password"}), 401

    # Generate token and set as httpOnly cookie
    token = create_access_token(identity=str(user.id))
    response = jsonify({"user": user.to_dict()})
    set_access_cookies(response, token)
    return response


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear the JWT cookie."""
    response = jsonify({"message": "Logged out successfully"})
    unset_jwt_cookies(response)
    return response


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_me():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json() or {}

    if "name" in data and data["name"].strip():
        user.name = data["name"].strip()

    db.session.commit()
    return jsonify({"user": user.to_dict()}), 200