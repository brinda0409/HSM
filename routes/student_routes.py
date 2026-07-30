import csv
import io
from flask import Blueprint, jsonify, request, Response
from services.db_service import query_all, query_one, execute_query
from utils.logger import logger
from datetime import datetime, timedelta

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/api/students", methods=["GET"])
def list_students():
    """GET /api/students - List all registered students with room details."""
    rows = query_all("""SELECT s.*, r.room_no, r.block 
                        FROM students s 
                        LEFT JOIN rooms r ON s.room_id = r.room_id 
                        ORDER BY s.student_id DESC""")
    return jsonify({"success": True, "data": rows, "count": len(rows)}), 200

@student_bp.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    """GET /api/students/<id> - Fetch single student record."""
    student = query_one("""SELECT s.*, r.room_no, r.block 
                           FROM students s 
                           LEFT JOIN rooms r ON s.room_id = r.room_id 
                           WHERE s.student_id = ?""", (student_id,))
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404
    return jsonify({"success": True, "data": student}), 200

@student_bp.route("/api/students", methods=["POST"])
def create_student():
    """POST /api/students - Create a new student record."""
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    roll_no = (data.get("roll_no") or "").strip().upper()
    email = (data.get("email") or "").strip().lower()
    contact = (data.get("contact") or "").strip()
    room_id = data.get("room_id")
    password = data.get("password") or "password123"

    if not name or not roll_no or not email or not contact:
        return jsonify({"success": False, "message": "Name, Roll No, Email, and Contact are required fields."}), 400

    # Check for unique constraints
    existing_roll = query_one("SELECT student_id FROM students WHERE UPPER(roll_no) = ?", (roll_no,))
    if existing_roll:
        return jsonify({"success": False, "message": f"Roll Number '{roll_no}' is already registered."}), 400

    existing_email = query_one("SELECT student_id FROM students WHERE LOWER(email) = ?", (email,))
    if existing_email:
        return jsonify({"success": False, "message": f"Email '{email}' is already registered."}), 400

    if room_id:
        room_id = int(room_id)
        room = query_one("SELECT room_id, capacity, occupied_count FROM rooms WHERE room_id = ?", (room_id,))
        if not room:
            return jsonify({"success": False, "message": "Selected room does not exist."}), 400

    try:
        new_id = execute_query(
            "INSERT INTO students (name, roll_no, email, contact, room_id, password) VALUES (?, ?, ?, ?, ?, ?)",
            (name, roll_no, email, contact, room_id, password)
        )

        if room_id:
            execute_query(
                "UPDATE rooms SET occupied_count = occupied_count + 1, status = CASE WHEN occupied_count + 1 >= capacity THEN 'Occupied' ELSE 'Available' END WHERE room_id = ?",
                (room_id,)
            )

        logger.info(f"Created student record ID {new_id} ({name}, Roll: {roll_no})")
        return jsonify({"success": True, "message": "Student created successfully", "student_id": new_id}), 201
    except Exception as e:
        logger.error(f"Error creating student: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@student_bp.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    """PUT /api/students/<id> - Update existing student details."""
    student = query_one("SELECT * FROM students WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status") or student.get("status") or "Active"
    new_room_id = data.get("room_id")
    if new_room_id is not None and new_room_id != "":
        new_room_id = int(new_room_id)
    else:
        new_room_id = student.get("room_id")

    old_room_id = student.get("room_id")

    try:
        execute_query(
            "UPDATE students SET room_id = ?, status = ? WHERE student_id = ?",
            (new_room_id, new_status, student_id)
        )

        # Update room occupancy counts if room changed
        if old_room_id != new_room_id:
            if old_room_id:
                execute_query(
                    "UPDATE rooms SET occupied_count = MAX(0, occupied_count - 1), status = 'Available' WHERE room_id = ?",
                    (old_room_id,)
                )
            if new_room_id:
                execute_query(
                    "UPDATE rooms SET occupied_count = occupied_count + 1, status = CASE WHEN occupied_count + 1 >= capacity THEN 'Occupied' ELSE 'Available' END WHERE room_id = ?",
                    (new_room_id,)
                )

        logger.info(f"Updated student record ID {student_id} (Status: {new_status})")
        return jsonify({"success": True, "message": f"Student status/allocation updated successfully ({new_status})"}), 200
    except Exception as e:
        logger.error(f"Error updating student {student_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@student_bp.route("/api/students/<int:student_id>/status", methods=["PUT"])
def toggle_student_status(student_id):
    """PUT /api/students/<id>/status - Suspend or Activate student account."""
    student = query_one("SELECT * FROM students WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        curr_status = student.get("status") or "Active"
        new_status = "Suspended" if curr_status == "Active" else "Active"

    try:
        execute_query("UPDATE students SET status = ? WHERE student_id = ?", (new_status, student_id))
        logger.info(f"Set student {student_id} status to {new_status}")
        return jsonify({"success": True, "message": f"Student status set to {new_status}", "status": new_status}), 200
    except Exception as e:
        logger.error(f"Error toggling student status {student_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@student_bp.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    """DELETE /api/students/<id> - Delete student record."""
    student = query_one("SELECT * FROM students WHERE student_id = ?", (student_id,))
    if not student:
        return jsonify({"success": False, "message": "Student not found"}), 404

    try:
        old_room_id = student["room_id"]
        execute_query("DELETE FROM students WHERE student_id = ?", (student_id,))

        if old_room_id:
            execute_query(
                "UPDATE rooms SET occupied_count = MAX(0, occupied_count - 1), status = 'Available' WHERE room_id = ?",
                (old_room_id,)
            )

        logger.info(f"Deleted student ID {student_id} ({student['name']})")
        return jsonify({"success": True, "message": "Student record deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting student {student_id}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

@student_bp.route("/api/students/upload-csv", methods=["POST"])
def upload_students_csv():
    """
    POST /api/students/upload-csv - Bulk import students from uploaded CSV file.
    Expected CSV columns: roll_no, name, email, contact, room_no (optional), password (optional)
    """
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No CSV file provided in upload."}), 400

    file = request.files["file"]
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"success": False, "message": "File must be a .csv extension."}), 400

    try:
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        reader = csv.DictReader(stream)

        # Normalize field names to lowercase
        headers = [h.strip().lower() for h in (reader.fieldnames or [])]
        
        required_cols = {"name", "roll_no", "email", "contact"}
        if not required_cols.issubset(set(headers)):
            missing = required_cols - set(headers)
            return jsonify({
                "success": False, 
                "message": f"CSV missing required column headers: {', '.join(missing)}. Required headers: roll_no, name, email, contact, room_no"
            }), 400

        # Pre-fetch rooms for mapping room_no -> room_id
        all_rooms = query_all("SELECT room_id, room_no FROM rooms")
        room_map = {r["room_no"].strip().upper(): r["room_id"] for r in all_rooms}

        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for row_idx, row in enumerate(reader, start=2):
            # Normalize dictionary keys
            clean_row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            
            roll_no = clean_row.get("roll_no", "").upper()
            name = clean_row.get("name", "")
            email = clean_row.get("email", "").lower()
            contact = clean_row.get("contact", "")
            room_no = clean_row.get("room_no", "").upper()
            password = clean_row.get("password") or "password123"

            if not roll_no or not name or not email or not contact:
                skipped_count += 1
                errors.append(f"Row {row_idx}: Missing required fields for Roll No '{roll_no}' / Name '{name}'")
                continue

            room_id = room_map.get(room_no) if room_no else None

            existing = query_one("SELECT student_id, room_id FROM students WHERE UPPER(roll_no) = ?", (roll_no,))

            if existing:
                # Update existing student
                old_room = existing["room_id"]
                execute_query(
                    "UPDATE students SET name = ?, email = ?, contact = ?, room_id = COALESCE(?, room_id), password = ? WHERE student_id = ?",
                    (name, email, contact, room_id, password, existing["student_id"])
                )
                if room_id and old_room != room_id:
                    if old_room:
                        execute_query("UPDATE rooms SET occupied_count = MAX(0, occupied_count - 1), status = 'Available' WHERE room_id = ?", (old_room,))
                    execute_query("UPDATE rooms SET occupied_count = occupied_count + 1, status = CASE WHEN occupied_count + 1 >= capacity THEN 'Occupied' ELSE 'Available' END WHERE room_id = ?", (room_id,))
                updated_count += 1
            else:
                # Insert new student
                new_id = execute_query(
                    "INSERT INTO students (name, roll_no, email, contact, room_id, password) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, roll_no, email, contact, room_id, password)
                )
                if room_id:
                    execute_query("UPDATE rooms SET occupied_count = occupied_count + 1, status = CASE WHEN occupied_count + 1 >= capacity THEN 'Occupied' ELSE 'Available' END WHERE room_id = ?", (room_id,))
                created_count += 1

        total_processed = created_count + updated_count

        return jsonify({
            "success": True,
            "message": f"Successfully processed CSV dataset: {created_count} created, {updated_count} updated, {skipped_count} skipped.",
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "errors": errors
        }), 200

    except Exception as e:
        logger.error(f"Error processing uploaded CSV file: {e}", exc_info=True)
        return jsonify({"success": False, "message": f"Failed to parse CSV file: {str(e)}"}), 500

@student_bp.route("/api/students/sample-csv", methods=["GET"])
def download_sample_csv():
    """GET /api/students/sample-csv - Serves a sample student CSV dataset file for users."""
    sample_content = (
        "roll_no,name,email,contact,room_no,password\n"
        "2026-CS-101,Aarav Sharma,aarav.sharma@hostel.edu,+91-9876543210,A-101,password123\n"
        "2026-CS-102,Diya Kapoor,diya.kapoor@hostel.edu,+91-9876543211,A-102,password123\n"
        "2026-CS-103,Rohan Gupta,rohan.gupta@hostel.edu,+91-9876543212,B-101,password123\n"
        "2026-CS-104,Ananya Rao,ananya.rao@hostel.edu,+91-9876543213,C-101,password123\n"
    )
    return Response(
        sample_content,
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=sample_students_dataset.csv",
            "Content-Type": "text/csv"
        }
    )

@student_bp.route("/api/dashboard/stats", methods=["GET"])
def get_dashboard_stats():
    """GET /api/dashboard/stats - Fetch summary metrics for Admin Dashboard."""
    open_complaints = query_one("SELECT COUNT(*) as cnt FROM complaints WHERE status IN ('Open', 'In Progress')")["cnt"]
    pending_leaves = query_one("SELECT COUNT(*) as cnt FROM leaves WHERE status = 'Pending'")["cnt"]
    
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today_visitors = query_one("SELECT COUNT(*) as cnt FROM visitors WHERE visit_date >= ?", (yesterday_str,))["cnt"]

    rooms_capacity = query_one("SELECT SUM(capacity) as cap, SUM(occupied_count) as occ FROM rooms")
    total_cap = rooms_capacity["cap"] or 1
    total_occ = rooms_capacity["occ"] or 0
    occupancy_pct = round((total_occ / total_cap) * 100, 1)

    return jsonify({
        "success": True,
        "data": {
            "open_complaints": open_complaints,
            "pending_leaves": pending_leaves,
            "today_visitors": today_visitors,
            "occupancy_pct": occupancy_pct,
            "total_occupied": total_occ,
            "total_capacity": total_cap
        }
    }), 200
