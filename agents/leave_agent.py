from datetime import datetime, timedelta
from services.db_service import query_one, query_all, execute_query
from utils.validators import parse_date
from utils.logger import logger

class LeaveAgent:
    """
    Leave Management Agent:
    Handles leave application, relative date resolution, logical range checks, ID generation (LV-YYYY-NNNN), and status updates.
    """

    def __init__(self):
        self.name = "leave_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "leave_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[LeaveAgent] Processing intent: {intent} for student: {student_id}")

        if intent in ["apply_leave", "create_leave"]:
            return self.apply_leave(student_id, entities)
        elif intent in ["get_leave_status", "get_leave"]:
            leave_id = entities.get("leave_id")
            return self.get_leave(leave_id, student_id)
        elif intent in ["list_leaves", "get_student_leaves"]:
            return self.list_leaves(student_id)
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported leave intent: {intent}"
            }

    def apply_leave(self, student_id, entities):
        """
        Applies for leave with relative date resolution and range validation.
        """
        leave_type = entities.get("leave_type", "Home Leave")
        reason = entities.get("reason", "Personal reasons")
        raw_start = entities.get("start_date")
        raw_end = entities.get("end_date")

        now = datetime.now()
        start_date = parse_date(raw_start) or now.strftime("%Y-%m-%d")
        end_date = parse_date(raw_end) or (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

        # Validate date logic
        if start_date > end_date:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Invalid leave range: Start date ({start_date}) cannot be after End date ({end_date})."
            }

        # Generate LV-YYYY-NNNN
        year = now.year
        count_row = query_one("SELECT COUNT(*) as cnt FROM leaves WHERE leave_id LIKE ?", (f"LV-{year}-%",))
        next_num = (count_row["cnt"] if count_row else 0) + 1
        leave_id = f"LV-{year}-{next_num:04d}"

        try:
            execute_query(
                """INSERT INTO leaves (leave_id, student_id, leave_type, start_date, end_date, reason, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'Pending')""",
                (leave_id, student_id, leave_type, start_date, end_date, reason)
            )

            leave_data = {
                "leave_id": leave_id,
                "student_id": student_id,
                "leave_type": leave_type,
                "start_date": start_date,
                "end_date": end_date,
                "reason": reason,
                "status": "Pending",
                "applied_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"[LeaveAgent] Leave applied successfully: {leave_id}")
            return {
                "success": True,
                "agent": self.name,
                "data": leave_data,
                "message": f"Leave request {leave_id} submitted for {leave_type} from {start_date} to {end_date}."
            }
        except Exception as e:
            logger.error(f"[LeaveAgent] Error applying for leave: {e}")
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Database error creating leave request: {str(e)}"
            }

    def get_leave(self, leave_id=None, student_id=None):
        """Retrieves specific leave record or latest leave for student."""
        if leave_id:
            row = query_one("SELECT l.*, COALESCE(s.name, 'Student #' || l.student_id) as student_name FROM leaves l LEFT JOIN students s ON CAST(l.student_id AS TEXT) = CAST(s.student_id AS TEXT) WHERE l.leave_id = ?", (leave_id,))
        elif student_id:
            row = query_one("SELECT l.*, COALESCE(s.name, 'Student #' || l.student_id) as student_name FROM leaves l LEFT JOIN students s ON CAST(l.student_id AS TEXT) = CAST(s.student_id AS TEXT) WHERE CAST(l.student_id AS TEXT) = CAST(? AS TEXT) ORDER BY l.applied_at DESC LIMIT 1", (student_id,))
        else:
            row = None

        if row:
            return {
                "success": True,
                "agent": self.name,
                "data": row,
                "message": f"Found leave request {row['leave_id']} (Status: {row['status']})."
            }
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": "No matching leave record found."
            }

    def list_leaves(self, student_id=None):
        """Lists leave records for student, or all leave records if student_id is None."""
        if student_id:
            rows = query_all("SELECT l.*, COALESCE(s.name, 'Student #' || l.student_id) as student_name, r.room_no FROM leaves l LEFT JOIN students s ON CAST(l.student_id AS TEXT) = CAST(s.student_id AS TEXT) LEFT JOIN rooms r ON s.room_id = r.room_id WHERE CAST(l.student_id AS TEXT) = CAST(? AS TEXT) ORDER BY l.applied_at DESC", (student_id,))
        else:
            rows = query_all("SELECT l.*, COALESCE(s.name, 'Student #' || l.student_id) as student_name, r.room_no FROM leaves l LEFT JOIN students s ON CAST(l.student_id AS TEXT) = CAST(s.student_id AS TEXT) LEFT JOIN rooms r ON s.room_id = r.room_id ORDER BY l.applied_at DESC")

        return {
            "success": True,
            "agent": self.name,
            "data": {"leaves": rows, "count": len(rows)},
            "message": f"Retrieved {len(rows)} leave records."
        }


    def update_status(self, leave_id, status):
        """Updates status of a leave request (Approved / Rejected / Pending)."""
        valid_statuses = ["Pending", "Approved", "Rejected"]
        if status not in valid_statuses:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Invalid status. Must be one of {valid_statuses}"}

        rowcount = execute_query(
            "UPDATE leaves SET status = ? WHERE leave_id = ?",
            (status, leave_id)
        )

        if rowcount > 0:
            return {"success": True, "agent": self.name, "data": {"leave_id": leave_id, "status": status}, "message": f"Leave request {leave_id} updated to {status}."}
        else:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Leave request {leave_id} not found."}

leave_agent = LeaveAgent()
