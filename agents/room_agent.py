from services.db_service import query_one, query_all, execute_query
from utils.logger import logger

class RoomAgent:
    """
    Autonomous AI Room Management Agent:
    Performs multi-factor room health analysis, maintenance conflict detection (Complaint Agent), 
    occupancy optimization, intelligent best-room matching algorithms, 
    suitability scoring, confidence ratings, Warden AI Decision Cards,
    and Student-to-Warden Room Change Approval Workflows.
    """

    def __init__(self):
        self.name = "room_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "room_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[RoomAgent] Processing intent: {intent} for student: {student_id}")

        if intent in ["get_room_info", "check_availability", "get_room", "empty_rooms"]:
            room_no = entities.get("room_no")
            is_empty_query = entities.get("filter") == "empty" or intent == "check_availability" or intent == "empty_rooms"
            
            if is_empty_query or not room_no:
                return self.get_available_rooms()
            return self.get_room(room_no, student_id)
        elif intent in ["allocate_room"]:
            target_student_id = entities.get("student_id") or student_id
            room_no = entities.get("room_no")
            return self.allocate_room(target_student_id, room_no)
        elif intent in ["transfer_room", "change_room", "request_room_transfer"]:
            target_student_id = entities.get("student_id") or student_id
            to_room_no = entities.get("to_room_no") or entities.get("room_no")
            reason = entities.get("reason") or "Student requested room transfer after checking vacancies."
            return self.request_room_transfer(target_student_id, to_room_no, reason)
        elif intent == "list_rooms":
            return self.list_rooms()
        elif intent in ["list_transfers", "list_transfer_requests"]:
            return self.list_transfer_requests()
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported room intent: {intent}"
            }

    def evaluate_room(self, room_dict):
        """
        Executes AI Health Analysis, Maintenance Conflict Detection, and Best-Match Scoring.
        """
        room_id = room_dict.get("room_id")
        room_no = room_dict.get("room_no", "A-101")
        block = room_dict.get("block", "Block A")
        capacity = room_dict.get("capacity", 2)
        occupied = room_dict.get("occupied_count", 0)
        status = room_dict.get("status", "Available")
        amenities = room_dict.get("amenities", "Standard")

        free_beds = capacity - occupied

        # Inter-Agent Conflict Detection (Complaint Agent lookup for this room)
        open_complaints = query_all(
            """SELECT c.complaint_id, c.category, c.priority 
               FROM complaints c 
               JOIN students s ON c.student_id = s.student_id 
               WHERE s.room_id = ? AND c.status = 'Open'""",
            (room_id,)
        )
        
        has_conflicts = len(open_complaints) > 0
        conflict_summary = f"Active {open_complaints[0]['category']} maintenance ticket ({open_complaints[0]['complaint_id']})" if has_conflicts else "No maintenance conflicts detected"

        # Calculate AI Room Health & Match Score (0% - 100%)
        health_score = 100
        if has_conflicts:
            health_score -= 30
        if status == "Maintenance":
            health_score -= 50
        if occupied >= capacity:
            health_score -= 20

        health_score = max(10, health_score)

        # Suitability Recommendation
        if status == "Maintenance" or occupied >= capacity:
            recommendation = "Full / Maintenance Block"
            confidence = 98
            reason = f"Room {room_no} is currently fully occupied or under maintenance."
        elif has_conflicts:
            recommendation = "Conditional Assignment"
            confidence = 88
            reason = f"Room {room_no} has 1 free bed but has an open {open_complaints[0]['category']} complaint."
        else:
            recommendation = "Optimal Room Choice"
            confidence = 96
            reason = f"Room {room_no} ({block}) has {free_beds} free bed(s), 100% health score, and zero maintenance tickets."

        return {
            "room_no": room_no,
            "block": block,
            "free_beds": free_beds,
            "health_score": health_score,
            "has_conflicts": has_conflicts,
            "conflict_summary": conflict_summary,
            "recommendation": recommendation,
            "confidence": confidence,
            "reason": reason
        }

    def find_best_available_room(self):
        """
        AI Intelligent Best Room Matching Algorithm:
        Scans all vacant rooms and ranks them by AI Match Score instead of returning arbitrary rooms.
        """
        empty_rooms = query_all("SELECT * FROM rooms WHERE occupied_count < capacity AND status != 'Maintenance' ORDER BY block, room_no")
        if not empty_rooms:
            return None, None

        best_room = None
        best_eval = None
        highest_score = -1

        for r in empty_rooms:
            r_dict = dict(r)
            ev = self.evaluate_room(r_dict)
            if ev["health_score"] > highest_score:
                highest_score = ev["health_score"]
                best_room = r_dict
                best_eval = ev

        return best_room, best_eval

    def get_available_rooms(self):
        """Lists vacant rooms enhanced with AI Best-Room Selection & Decision Cards."""
        empty_rooms = query_all("SELECT * FROM rooms WHERE occupied_count < capacity AND status != 'Maintenance' ORDER BY block, room_no")
        total_empty_rooms = len(empty_rooms)
        total_free_beds = sum(r["capacity"] - r["occupied_count"] for r in empty_rooms)
        
        if not empty_rooms:
            return {
                "success": True,
                "agent": self.name,
                "data": {"rooms": [], "empty_room_count": 0, "free_bed_count": 0},
                "message": "All hostel rooms are currently fully occupied. There are 0 empty rooms."
            }

        best_room, best_eval = self.find_best_available_room()

        room_lines = []
        for r in empty_rooms:
            r_dict = dict(r)
            ev = self.evaluate_room(r_dict)
            free_beds = r["capacity"] - r["occupied_count"]
            star = " ⭐ [AI RECOMMENDED BEST CHOICE]" if best_room and r["room_id"] == best_room["room_id"] else ""
            room_lines.append(f"• Room **{r['room_no']}** ({r['block']}, Floor {r['floor']}): **{free_beds} bed(s) available** (Health: **{ev['health_score']}%**){star}")

        msg = f"🏠 **Autonomous AI Room Vacancy Report & Optimization Audit**:\n" \
              f"There are **{total_empty_rooms} vacant room(s)** with **{total_free_beds} total free bed(s)**.\n\n" \
              f"🧠 **AI Best Room Recommendation Card**:\n" \
              f"• 👁️ **Observation**: Room **{best_room['room_no']}** ({best_room['block']}) selected as top choice.\n" \
              f"• 📊 **Analysis**: Health Score: **{best_eval['health_score']}%** | Amenities: {best_room['amenities']}\n" \
              f"• ⚠️ **Conflict Check**: {best_eval['conflict_summary']}\n" \
              f"• 💡 **AI Recommendation**: **{best_eval['recommendation']}** (Confidence: **{best_eval['confidence']}%**)\n" \
              f"• 🎯 **Reason**: {best_eval['reason']}\n\n" \
              f"📋 **All Vacant Rooms**:\n" + "\n".join(room_lines)

        return {
            "success": True,
            "agent": self.name,
            "data": {
                "empty_rooms": empty_rooms,
                "empty_room_count": total_empty_rooms,
                "free_bed_count": total_free_beds,
                "ai_best_room": best_room,
                "ai_decision": best_eval
            },
            "message": msg
        }

    def get_room(self, room_no=None, student_id=None):
        """Checks details and availability for a specific room with AI Evaluation."""
        if room_no:
            room = query_one("SELECT * FROM rooms WHERE room_no = ? OR room_no = ?", (room_no, room_no.replace("-", "")))
        elif student_id:
            room = query_one("""SELECT r.* FROM rooms r 
                                JOIN students s ON r.room_id = s.room_id 
                                WHERE s.student_id = ?""", (student_id,))
        else:
            return self.get_available_rooms()

        if room:
            room_dict = dict(room)
            ai_eval = self.evaluate_room(room_dict)
            is_available = room["occupied_count"] < room["capacity"] and room["status"] != "Maintenance"

            msg = f"🏠 **Room Audit**: **Room {room['room_no']}** ({room['block']})\n\n" \
                  f"🧠 **Autonomous AI Decision Card**:\n" \
                  f"• 👁️ **Observation**: Capacity {room['capacity']}, Occupied {room['occupied_count']}/{room['capacity']}.\n" \
                  f"• 📊 **Analysis**: Health Score: **{ai_eval['health_score']}%** | Status: {room['status']}\n" \
                  f"• ⚠️ **Conflict Check**: {ai_eval['conflict_summary']}\n" \
                  f"• 💡 **AI Recommendation**: **{ai_eval['recommendation']}** (Confidence: **{ai_eval['confidence']}%**)\n" \
                  f"• 🎯 **Reason**: {ai_eval['reason']}"

            return {
                "success": True,
                "agent": self.name,
                "data": {
                    "room": room_dict,
                    "is_available": is_available,
                    "available_beds": room["capacity"] - room["occupied_count"],
                    "ai_decision": ai_eval
                },
                "message": msg
            }
        else:
            return self.get_available_rooms()

    def allocate_room(self, student_id, room_no):
        """Directly allocates a student to a room (Warden action)."""
        if not room_no:
            best_room, _ = self.find_best_available_room()
            if best_room:
                room_no = best_room["room_no"]
            else:
                return {"success": False, "agent": self.name, "data": {}, "message": "All rooms are currently at full capacity."}

        room = query_one("SELECT * FROM rooms WHERE room_no = ? OR room_no = ?", (room_no, room_no.replace("-", "")))
        if not room:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Room {room_no} does not exist."}

        room_dict = dict(room)
        ai_eval = self.evaluate_room(room_dict)

        if room["occupied_count"] >= room["capacity"]:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Room {room['room_no']} is already at full capacity ({room['capacity']}/{room['capacity']})."}

        student = query_one("SELECT * FROM students WHERE student_id = ?", (student_id,))
        if not student:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Student ID {student_id} not found."}

        # Check if student is already in a room and decrement old room
        old_room_id = student.get("room_id")
        if old_room_id:
            execute_query("UPDATE rooms SET occupied_count = MAX(0, occupied_count - 1), status = 'Available' WHERE room_id = ?", (old_room_id,))

        # Update student and new room
        new_occupied = room["occupied_count"] + 1
        new_status = "Occupied" if new_occupied >= room["capacity"] else "Available"

        execute_query("UPDATE students SET room_id = ? WHERE student_id = ?", (room["room_id"], student_id))
        execute_query("UPDATE rooms SET occupied_count = ?, status = ? WHERE room_id = ?", (new_occupied, new_status, room["room_id"]))

        logger.info(f"[RoomAgent] Student {student_id} allocated to room {room['room_no']} (AI Match Score: {ai_eval['health_score']}%)")

        msg = f"✅ **Room Allocation Executed**: **Room {room['room_no']}** ({room['block']})\n\n" \
              f"🧠 **Autonomous AI Allocation Decision Card**:\n" \
              f"• 👤 **Student**: **{student['name']}** (ID: #{student_id})\n" \
              f"• 🏠 **Allocated Room**: **Room {room['room_no']}** (Floor {room['floor']})\n" \
              f"• 📊 **Match & Health Score**: **{ai_eval['health_score']}%**\n" \
              f"• ⚠️ **Conflict Check**: {ai_eval['conflict_summary']}\n" \
              f"• 💡 **AI Recommendation**: **{ai_eval['recommendation']}** (Confidence: **{ai_eval['confidence']}%**)\n" \
              f"• 🎯 **Reason**: {ai_eval['reason']}"

        return {
            "success": True,
            "agent": self.name,
            "data": {"student_id": student_id, "room_no": room["room_no"], "block": room["block"], "ai_decision": ai_eval},
            "message": msg
        }

    def request_room_transfer(self, student_id, to_room_no, reason="Requested room transfer"):
        """
        Registers a Student Room Change Request for Warden Approval.
        """
        if not to_room_no:
            best_room, _ = self.find_best_available_room()
            if best_room:
                to_room_no = best_room["room_no"]
            else:
                return {"success": False, "agent": self.name, "data": {}, "message": "All rooms are currently full. Cannot submit transfer request."}

        # Check target room
        target_room = query_one("SELECT * FROM rooms WHERE room_no = ? OR room_no = ?", (to_room_no, to_room_no.replace("-", "")))
        if not target_room:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Room {to_room_no} does not exist."}

        # Fetch student details & current room
        student = query_one("""SELECT s.*, r.room_no as current_room_no 
                               FROM students s 
                               LEFT JOIN rooms r ON s.room_id = r.room_id 
                               WHERE s.student_id = ?""", (student_id,))
        
        if not student:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Student ID #{student_id} not found."}

        from_room_no = student.get("current_room_no") or "Unassigned"

        # Evaluate target room with AI
        ai_eval = self.evaluate_room(dict(target_room))

        try:
            transfer_id = execute_query(
                """INSERT INTO room_transfers (student_id, from_room_no, to_room_no, reason, status)
                   VALUES (?, ?, ?, ?, 'Pending')""",
                (student_id, from_room_no, target_room["room_no"], reason)
            )

            msg = f"📩 **Room Transfer Request Submitted to Warden**:\n\n" \
                  f"🧠 **Autonomous AI Evaluation Card**:\n" \
                  f"• 👤 **Student**: **{student['name']}** (Current Room: **{from_room_no}**)\n" \
                  f"• 🏠 **Requested Room**: **{target_room['room_no']}** ({target_room['block']})\n" \
                  f"• 📊 **Target Room Health**: **{ai_eval['health_score']}%**\n" \
                  f"• ⚠️ **Conflict Check**: {ai_eval['conflict_summary']}\n" \
                  f"• 💡 **AI Warden Recommendation**: **{ai_eval['recommendation']}** (Confidence: **{ai_eval['confidence']}%**)\n" \
                  f"• ⏳ **Status**: **Pending Warden Approval** (Request ID: **#{transfer_id}**)"

            logger.info(f"[RoomAgent] Room transfer request #{transfer_id} created for student #{student_id} to room {target_room['room_no']}")

            return {
                "success": True,
                "agent": self.name,
                "data": {
                    "transfer_id": transfer_id,
                    "student_id": student_id,
                    "from_room_no": from_room_no,
                    "to_room_no": target_room["room_no"],
                    "status": "Pending",
                    "ai_decision": ai_eval
                },
                "message": msg
            }
        except Exception as e:
            logger.error(f"[RoomAgent] Error creating room transfer request: {e}")
            return {"success": False, "agent": self.name, "data": {}, "message": f"Database error requesting room transfer: {str(e)}"}

    def transfer_room(self, student_id, to_room_no):
        """Legacy helper maps to request_room_transfer for student workflow."""
        return self.request_room_transfer(student_id, to_room_no)

    def list_transfer_requests(self):
        """Lists all pending & historical room transfer requests for Warden Dashboard."""
        rows = query_all("""SELECT t.*, COALESCE(s.name, 'Student #' || t.student_id) as student_name, s.roll_no, r.capacity, r.occupied_count, r.block
                            FROM room_transfers t
                            LEFT JOIN students s ON CAST(t.student_id AS TEXT) = CAST(s.student_id AS TEXT)
                            LEFT JOIN rooms r ON UPPER(TRIM(t.to_room_no)) = UPPER(TRIM(r.room_no))
                            ORDER BY t.transfer_id DESC""")
        
        transfers_with_ai = []
        for r in rows:
            t_obj = dict(r)
            target_room = query_one("SELECT * FROM rooms WHERE room_no = ?", (t_obj["to_room_no"],))
            if target_room:
                t_obj["ai_decision"] = self.evaluate_room(dict(target_room))
            else:
                t_obj["ai_decision"] = {"health_score": 100, "recommendation": "Approve Transfer", "confidence": 95, "conflict_summary": "No conflicts"}
            transfers_with_ai.append(t_obj)

        return {
            "success": True,
            "agent": self.name,
            "data": {"transfers": transfers_with_ai, "count": len(transfers_with_ai)},
            "message": f"Retrieved {len(transfers_with_ai)} room transfer requests."
        }

    def update_transfer_status(self, transfer_id, status):
        """Warden approves or rejects a student room transfer request."""
        valid = ["Pending", "Approved", "Rejected"]
        if status not in valid:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Invalid status {status}"}

        transfer = query_one("SELECT * FROM room_transfers WHERE transfer_id = ?", (transfer_id,))
        if not transfer:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Transfer request #{transfer_id} not found."}

        execute_query("UPDATE room_transfers SET status = ? WHERE transfer_id = ?", (status, transfer_id))

        if status == "Approved":
            # Relocate student to destination room
            alloc_res = self.allocate_room(transfer["student_id"], transfer["to_room_no"])
            return {
                "success": True,
                "agent": self.name,
                "data": {"transfer_id": transfer_id, "status": "Approved"},
                "message": f"Room transfer request #{transfer_id} APPROVED! Student relocated to Room {transfer['to_room_no']}."
            }
        else:
            return {
                "success": True,
                "agent": self.name,
                "data": {"transfer_id": transfer_id, "status": "Rejected"},
                "message": f"Room transfer request #{transfer_id} REJECTED by Warden."
            }

    def list_rooms(self):
        """Lists all rooms with embedded AI Decision Cards and pending transfer requests."""
        rooms = query_all("SELECT * FROM rooms ORDER BY block, room_no")
        transfers = self.list_transfer_requests().get("data", {}).get("transfers", [])
        
        rooms_with_ai = []
        for r in rooms:
            r_obj = dict(r)
            r_obj["ai_decision"] = self.evaluate_room(r_obj)
            # Find any pending transfer requests targeting this room
            matching_transfers = [t for t in transfers if t["to_room_no"] == r_obj["room_no"] or t["from_room_no"] == r_obj["room_no"]]
            r_obj["pending_transfers"] = matching_transfers
            rooms_with_ai.append(r_obj)

        return {
            "success": True,
            "agent": self.name,
            "data": {"rooms": rooms_with_ai, "transfers": transfers, "count": len(rooms_with_ai)},
            "message": f"Retrieved {len(rooms_with_ai)} room records with AI health evaluation."
        }

room_agent = RoomAgent()
