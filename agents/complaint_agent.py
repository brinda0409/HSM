from datetime import datetime
from services.db_service import query_one, query_all, execute_query
from utils.logger import logger

class ComplaintAgent:
    """
    Enhanced Autonomous Complaint Management Agent:
    Executes an 8-step intelligent pipeline:
    Register -> Categorize -> Find Similar Complaints -> Assign Severity -> 
    Estimate Resolution Time -> Suggest Technician -> Recommend Action -> Explain Why
    """

    CATEGORIES = ["Electrical", "Plumbing", "Furniture", "Internet", "Cleanliness", "Other"]
    SEVERITIES = ["Low", "Medium", "High", "Urgent"]

    TECHNICIAN_DIRECTORY = {
        "Electrical": {"name": "Technician Suresh Kumar", "dept": "Electrical Maintenance", "ext": "102"},
        "Plumbing": {"name": "Technician Ramesh Patel", "dept": "Plumbing Operations", "ext": "104"},
        "Internet": {"name": "Network Engineer Ankit Sharma", "dept": "IT Helpdesk", "ext": "108"},
        "Furniture": {"name": "Carpentry Specialist Mohan Lal", "dept": "Facilities Dept", "ext": "110"},
        "Cleanliness": {"name": "Supervisor Sunita Devi", "dept": "Sanitation Dept", "ext": "112"},
        "Other": {"name": "Campus Maintenance Desk", "dept": "General Services", "ext": "100"}
    }

    ETA_MAP = {
        "Urgent": "2 Hours",
        "High": "4 Hours",
        "Medium": "12 Hours",
        "Low": "24 Hours"
    }

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
        Executes the 8-step intelligent complaint processing pipeline.
        """
        description = entities.get("description", "No description provided.")

        # Step 1: Register & Generate CMP-YYYY-NNNN ID
        year = datetime.now().year
        count_row = query_one("SELECT COUNT(*) as cnt FROM complaints WHERE complaint_id LIKE ?", (f"CMP-{year}-%",))
        next_num = (count_row["cnt"] if count_row else 0) + 1
        complaint_id = f"CMP-{year}-{next_num:04d}"

        # Fetch student & room info for context
        student = query_one("""SELECT s.*, r.room_no, r.block 
                               FROM students s 
                               LEFT JOIN rooms r ON s.room_id = r.room_id 
                               WHERE s.student_id = ?""", (student_id,))
        s_name = student["name"] if student else f"Student #{student_id}"
        room_no = student["room_no"] if student else "Hostel Room"

        # Step 2: Categorize
        category = entities.get("category") or self._auto_categorize(description)

        # Step 3: Find Similar Complaints
        similar_rows = query_all(
            "SELECT complaint_id, category, description, status FROM complaints WHERE category = ? AND complaint_id != ? ORDER BY created_at DESC LIMIT 3",
            (category, complaint_id)
        )
        similar_ids = [r["complaint_id"] for r in similar_rows]
        similar_summary = f"Found {len(similar_ids)} similar complaint(s) ({', '.join(similar_ids)})" if similar_ids else "No prior similar complaints found."

        # Step 4: Assign Severity
        severity = entities.get("priority") or self._auto_prioritize(category, description)

        # Step 5: Estimate Resolution Time
        eta = self.ETA_MAP.get(severity, "12 Hours")

        # Step 6: Suggest Technician
        tech_info = self.TECHNICIAN_DIRECTORY.get(category, self.TECHNICIAN_DIRECTORY["Other"])
        tech_display = f"**{tech_info['name']}** ({tech_info['dept']}, Ext: {tech_info['ext']})"

        # Step 7: Recommend Action
        recommended_action = f"Dispatch {tech_info['name']} to **{room_no}** to inspect and resolve {category.lower()} issue."

        # Step 8: Explain Why
        explain_why = f"{severity} severity assigned based on {category.lower()} impact criteria. Resolution ETA set to {eta} according to {tech_info['dept']} SLA."

        # Save to database
        try:
            execute_query(
                """INSERT INTO complaints (complaint_id, student_id, category, description, priority, status)
                   VALUES (?, ?, ?, ?, ?, 'Open')""",
                (complaint_id, student_id, category, description, severity)
            )

            complaint_data = {
                "complaint_id": complaint_id,
                "student_id": student_id,
                "category": category,
                "description": description,
                "priority": severity,
                "status": "Open",
                "similar_complaints": similar_ids,
                "eta": eta,
                "technician": tech_info,
                "recommended_action": recommended_action,
                "explain_why": explain_why,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            full_msg = f"✅ **Complaint Registered**: **{complaint_id}**\n\n" \
                       f"🔄 **Autonomous Agent Processing Pipeline**:\n\n" \
                       f"• 🏷️ **Category**: **{category}**\n" \
                       f"• 🔍 **Find Similar Complaints**: {similar_summary}\n" \
                       f"• ⚡ **Assign Severity**: **{severity}**\n" \
                       f"• ⏱️ **Estimate Resolution Time**: **{eta}**\n" \
                       f"• 👤 **Suggest Technician**: {tech_display}\n" \
                       f"• 💡 **Recommend Action**: {recommended_action}\n" \
                       f"• 🧠 **Explain Why**: {explain_why}"

            logger.info(f"[ComplaintAgent] Pipeline executed successfully for {complaint_id}")
            return {
                "success": True,
                "agent": self.name,
                "data": complaint_data,
                "message": full_msg
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
                "message": f"Found complaint {row['complaint_id']} (Status: {row['status']}, Category: {row['category']}, Priority: {row['priority']})."
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
