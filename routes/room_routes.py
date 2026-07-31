from flask import Blueprint, request, jsonify
from agents.room_agent import room_agent

room_bp = Blueprint("room_bp", __name__)

@room_bp.route("/api/rooms/<room_no>", methods=["GET"])
def get_room(room_no):
    """GET /api/rooms/<room_no> - Get room availability & specs."""
    res = room_agent.get_room(room_no=room_no)
    status_code = 200 if res.get("success") else 404
    return jsonify(res), status_code

@room_bp.route("/api/rooms", methods=["GET"])
def list_rooms():
    """GET /api/rooms - List all rooms."""
    res = room_agent.list_rooms()
    return jsonify(res), 200

@room_bp.route("/api/rooms/transfers", methods=["GET"])
def list_transfers():
    """GET /api/rooms/transfers - List all student room change requests."""
    res = room_agent.list_transfer_requests()
    return jsonify(res), 200

@room_bp.route("/api/rooms/transfers/<int:transfer_id>/status", methods=["PUT"])
def update_transfer_status(transfer_id):
    """PUT /api/rooms/transfers/<transfer_id>/status - Warden approve or reject room change request."""
    data = request.get_json() or {}
    status = data.get("status")

    if not status:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "status is required."}), 400

    res = room_agent.update_transfer_status(transfer_id, status)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

@room_bp.route("/api/rooms/allocate", methods=["POST"])
def allocate_room():
    """POST /api/rooms/allocate - Allocate student to room."""
    data = request.get_json() or {}
    student_id = data.get("student_id")
    room_no = data.get("room_no")

    if not student_id or not room_no:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "student_id and room_no are required."}), 400

    res = room_agent.allocate_room(int(student_id), room_no)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code

@room_bp.route("/api/rooms/transfer", methods=["POST"])
def transfer_room():
    """POST /api/rooms/transfer - Transfer student to a different room."""
    data = request.get_json() or {}
    student_id = data.get("student_id")
    to_room_no = data.get("to_room_no") or data.get("room_no")
    reason = data.get("reason") or "Requested room transfer"

    if not student_id or not to_room_no:
        return jsonify({"success": False, "error": "BAD_REQUEST", "message": "student_id and to_room_no are required."}), 400

    res = room_agent.request_room_transfer(int(student_id), to_room_no, reason)
    status_code = 200 if res.get("success") else 400
    return jsonify(res), status_code
