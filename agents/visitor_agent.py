from datetime import datetime
from services.db_service import query_one, query_all, execute_query
from utils.validators import parse_date, parse_time, is_valid_phone
from utils.logger import logger

class VisitorAgent:
    """
    Visitor Management Agent:
    Handles visitor registration, date/time validation, visiting-hour rules check, and student persistence.
    """

    VISITING_START_HOUR = 9   # 09:00 AM
    VISITING_END_HOUR = 20    # 08:00 PM

    def __init__(self):
        self.name = "visitor_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "visitor_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[VisitorAgent] Processing intent: {intent} for student: {student_id}")

        if intent in ["register_visitor", "create_visitor"]:
            return self.register_visitor(student_id, entities)
        elif intent in ["list_visitors", "get_visitors"]:
            return self.list_visitors(student_id)
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported visitor intent: {intent}"
            }

    def register_visitor(self, student_id, entities):
        """
        Validates details and registers a guest/visitor.
        """
        name = entities.get("visitor_name") or entities.get("name") or "Guest Visitor"
        contact = entities.get("contact") or "+1-555-0000"
        purpose = entities.get("purpose") or "Personal Visit"
        raw_date = entities.get("visit_date")
        raw_time = entities.get("visit_time") or "11:00"

        # Validate date
        visit_date = parse_date(raw_date) or datetime.now().strftime("%Y-%m-%d")
        visit_time = parse_time(raw_time) or "11:00"

        # Ensure date is not in the past
        today_str = datetime.now().strftime("%Y-%m-%d")
        if visit_date < today_str:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Invalid visit date '{visit_date}'. Visitors cannot be registered for past dates."
            }

        # Check visiting hours (09:00 AM - 08:00 PM)
        try:
            hour = int(visit_time.split(":")[0])
            if hour < self.VISITING_START_HOUR or hour >= self.VISITING_END_HOUR:
                return {
                    "success": False,
                    "agent": self.name,
                    "data": {},
                    "message": f"Visiting time {visit_time} is outside allowed visiting hours (09:00 AM to 08:00 PM)."
                }
        except Exception:
            pass # fallback to default if hour parsing fails

        try:
            visitor_id = execute_query(
                """INSERT INTO visitors (student_id, name, contact, purpose, visit_date, visit_time, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'Pending')""",
                (student_id, name, contact, purpose, visit_date, visit_time)
            )

            visitor_data = {
                "visitor_id": visitor_id,
                "student_id": student_id,
                "name": name,
                "contact": contact,
                "purpose": purpose,
                "visit_date": visit_date,
                "visit_time": visit_time,
                "status": "Pending"
            }

            logger.info(f"[VisitorAgent] Visitor {name} registered with ID: {visitor_id}")
            return {
                "success": True,
                "agent": self.name,
                "data": visitor_data,
                "message": f"Visitor pass request for '{name}' registered for {visit_date} at {visit_time}. Status: Pending (Waiting for Warden response)."
            }
        except Exception as e:
            logger.error(f"[VisitorAgent] Error registering visitor: {e}")
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Database error registering visitor: {str(e)}"
            }

    def list_visitors(self, student_id=None):
        """Lists visitors for a student or all visitors for hostel management."""
        if student_id:
            rows = query_all("SELECT v.*, COALESCE(s.name, 'Student #' || v.student_id) as student_name, r.room_no FROM visitors v LEFT JOIN students s ON CAST(v.student_id AS TEXT) = CAST(s.student_id AS TEXT) LEFT JOIN rooms r ON s.room_id = r.room_id WHERE CAST(v.student_id AS TEXT) = CAST(? AS TEXT) ORDER BY v.visit_date DESC, v.visit_time DESC", (student_id,))
        else:
            rows = query_all("SELECT v.*, COALESCE(s.name, 'Student #' || v.student_id) as student_name, r.room_no FROM visitors v LEFT JOIN students s ON CAST(v.student_id AS TEXT) = CAST(s.student_id AS TEXT) LEFT JOIN rooms r ON s.room_id = r.room_id ORDER BY v.visit_date DESC, v.visit_time DESC")

        return {
            "success": True,
            "agent": self.name,
            "data": {"visitors": rows, "count": len(rows)},
            "message": f"Retrieved {len(rows)} visitor records."
        }

    def update_status(self, visitor_id, status):
        """Updates status of a visitor pass (Approved / Rejected / Pending)."""
        valid_statuses = ["Pending", "Approved", "Rejected"]
        if status not in valid_statuses:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Invalid status. Must be one of {valid_statuses}"}

        rowcount = execute_query(
            "UPDATE visitors SET status = ? WHERE visitor_id = ?",
            (status, visitor_id)
        )

        if rowcount > 0:
            return {"success": True, "agent": self.name, "data": {"visitor_id": visitor_id, "status": status}, "message": f"Visitor pass #{visitor_id} updated to {status}."}
        else:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Visitor record #{visitor_id} not found."}

visitor_agent = VisitorAgent()

