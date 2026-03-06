from flask import jsonify


def success_response(data=None, message="Success", status_code=200):
    """Standard success response."""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return jsonify(response), status_code


def error_response(message="An error occurred", status_code=400):
    """Standard error response."""
    return jsonify({"success": False, "message": message}), status_code
