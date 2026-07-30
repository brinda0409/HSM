from datetime import datetime
from services.db_service import query_one, query_all, execute_query
from utils.logger import logger

class ComplaintAgent:
    """
    Complaint Management Agent:
    Handles registration, categorization, priority assignment, status tracking, and ID generation (CMP-YYYY-NNNN).
    """

    CATEGORIES = ["Electrical", "Plumbing", "Furniture", "Internet", "Cleanliness", "Other"]
    PRIORITIES = ["Low", "Medium", "High", "Urgent"]

    def __init__(self):
        self.name = "complaint_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "complaint_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[ComplaintAgent] Processing intent: {intent} for student: {student_id}")

        if intent in ["register_complaint", "create_complaint"]:
            return self.register_complaint(student_id, entities)
        elif intent in ["get_complaint_status", "get_complaint"]:
            complaint_id = entities.get("complaint_id")
            return self.get_complaint(complaint_id, student_id)
        elif intent in ["list_complaints", "get_complaints"]:
            return self.list_complaints(student_id)
        elif intent in ["resolve_complaint", "close_complaint"]:
            complaint_id = entities.get("complaint_id")
            if complaint_id:
                return self.update_status(complaint_id, "Resolved")
            return {"success": False, "agent": self.name, "data": {}, "message": "Please specify a Complaint ID (e.g., CMP-2026-0001) to resolve."}
        elif intent in ["update_complaint_status", "change_complaint_status"]:
            complaint_id = entities.get("complaint_id")
            status = entities.get("status", "In Progress")
            if complaint_id:
                return self.update_status(complaint_id, status)
            return {"success": False, "agent": self.name, "data": {}, "message": "Please specify a Complaint ID to update status."}
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported complaint intent: {intent}"
            }

    def register_complaint(self, student_id, entities):
        """
        Registers a new complaint with auto-categorization and priority generation.
        """
        description = entities.get("description", "No description provided.")
        category = entities.get("category") or self._auto_categorize(description)
        priority = entities.get("priority") or self._auto_prioritize(category, description)

        # Generate CMP-YYYY-NNNN
        year = datetime.now().year
        count_row = query_one("SELECT COUNT(*) as cnt FROM complaints WHERE complaint_id LIKE ?", (f"CMP-{year}-%",))
        next_num = (count_row["cnt"] if count_row else 0) + 1
        complaint_id = f"CMP-{year}-{next_num:04d}"

        try:
            execute_query(
                """INSERT INTO complaints (complaint_id, student_id, category, description, priority, status)
                   VALUES (?, ?, ?, ?, ?, 'Open')""",
                (complaint_id, student_id, category, description, priority)
            )

            complaint_data = {
                "complaint_id": complaint_id,
                "student_id": student_id,
                "category": category,
                "description": description,
                "priority": priority,
                "status": "Open",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"[ComplaintAgent] Complaint registered successfully: {complaint_id}")
            return {
                "success": True,
                "agent": self.name,
                "data": complaint_data,
                "message": f"Complaint {complaint_id} registered successfully under category {category} with {priority} priority."
            }
        except Exception as e:
            logger.error(f"[ComplaintAgent] Failed to register complaint: {e}")
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Failed to record complaint in database: {str(e)}"
            }

    def get_complaint(self, complaint_id=None, student_id=None):
        """Retrieves a specific complaint by ID, or latest complaint for student."""
        if complaint_id:
            row = query_one("SELECT c.*, s.name as student_name FROM complaints c JOIN students s ON c.student_id = s.student_id WHERE c.complaint_id = ?", (complaint_id,))
        elif student_id:
            row = query_one("SELECT c.*, s.name as student_name FROM complaints c JOIN students s ON c.student_id = s.student_id WHERE c.student_id = ? ORDER BY c.created_at DESC LIMIT 1", (student_id,))
        else:
            row = None

        if row:
            return {
                "success": True,
                "agent": self.name,
                "data": row,
                "message": f"Found complaint {row['complaint_id']} (Status: {row['status']})."
            }
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": "No matching complaint record found."
            }

    def list_complaints(self, student_id=None):
        """Lists complaints for student, or all complaints if student_id is None."""
        if student_id:
            rows = query_all("SELECT c.*, s.name as student_name, r.room_no FROM complaints c JOIN students s ON c.student_id = s.student_id LEFT JOIN rooms r ON s.room_id = r.room_id WHERE c.student_id = ? ORDER BY c.created_at DESC", (student_id,))
        else:
            rows = query_all("SELECT c.*, s.name as student_name, r.room_no FROM complaints c JOIN students s ON c.student_id = s.student_id LEFT JOIN rooms r ON s.room_id = r.room_id ORDER BY c.created_at DESC")
        
        return {
            "success": True,
            "agent": self.name,
            "data": {"complaints": rows, "count": len(rows)},
            "message": f"Retrieved {len(rows)} complaint records."
        }

    def update_status(self, complaint_id, status):
        """Updates status of a complaint (Open, In Progress, Resolved, Closed)."""
        valid_statuses = ["Open", "In Progress", "Resolved", "Closed"]
        if status not in valid_statuses:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Invalid status. Must be one of {valid_statuses}"}

        resolved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status in ["Resolved", "Closed"] else None

        rowcount = execute_query(
            "UPDATE complaints SET status = ?, resolved_at = COALESCE(?, resolved_at) WHERE complaint_id = ?",
            (status, resolved_at, complaint_id)
        )

        if rowcount > 0:
            return {"success": True, "agent": self.name, "data": {"complaint_id": complaint_id, "status": status}, "message": f"Complaint {complaint_id} updated to {status}."}
        else:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Complaint {complaint_id} not found."}

    def _auto_categorize(self, text):
        t = text.lower()
        if any(w in t for w in ["light", "fan", "ac", "air condition", "switch", "plug", "socket", "power", "electricity"]):
            return "Electrical"
        elif any(w in t for w in ["water", "tap", "sink", "leak", "flush", "toilet", "drain", "pipe"]):
            return "Plumbing"
        elif any(w in t for w in ["wifi", "internet", "router", "network", "lan"]):
            return "Internet"
        elif any(w in t for w in ["bed", "chair", "table", "door", "cupboard", "desk", "window", "lock"]):
            return "Furniture"
        elif any(w in t for w in ["clean", "dirty", "dustbin", "trash", "garbage", "pest"]):
            return "Cleanliness"
        return "Other"

    def _auto_prioritize(self, category, text):
        t = text.lower()
        if any(w in t for w in ["urgent", "emergency", "spark", "fire", "smoke", "flooding", "short circuit"]):
            return "Urgent"
        if category in ["Electrical", "Plumbing", "Internet"] or any(w in t for w in ["broken", "no water", "no light", "hot", "leaking"]):
            return "High"
        return "Medium"

complaint_agent = ComplaintAgent()
