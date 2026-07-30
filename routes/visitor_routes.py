from flask import Blueprint, request, jsonify
from agents.visitor_agent import visitor_agent

visitor_bp = Blueprint("visitor_bp", __name__)

@visitor_bp.route("/api/visitors", methods=["POST"])
def register_visitor():
    """POST /api/visitors - Register a visitor."""
    data = request.get_json() or {}
    student_id = data.get("student_id", 1)

    req = {
        "intent": "register_visitor",
        "entities": data,
        "student_id": int(student_id) if str(student_id).isdigit() else 1
    }
    res = visitor_agent.process_request(req)
    status_code = 201 if res.get("success") else 400
    return jsonify(res), status_code

@visitor_bp.route("/api/visitors", methods=["GET"])
def list_visitors():
    """GET /api/visitors - List all visitors (optional query param ?student_id=X)."""
    student_id = request.args.get("student_id")
    student_id = int(student_id) if student_id and student_id.isdigit() else None
    res = visitor_agent.list_visitors(student_id=student_id)
    return jsonify(res), 200

@visitor_bp.route("/api/visitors/<int:visitor_id>/status", methods=["PUT"])
def update_visitor_status(visitor_id):
    """PUT /api/visitors/<visitor_id>/status - Approve or reject visitor pass."""
    data = request.get_json() or {}
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "Status field is required."}), 400

    res = visitor_agent.update_status(visitor_id, status)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

