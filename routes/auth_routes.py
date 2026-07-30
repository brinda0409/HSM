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

    # 1. Check Warden Table First (or if email contains 'warden' or role == 'warden')
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
    login_identifier = email # Can be email or roll_no typed in input box
    student = query_one("""SELECT s.*, r.room_no, r.block 
                           FROM students s 
                           LEFT JOIN rooms r ON s.room_id = r.room_id 
                           WHERE (LOWER(s.email) = ? OR UPPER(s.roll_no) = ?) AND s.password = ?""", 
                        (login_identifier.lower(), login_identifier.upper(), password))
    if student:
        if student.get("status") == "Suspended":
            return jsonify({"success": False, "message": "Your student account is currently Suspended by the Warden. Please contact administration."}), 403

        user_data = {
            "id": student["student_id"],
            "name": student["name"],
            "roll_no": student["roll_no"],
            "email": student["email"],
            "contact": student["contact"],
            "role": "student",
            "room_no": student["room_no"] or "Unassigned",
            "block": student["block"] or "Main Campus",
            "status": student.get("status") or "Active"
        }
        session["user"] = user_data
        logger.info(f"Student logged in: {student['name']} ({student['roll_no']})")
        return jsonify({"success": True, "user": user_data, "message": "Student authenticated successfully."}), 200

    return jsonify({"success": False, "message": "Invalid email/roll number or password. Please check your credentials."}), 401



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
        role_param = request.args.get("role", "").lower()
        if "warden" in role_param:
            default_warden = {
                "id": 1,
                "name": "Dr. Robert Vance",
                "email": "warden@hostel.edu",
                "role": "warden",
                "block_assigned": "Block A & B",
                "office_hours": "09:00 AM - 05:00 PM (Mon-Sat)"
            }
            return jsonify({"success": True, "user": default_warden, "is_demo": True}), 200

        # Default fallback to Alex Johnson demo student if session empty
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
