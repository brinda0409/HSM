from services.db_service import query_one, query_all
from utils.logger import logger

class RecommendationAgent:
    """
    Recommendation Agent (Agent #7):
    Provides personalized suggestions, proactive reminders, room transfer advice 
    based on complaint history, and administrative recommendations for Wardens.
    """

    def __init__(self):
        self.name = "recommendation_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to multi-agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int, "role": str}
        :return: {"success": bool, "agent": "recommendation_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent", "get_recommendations")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)
        role = request_dict.get("role", "student")

        logger.info(f"[RecommendationAgent] Processing intent: {intent} for student: {student_id}, role: {role}")

        if role == "warden" or intent in ["get_warden_recommendations", "warden_suggestions"]:
            return self.get_warden_recommendations()
        else:
            return self.get_student_recommendations(student_id)

    def get_student_recommendations(self, student_id=1):
        """Generates personalized AI recommendations and reminders for a student."""
        # 1. Fetch student info
        student = query_one("""SELECT s.*, r.room_no, r.block 
                               FROM students s 
                               LEFT JOIN rooms r ON s.room_id = r.room_id 
                               WHERE s.student_id = ?""", (student_id,))
        s_name = student["name"] if student else "Student"
        room_no = student["room_no"] if student else "A-101"

        # 2. Analyze complaint history
        complaints = query_all("SELECT * FROM complaints WHERE student_id = ? ORDER BY created_at DESC", (student_id,))
        
        category_counts = {}
        for c in complaints:
            cat = c.get("category", "Other")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        recommendations = []
        reminders = []

        # Complaint-driven Smart Recommendations
        if category_counts.get("Internet", 0) >= 1 or category_counts.get("Wi-Fi", 0) >= 1:
            vacant_rooms = query_all("SELECT * FROM rooms WHERE occupied_count < capacity AND status = 'Available' ORDER BY block, room_no")
            suggested_room = vacant_rooms[0]["room_no"] if vacant_rooms else "Room A-104"
            recommendations.append(f"📡 **Wi-Fi Connectivity Alert**: You have logged issues regarding Wi-Fi in {room_no}. **Suggested**: Request a room transfer to **{suggested_room}** (Block A) which features high-speed dual-band mesh coverage.")
        
        if category_counts.get("Plumbing", 0) >= 1 or category_counts.get("Electrical", 0) >= 1:
            recommendations.append(f"🔧 **Maintenance Follow-up**: Priority repair is active for your room **{room_no}**. **Suggested**: Contact Warden office if technician visit is needed during specific hours.")

        if not recommendations:
            vacant_rooms = query_all("SELECT * FROM rooms WHERE occupied_count < capacity ORDER BY room_no")
            target_room = vacant_rooms[0]["room_no"] if vacant_rooms else "Room B-201"
            recommendations.append(f"💡 **Room Optimization**: Your current room **{room_no}** is in good standing. **Suggested**: Explore quiet study zone rooms like **{target_room}** if preparing for exams.")

        # Timings & Schedule Reminders
        reminders.append("🍽️ **Mess Timing Notice**: Dinner starts at **7:00 PM** today (7:00 PM - 9:00 PM). *Tip: Submit a late mess pass if arriving after 8:30 PM.*")
        reminders.append("🚪 **Curfew Alert**: Night curfew is enforced at **10:00 PM**. Ensure leave / outpass is approved if staying out late.")
        reminders.append("📅 **Upcoming Outpass Planning**: Long weekend ahead! Apply for Home Leave 24 hours in advance for quick Warden approval.")

        full_message = f"🌟 **Personalized AI Recommendations for {s_name}**:\n\n"
        full_message += "### 💡 Smart Suggestions:\n" + "\n".join([f"• {r}" for r in recommendations]) + "\n\n"
        full_message += "### ⏰ Active Reminders:\n" + "\n".join([f"• {rm}" for rm in reminders])

        return {
            "success": True,
            "agent": self.name,
            "data": {
                "student_id": student_id,
                "recommendations": recommendations,
                "reminders": reminders,
                "frequent_issue": max(category_counts, key=category_counts.get) if category_counts else None
            },
            "message": full_message
        }

    def get_warden_recommendations(self):
        """Generates administrative AI recommendations and insights for the Warden."""
        # 1. Fetch pending leaves count
        pending_leaves = query_all("SELECT * FROM leaves WHERE status = 'Pending'")
        pending_complaints = query_all("SELECT * FROM complaints WHERE status = 'Pending'")
        maintenance_rooms = query_all("SELECT * FROM rooms WHERE status = 'Maintenance'")

        warden_suggestions = []
        warden_reminders = []

        if len(pending_leaves) > 0:
            warden_suggestions.append(f"📋 **Batch Leave Approvals**: You have **{len(pending_leaves)} pending leave request(s)** awaiting review. **Action Suggested**: Say *'Approve all pending leave requests'* to auto-approve.")
        else:
            warden_suggestions.append("✅ **Leave Queue Clear**: All student leave applications are currently processed.")

        if len(pending_complaints) > 0:
            warden_suggestions.append(f"🔧 **Maintenance Audit**: **{len(pending_complaints)} open complaint(s)** pending resolution. **Action Suggested**: Review Block A plumbing & internet tickets.")

        warden_reminders.append("📊 **Weekly Audit Report**: Export this week's administrative PDF audit report before Friday 5:00 PM.")
        warden_reminders.append("🚪 **Visiting Hours Notice**: Evening visitor entry closes at **07:00 PM**.")

        full_message = "🛡️ **Warden Executive AI Recommendations**:\n\n"
        full_message += "### ⚡ Recommended Actions:\n" + "\n".join([f"• {s}" for s in warden_suggestions]) + "\n\n"
        full_message += "### 📌 Operational Reminders:\n" + "\n".join([f"• {r}" for r in warden_reminders])

        return {
            "success": True,
            "agent": self.name,
            "data": {
                "pending_leaves_count": len(pending_leaves),
                "pending_complaints_count": len(pending_complaints),
                "recommendations": warden_suggestions,
                "reminders": warden_reminders
            },
            "message": full_message
        }

recommendation_agent = RecommendationAgent()
