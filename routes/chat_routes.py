from flask import Blueprint, request, jsonify
from agents.decision_agent import decision_agent
from services.db_service import query_all
from utils.logger import logger

chat_bp = Blueprint("chat_bp", __name__)

@chat_bp.route("/api/chat", methods=["POST"])
def chat():
    """
    POST /api/chat
    Main conversational entry point handled by Decision Agent.
    Body: {"message": "...", "student_id": 1, "role": "student" | "warden"}
    """
    data = request.get_json() or {}
    message = data.get("message")
    student_id = data.get("student_id", 1)
    role = data.get("role", "student")
    if isinstance(role, str):
        role = role.strip().lower()
    else:
        role = "student"

    if not message:
        return jsonify({
            "success": False,
            "error": "BAD_REQUEST",
            "message": "Message field is required."
        }), 400

    try:
        student_id = int(student_id)
    except (ValueError, TypeError):
        student_id = 1

    logger.info(f"API Call POST /api/chat - Student ID: {student_id}, Role: {role}")
    result = decision_agent.process_chat(message, student_id=student_id, role=role)
    return jsonify(result), 200

@chat_bp.route("/api/chat_logs", methods=["GET"])
def get_chat_logs():
    """
    GET /api/chat_logs
    Retrieves execution audit logs for Warden Dashboard oversight.
    """
    logs = query_all("SELECT * FROM chat_logs ORDER BY timestamp DESC LIMIT 50")
    return jsonify({"success": True, "data": logs, "count": len(logs)}), 200
