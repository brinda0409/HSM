from services.db_service import query_one, query_all, execute_query
from utils.logger import logger

class RoomAgent:
    """
    Room Management Agent:
    Handles room availability checks, room allocations, occupancy tracking, and transfers.
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

        if intent in ["get_room_info", "check_availability", "get_room"]:
            room_no = entities.get("room_no")
            return self.get_room(room_no, student_id)
        elif intent in ["allocate_room"]:
            target_student_id = entities.get("student_id") or student_id
            room_no = entities.get("room_no")
            return self.allocate_room(target_student_id, room_no)
        elif intent in ["transfer_room", "change_room"]:
            target_student_id = entities.get("student_id") or student_id
            to_room_no = entities.get("to_room_no") or entities.get("room_no")
            return self.transfer_room(target_student_id, to_room_no)
        elif intent == "list_rooms":
            return self.list_rooms()
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported room intent: {intent}"
            }

    def get_room(self, room_no=None, student_id=None):
        """Checks details and availability for a specific room or student's current room."""
        if room_no:
            room = query_one("SELECT * FROM rooms WHERE room_no = ? OR room_no = ?", (room_no, room_no.replace("-", "")))
        elif student_id:
            room = query_one("""SELECT r.* FROM rooms r 
                                JOIN students s ON r.room_id = s.room_id 
                                WHERE s.student_id = ?""", (student_id,))
        else:
            room = None

        if room:
            is_available = room["occupied_count"] < room["capacity"] and room["status"] != "Maintenance"
            return {
                "success": True,
                "agent": self.name,
                "data": {
                    "room": room,
                    "is_available": is_available,
                    "available_beds": room["capacity"] - room["occupied_count"]
                },
                "message": f"Room {room['room_no']} ({room['block']}): Capacity {room['capacity']}, Occupied {room['occupied_count']}. Status: {room['status']}."
            }
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Room '{room_no or 'for student ' + str(student_id)}' not found in database."
            }

    def allocate_room(self, student_id, room_no):
        """Allocates a student to a room if capacity permits."""
        room = query_one("SELECT * FROM rooms WHERE room_no = ? OR room_no = ?", (room_no, room_no.replace("-", "")))
        if not room:
            return {"success": False, "agent": self.name, "data": {}, "message": f"Room {room_no} does not exist."}

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

        logger.info(f"[RoomAgent] Student {student_id} allocated to room {room['room_no']}")
        return {
            "success": True,
            "agent": self.name,
            "data": {"student_id": student_id, "room_no": room["room_no"], "block": room["block"]},
            "message": f"Student {student['name']} allocated to Room {room['room_no']} ({room['block']})."
        }

    def transfer_room(self, student_id, to_room_no):
        """Transfers a student from current room to destination room if space is available."""
        if not to_room_no:
            return {"success": False, "agent": self.name, "data": {}, "message": "Destination room number is required for transfer."}
        
        return self.allocate_room(student_id, to_room_no)

    def list_rooms(self):
        """Lists all rooms with occupants."""
        rooms = query_all("SELECT * FROM rooms ORDER BY block, room_no")
        return {
            "success": True,
            "agent": self.name,
            "data": {"rooms": rooms, "count": len(rooms)},
            "message": f"Retrieved {len(rooms)} room records."
        }

room_agent = RoomAgent()
