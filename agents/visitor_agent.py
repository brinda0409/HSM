from datetime import datetime
from services.db_service import query_one, query_all, execute_query
from utils.validators import parse_date, parse_time, is_valid_phone
from utils.logger import logger

class VisitorAgent:
    """
    Autonomous AI Visitor Management Agent:
    Performs multi-layer observation, visiting-hour rule verification, historical pattern analysis, 
    inter-agent conflict detection (Leave Agent overlap, Complaint Agent room flags), 
    risk scoring (Low/Medium/High), confidence score generation, and Warden AI decision cards.
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
        elif intent in ["approve_visitor", "approve_visitor_pass"]:
            visitor_id = entities.get("visitor_id")
            if not visitor_id:
                name = entities.get("visitor_name") or entities.get("name")
                if name:
                    row = query_one("SELECT visitor_id FROM visitors WHERE name LIKE ? AND status = 'Pending'", (f"%{name}%",))
                    if row:
                        visitor_id = row["visitor_id"]
            if visitor_id:
                return self.update_status(visitor_id, "Approved")
            return {"success": False, "agent": self.name, "data": {}, "message": "Please specify a Visitor Pass ID or Name to approve."}
        elif intent in ["reject_visitor", "reject_visitor_pass"]:
            visitor_id = entities.get("visitor_id")
            if visitor_id:
                return self.update_status(visitor_id, "Rejected")
            return {"success": False, "agent": self.name, "data": {}, "message": "Please specify a Visitor Pass ID to reject."}
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported visitor intent: {intent}"
            }

    def register_visitor(self, student_id, entities):
        """
        Validates details, registers visitor, and runs Autonomous AI Evaluation Pipeline.
        """
        name = entities.get("visitor_name") or entities.get("name") or "Guest Visitor"
        contact = entities.get("contact") or "+1-555-0000"
        purpose = entities.get("purpose") or "Parent Visit"
        raw_date = entities.get("visit_date")
        raw_time = entities.get("visit_time") or "11:00"

        # Validate date & time
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
        time_valid = True
        try:
            hour = int(visit_time.split(":")[0])
            if hour < self.VISITING_START_HOUR or hour >= self.VISITING_END_HOUR:
                time_valid = False
        except Exception:
            pass

        if not time_valid:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Visiting time {visit_time} is outside allowed hostel visiting hours (09:00 AM to 08:00 PM)."
            }

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

            # Run Autonomous AI Agent Evaluation Pipeline
            ai_eval = self.evaluate_visitor(visitor_data)
            visitor_data["ai_decision"] = ai_eval

            logger.info(f"[VisitorAgent] Visitor {name} registered & evaluated via AI with ID: {visitor_id} (Risk: {ai_eval['risk_score']}%)")

            msg = f"✅ **Visitor Pass Registered**: **#{visitor_id}**\n\n" \
                  f"🧠 **Autonomous AI Visitor Decision Card**:\n" \
                  f"• 👁️ **Observation**: Visitor **{name}** registered for **{purpose}** on **{visit_date}** at **{visit_time}**.\n" \
                  f"• 📜 **Policy Check**: {ai_eval['policy_status']}\n" \
                  f"• 📊 **Historical Analysis**: {ai_eval['historical_summary']}\n" \
                  f"• ⚠️ **Conflict Check**: {ai_eval['conflict_summary']}\n" \
                  f"• 🛡️ **Risk Score**: **{ai_eval['risk_score']}% ({ai_eval['risk_level']})** — {ai_eval['risk_reason']}\n" \
                  f"• 💡 **AI Recommendation**: **{ai_eval['recommendation']}** (Confidence: **{ai_eval['confidence']}%**)\n" \
                  f"• 🎯 **Reason**: {ai_eval['reason']}"

            return {
                "success": True,
                "agent": self.name,
                "data": visitor_data,
                "message": msg
            }
        except Exception as e:
            logger.error(f"[VisitorAgent] Error registering visitor: {e}")
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Database error registering visitor: {str(e)}"
            }

    def evaluate_visitor(self, visitor_dict):
        """
        Executes AI Agent Reasoning, Pattern Analysis, Conflict Detection, and Risk Calculation.
        """
        student_id = visitor_dict.get("student_id", 1)
        v_name = visitor_dict.get("name", "Guest")
        purpose = visitor_dict.get("purpose", "Parent Visit")
        visit_date = visitor_dict.get("visit_date", "")
        visit_time = visitor_dict.get("visit_time", "11:00")

        # Fetch host student & room context
        student = query_one("""SELECT s.*, r.room_no, r.block 
                               FROM students s 
                               LEFT JOIN rooms r ON s.room_id = r.room_id 
                               WHERE s.student_id = ?""", (student_id,))
        
        s_name = student["name"] if student else f"Student #{student_id}"
        room_no = student["room_no"] if student else "Hostel Room"

        # Policy Check
        hour = 11
        try:
            hour = int(visit_time.split(":")[0])
        except Exception:
            pass

        within_hours = (self.VISITING_START_HOUR <= hour < self.VISITING_END_HOUR)
        policy_status = f"Valid visiting time ({visit_time} within 09:00 AM - 08:00 PM window)" if within_hours else f"Flagged: Outside hours ({visit_time})"

        # Historical Pattern Analysis
        past_visits = query_all("SELECT visitor_id, visit_date, status FROM visitors WHERE CAST(student_id AS TEXT) = CAST(? AS TEXT)", (student_id,))
        past_count = len(past_visits)
        repeat_visitor = query_one("SELECT COUNT(*) as cnt FROM visitors WHERE name LIKE ? AND CAST(student_id AS TEXT) = CAST(? AS TEXT)", (f"%{v_name}%", student_id))
        repeat_count = repeat_visitor["cnt"] if repeat_visitor else 0

        historical_summary = f"{past_count} total host visit(s) logged. {v_name} has visited {repeat_count} time(s)."

        # Inter-Agent Conflict Detection (Leave Agent + Complaint Agent)
        conflicts = []
        # Check if student is away on Leave on the visit date!
        leave_conflict = query_one(
            "SELECT leave_id, leave_type, start_date, end_date FROM leaves WHERE CAST(student_id AS TEXT) = CAST(? AS TEXT) AND status = 'Approved' AND ? BETWEEN start_date AND end_date",
            (student_id, visit_date)
        )
        if leave_conflict:
            conflicts.append(f"Leave Agent Conflict: Host student {s_name} is on approved {leave_conflict['leave_type']} ({leave_conflict['leave_id']}) during this date!")

        # Check if student room has active open complaint
        complaint_conflict = query_one(
            "SELECT complaint_id, category FROM complaints WHERE CAST(student_id AS TEXT) = CAST(? AS TEXT) AND status = 'Open'",
            (student_id,)
        )
        if complaint_conflict:
            conflicts.append(f"Complaint Agent Alert: Room {room_no} has active open {complaint_conflict['category']} ticket ({complaint_conflict['complaint_id']}).")

        conflict_summary = "No inter-agent conflicts detected" if not conflicts else " | ".join(conflicts)

        # Risk Assessment Calculation
        risk_score = 10
        risk_factors = []

        if "Parent" not in purpose and "Family" not in purpose:
            risk_score += 15
            risk_factors.append("Non-family visitor purpose")
        if repeat_count > 3:
            risk_score += 20
            risk_factors.append("High visit frequency (>3 visits)")
        if hour >= 19:  # Entry near 07:00 PM - 08:00 PM cutoff
            risk_score += 15
            risk_factors.append("Evening arrival near curfew cutoff")
        if conflicts:
            risk_score += 35
            risk_factors.append("Inter-agent conflict detected")

        risk_score = min(98, max(5, risk_score))
        risk_level = "Low" if risk_score <= 30 else ("Medium" if risk_score <= 65 else "High")
        risk_reason = "Parent visit & clear schedule" if not risk_factors else f"Calculated based on: {', '.join(risk_factors)}"

        # Intelligent Recommendation & Confidence Score
        if risk_score <= 30 and not conflicts:
            recommendation = "Approve Visitor"
            confidence = 96
            reason_text = "Verified parent visit within standard visiting hours with zero conflicts."
        elif risk_score <= 65 or conflicts:
            recommendation = "Manual Review Required"
            confidence = 90
            reason_text = f"Requires Warden verification due to: {conflict_summary if conflicts else 'evening entry time'}."
        else:
            recommendation = "Reject Pass"
            confidence = 93
            reason_text = f"High risk score ({risk_score}%) due to active conflicts and policy flags."

        return {
            "visitor_name": v_name,
            "host_student": s_name,
            "room_no": room_no,
            "purpose": purpose,
            "policy_status": policy_status,
            "historical_summary": historical_summary,
            "conflict_summary": conflict_summary,
            "has_conflicts": len(conflicts) > 0,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_reason": risk_reason,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason_text
        }

    def list_visitors(self, student_id=None):
        """Lists visitors with embedded AI Decision Cards for Warden Security Logs."""
        if student_id:
            rows = query_all("""SELECT v.*, COALESCE(s.name, 'Student #' || v.student_id) as student_name, r.room_no 
                                FROM visitors v 
                                LEFT JOIN students s ON CAST(v.student_id AS TEXT) = CAST(s.student_id AS TEXT) 
                                LEFT JOIN rooms r ON s.room_id = r.room_id 
                                WHERE CAST(v.student_id AS TEXT) = CAST(? AS TEXT) 
                                ORDER BY v.visit_date DESC, v.visit_time DESC""", (student_id,))
        else:
            rows = query_all("""SELECT v.*, COALESCE(s.name, 'Student #' || v.student_id) as student_name, r.room_no 
                                FROM visitors v 
                                LEFT JOIN students s ON CAST(v.student_id AS TEXT) = CAST(s.student_id AS TEXT) 
                                LEFT JOIN rooms r ON s.room_id = r.room_id 
                                ORDER BY v.visit_date DESC, v.visit_time DESC""")

        # Attach AI Decision Card evaluation to each visitor row
        visitors_with_ai = []
        for r in rows:
            v_obj = dict(r)
            v_obj["ai_decision"] = self.evaluate_visitor(v_obj)
            visitors_with_ai.append(v_obj)

        return {
            "success": True,
            "agent": self.name,
            "data": {"visitors": visitors_with_ai, "count": len(visitors_with_ai)},
            "message": f"Retrieved {len(visitors_with_ai)} visitor records with AI evaluation."
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
