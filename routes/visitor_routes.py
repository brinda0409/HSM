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
