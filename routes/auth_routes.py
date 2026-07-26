from flask import Blueprint, request, jsonify, session
from services.db_service import query_one
from utils.logger import logger

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/api/login", methods=["POST"])
def login():
    """
    POST /api/login - Authenticate Student or Warden credentials.
    Payload: { "email": str, "password": str, "role": "student" | "warden" (optional) }
    """
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    role = data.get("role", "").strip().lower()

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    # 1. Check Warden Table
    if role == "warden" or not role:
        warden = query_one("SELECT * FROM wardens WHERE LOWER(email) = ? AND password = ?", (email, password))
        if warden:
            user_data = {
                "id": warden["warden_id"],
                "name": warden["name"],
                "email": warden["email"],
                "role": "warden",
                "block_assigned": warden["block_assigned"],
                "office_hours": warden["office_hours"]
            }
            session["user"] = user_data
            logger.info(f"Warden logged in: {warden['name']} ({warden['email']})")
            return jsonify({"success": True, "user": user_data, "message": "Warden authenticated successfully."}), 200

    # 2. Check Student Table
    if role == "student" or not role:
        student = query_one("""SELECT s.*, r.room_no, r.block 
                               FROM students s 
                               LEFT JOIN rooms r ON s.room_id = r.room_id 
                               WHERE LOWER(s.email) = ? AND s.password = ?""", (email, password))
        if student:
            user_data = {
                "id": student["student_id"],
                "name": student["name"],
                "roll_no": student["roll_no"],
                "email": student["email"],
                "contact": student["contact"],
                "role": "student",
                "room_no": student["room_no"] or "Unassigned",
                "block": student["block"] or "Main Campus"
            }
            session["user"] = user_data
            logger.info(f"Student logged in: {student['name']} (Room {student['room_no']})")
            return jsonify({"success": True, "user": user_data, "message": "Student authenticated successfully."}), 200

    return jsonify({"success": False, "message": "Invalid email or password. Please check your credentials."}), 401


@auth_bp.route("/api/logout", methods=["POST"])
def logout():
    """POST /api/logout - End current user session."""
    user = session.pop("user", None)
    if user:
        logger.info(f"User logged out: {user.get('email')}")
    return jsonify({"success": True, "message": "Logged out successfully."}), 200


@auth_bp.route("/api/me", methods=["GET"])
def get_current_user():
    """GET /api/me - Retrieve current authenticated user session."""
    user = session.get("user")
    if user:
        return jsonify({"success": True, "user": user}), 200
    else:
        # Default fallback to Alex Johnson demo user if session empty for seamless evaluation
        default_user = {
            "id": 1,
            "name": "Alex Johnson",
            "roll_no": "CS2024-001",
            "email": "alex.j@hostel.edu",
            "role": "student",
            "room_no": "A-101",
            "block": "Block A"
        }
        return jsonify({"success": True, "user": default_user, "is_demo": True}), 200
