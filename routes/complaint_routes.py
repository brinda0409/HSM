from flask import Blueprint, request, jsonify
from agents.complaint_agent import complaint_agent

complaint_bp = Blueprint("complaint_bp", __name__)

@complaint_bp.route("/api/complaints", methods=["POST"])
def create_complaint():
    """POST /api/complaints - Register a complaint manually or via API."""
    data = request.get_json() or {}
    student_id = data.get("student_id", 1)
    
    req = {
        "intent": "register_complaint",
        "entities": data,
        "student_id": int(student_id) if str(student_id).isdigit() else 1
    }
    res = complaint_agent.process_request(req)
    status_code = 201 if res.get("success") else 400
    return jsonify(res), status_code

@complaint_bp.route("/api/complaints/<complaint_id>", methods=["GET"])
def get_complaint(complaint_id):
    """GET /api/complaints/<id> - Fetch a single complaint by ID."""
    res = complaint_agent.get_complaint(complaint_id=complaint_id)
    status_code = 200 if res.get("success") else 404
    return jsonify(res), status_code

@complaint_bp.route("/api/complaints", methods=["GET"])
def list_complaints():
    """GET /api/complaints - List complaints (optional query param ?student_id=X)."""
    student_id = request.args.get("student_id")
    student_id = int(student_id) if student_id and student_id.isdigit() else None
    res = complaint_agent.list_complaints(student_id=student_id)
    return jsonify(res), 200

@complaint_bp.route("/api/complaints/<complaint_id>/status", methods=["PUT"])
def update_complaint_status(complaint_id):
    """PUT /api/complaints/<id>/status - Update complaint status (Open, In Progress, Resolved, Closed)."""
    data = request.get_json() or {}
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "Status field is required."}), 400

    res = complaint_agent.update_status(complaint_id, status)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code
