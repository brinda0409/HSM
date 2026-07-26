from flask import Blueprint, jsonify
from services.db_service import query_all, query_one

student_bp = Blueprint("student_bp", __name__)

@student_bp.route("/api/students", methods=["GET"])
def list_students():
    """GET /api/students - List all registered students with room details."""
    rows = query_all("""SELECT s.*, r.room_no, r.block 
                        FROM students s 
                        LEFT JOIN rooms r ON s.room_id = r.room_id 
                        ORDER BY s.student_id""")
    return jsonify({"success": True, "data": rows, "count": len(rows)}), 200

from datetime import datetime, timedelta

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
