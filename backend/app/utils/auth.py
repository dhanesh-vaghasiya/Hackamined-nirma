from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from app.models import User


def get_current_user():
    """Get the current authenticated user from JWT."""
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))


def admin_required(fn):
    """Decorator to require admin role (extend User model with a role field)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if not user:
            return jsonify({"message": "User not found"}), 404
        # Add role checking logic here when you add roles
        # if user.role != "admin":
        #     return jsonify({"message": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper
