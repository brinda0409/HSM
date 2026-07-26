from flask import Blueprint, request, jsonify
from agents.leave_agent import leave_agent

leave_bp = Blueprint("leave_bp", __name__)

@leave_bp.route("/api/leaves", methods=["POST"])
def apply_leave():
    """POST /api/leaves - Submit a leave application."""
    data = request.get_json() or {}
    student_id = data.get("student_id", 1)

    req = {
        "intent": "apply_leave",
        "entities": data,
        "student_id": int(student_id) if str(student_id).isdigit() else 1
    }
    res = leave_agent.process_request(req)
    status_code = 201 if res.get("success") else 400
    return jsonify(res), status_code

@leave_bp.route("/api/leaves/<student_id>", methods=["GET"])
def get_student_leaves(student_id):
    """GET /api/leaves/<student_id> - List leaves for a specific student."""
    if str(student_id).isdigit():
        res = leave_agent.list_leaves(student_id=int(student_id))
    else:
        # if leave_id like LV-2026-0001 was passed
        res = leave_agent.get_leave(leave_id=student_id)
    return jsonify(res), 200

@leave_bp.route("/api/leaves", methods=["GET"])
def list_leaves():
    """GET /api/leaves - List all leave applications across hostel."""
    res = leave_agent.list_leaves()
    return jsonify(res), 200

@leave_bp.route("/api/leaves/<leave_id>/status", methods=["PUT"])
def update_leave_status(leave_id):
    """PUT /api/leaves/<leave_id>/status - Approve or reject leave application."""
    data = request.get_json() or {}
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "Status field is required."}), 400

    res = leave_agent.update_status(leave_id, status)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code
