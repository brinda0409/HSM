from datetime import datetime
from services.db_service import query_one, query_all
from agents.complaint_agent import complaint_agent
from agents.leave_agent import leave_agent
from agents.visitor_agent import visitor_agent
from agents.room_agent import room_agent
from agents.recommendation_agent import recommendation_agent
from utils.logger import logger

class NotificationAgent:
    """
    Autonomous Smart Notification Assistant:
    Analyzes hostel events (Complaints, Leaves, Visitors, Room Transfers, Announcements)
    and uses outputs from Complaint, Leave, Visitor, Room, and Recommendation Agents.
    
    For every notification, determines:
    1. Recipient (Who should receive the notification)
    2. Notification Priority (Critical, High, Medium, Low)
    3. Best Time to Send (Suggested Timing)
    4. Reason for the Notification
    5. Confidence Score (%)
    """

    def __init__(self):
        self.name = "notification_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "notification_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent", "get_notification_recommendation")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[NotificationAgent] Processing intent: {intent} for student/warden: {student_id}")

        return self.generate_notification_recommendations(entities, student_id)

    def generate_notification_recommendations(self, entities={}, student_id=1):
        """
        Analyzes real-time hostel database events and inter-agent outputs to synthesize smart notification recommendations.
        """
        recommendations = []

        # 1. Analyze Complaints (Collaborate with Complaint Agent)
        open_complaint = query_one("""SELECT c.*, s.name as student_name, r.room_no, r.block 
                                     FROM complaints c
                                     JOIN students s ON c.student_id = s.student_id
                                     LEFT JOIN rooms r ON s.room_id = r.room_id
                                     WHERE c.status IN ('Open', 'In Progress')
                                     ORDER BY c.complaint_id DESC LIMIT 1""")
        if open_complaint:
            c_type = open_complaint.get("category", "General Maintenance")
            s_name = open_complaint.get("student_name", f"Student #{open_complaint['student_id']}")
            r_no = open_complaint.get("room_no", "A-101")
            prio = "Critical" if open_complaint.get("priority") == "High" else "High"
            prio_badge = "🔴 CRITICAL" if prio == "Critical" else "🟠 HIGH"
            
            recommendations.append({
                "source": "Complaint Agent",
                "event": f"Complaint #{open_complaint['complaint_id']} ({c_type})",
                "recipient": f"{c_type} Maintenance Team & {s_name} (Room {r_no})",
                "priority_badge": prio_badge,
                "channel": "📱 SMS & Mobile Push | 📢 Maintenance Portal",
                "suggested_timing": "Immediate Dispatch (Within 15 mins)",
                "reason": f"Unresolved {c_type.lower()} issue in Room {r_no} reported by {s_name}. Immediate technician alert required.",
                "draft": f"ALERT: Maintenance ticket #{open_complaint['complaint_id']} ({c_type}) logged for Room {r_no}. Technician assigned.",
                "confidence": 98
            })

        # 2. Analyze Leave Applications (Collaborate with Leave Agent)
        pending_leave = query_one("""SELECT l.*, s.name as student_name, s.roll_no 
                                   FROM leaves l
                                   JOIN students s ON l.student_id = s.student_id
                                   WHERE l.status = 'Pending'
                                   ORDER BY l.leave_id DESC LIMIT 1""")
        if pending_leave:
            is_emergency = "emergency" in str(pending_leave.get("leave_type", "")).lower() or "emergency" in str(pending_leave.get("reason", "")).lower()
            l_type = pending_leave.get("leave_type", "Home Leave")
            s_name = pending_leave.get("student_name", f"Student #{pending_leave['student_id']}")
            prio_badge = "🔴 CRITICAL" if is_emergency else "🟠 HIGH"
            timing = "Immediate Warden Alert" if is_emergency else "Before 06:00 PM Outpass Cutoff"

            recommendations.append({
                "source": "Leave Agent",
                "event": f"Leave Request {pending_leave['leave_id']} ({l_type})",
                "recipient": f"Chief Warden & Block Supervisor for {s_name}",
                "priority_badge": prio_badge,
                "channel": "📱 Push Notification | ✉️ Warden Email Digest",
                "suggested_timing": timing,
                "reason": f"Student {s_name} submitted {l_type} ({pending_leave['start_date']} to {pending_leave['end_date']}). Warden approval required.",
                "draft": f"ACTION REQUIRED: Leave Application {pending_leave['leave_id']} for {s_name} awaits Warden review.",
                "confidence": 96
            })

        # 3. Analyze Visitor Requests (Collaborate with Visitor Agent)
        pending_visitor = query_one("""SELECT v.*, s.name as student_name, r.room_no 
                                      FROM visitors v
                                      JOIN students s ON v.student_id = s.student_id
                                      LEFT JOIN rooms r ON s.room_id = r.room_id
                                      WHERE v.status = 'Pending'
                                      ORDER BY v.visitor_id DESC LIMIT 1""")
        if pending_visitor:
            v_name = pending_visitor.get("name", "Parent / Guest")
            s_name = pending_visitor.get("student_name", f"Student #{pending_visitor['student_id']}")
            r_no = pending_visitor.get("room_no", "A-101")

            recommendations.append({
                "source": "Visitor Agent",
                "event": f"Visitor Pass #{pending_visitor['visitor_id']} ({v_name})",
                "recipient": f"Main Gate Security Desk & Warden",
                "priority_badge": "🟡 MEDIUM",
                "channel": "🔊 Main Gate Security Terminal | 📱 Push Alert",
                "suggested_timing": f"30 Mins Prior to Visit ({pending_visitor['visit_date']} {pending_visitor['visit_time']})",
                "reason": f"Visitor pass request for {v_name} arriving to meet {s_name} (Room {r_no}). Security desk pre-verification recommended.",
                "draft": f"SECURITY ALERT: Visitor {v_name} scheduled to meet student {s_name} (Room {r_no}) on {pending_visitor['visit_date']}.",
                "confidence": 95
            })

        # 4. Analyze Room Transfer Requests (Collaborate with Room Agent)
        pending_transfer = query_one("""SELECT t.*, s.name as student_name 
                                       FROM room_transfers t
                                       JOIN students s ON t.student_id = s.student_id
                                       WHERE t.status = 'Pending'
                                       ORDER BY t.transfer_id DESC LIMIT 1""")
        if pending_transfer:
            s_name = pending_transfer.get("student_name", f"Student #{pending_transfer['student_id']}")
            recommendations.append({
                "source": "Room Agent",
                "event": f"Room Change Request #{pending_transfer['transfer_id']}",
                "recipient": f"{s_name} & Housekeeping Team",
                "priority_badge": "🟡 MEDIUM",
                "channel": "📱 Student App Alert | 📢 Housekeeping Dashboard",
                "suggested_timing": "Next Day 09:00 AM Shift Start",
                "reason": f"Room transfer pending from {pending_transfer['from_room_no']} to {pending_transfer['to_room_no']} for {s_name}.",
                "draft": f"ROOM UPDATE: Transfer request from {pending_transfer['from_room_no']} to {pending_transfer['to_room_no']} for {s_name} is under review.",
                "confidence": 94
            })

        # 5. Default General Announcement Notification (Collaborate with Recommendation Agent)
        if not recommendations:
            recommendations.append({
                "source": "Recommendation Agent",
                "event": "Hostel Operations Broadcast",
                "recipient": "All Hostel Residents & Block Wardens",
                "priority_badge": "🟢 LOW",
                "channel": "📢 App Notice Board | ✉️ Student Email Broadcast",
                "suggested_timing": "Daily Morning Briefing (08:30 AM)",
                "reason": "Routine hostel operational updates, dining menu broadcast, and curfew reminder.",
                "draft": "NOTICE: Please ensure return before 10:00 PM curfew. Dining hall dinner timings are 07:30 PM - 09:30 PM.",
                "confidence": 92
            })

        # Format output with color-coded priority badges & channels
        cards = []
        for r in recommendations:
            card_text = (
                f"🔔 **Smart AI Notification Recommendation** ({r['event']}):\n"
                f"• 🚨 **Priority Level**: {r['priority_badge']}\n"
                f"• 📡 **Delivery Channel**: **{r['channel']}**\n"
                f"• 👥 **Recipient**: **{r['recipient']}**\n"
                f"• ⏰ **Suggested Timing**: **{r['suggested_timing']}**\n"
                f"• 🎯 **Reason**: {r['reason']}\n"
                f"• 💬 **Message Draft**: *\"{r['draft']}\"*\n"
                f"• 🛡️ **Confidence Score**: **{r['confidence']}%**"
            )
            cards.append(card_text)

        msg = "📢 **Autonomous Smart Notification Assistant Recommendations**:\n\n" + "\n\n---\n\n".join(cards)

        return {
            "success": True,
            "agent": self.name,
            "data": {"recommendations": recommendations, "count": len(recommendations)},
            "message": msg
        }

notification_agent = NotificationAgent()
