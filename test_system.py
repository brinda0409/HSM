import os
import unittest
from services.db_service import init_db, query_one, query_all
from agents.complaint_agent import complaint_agent
from agents.visitor_agent import visitor_agent
from agents.room_agent import room_agent
from agents.info_agent import info_agent
from agents.leave_agent import leave_agent
from agents.decision_agent import decision_agent
from app import create_app

class TestSHMSSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize database."""
        init_db()
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_database_seeding(self):
        """Test database table creation and seed data."""
        rooms = query_all("SELECT * FROM rooms")
        students = query_all("SELECT * FROM students")
        info = query_all("SELECT * FROM hostel_info")
        self.assertGreaterEqual(len(rooms), 10, "Should have at least 10 rooms seeded.")
        self.assertGreaterEqual(len(students), 10, "Should have at least 10 students seeded.")
        self.assertGreaterEqual(len(info), 5, "Should have hostel info seeded.")

    def test_02_complaint_agent(self):
        """Test complaint registration and status updating."""
        req = {
            "intent": "register_complaint",
            "entities": {
                "description": "Bathroom pipe leaking water in A-101",
                "category": "Plumbing"
            },
            "student_id": 1
        }
        res = complaint_agent.process_request(req)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["category"], "Plumbing")
        self.assertTrue(res["data"]["complaint_id"].startswith("CMP-"))

        # Update status
        upd = complaint_agent.update_status(res["data"]["complaint_id"], "Resolved")
        self.assertTrue(upd["success"])

    def test_03_visitor_agent(self):
        """Test visitor registration and visiting hours validation."""
        req = {
            "intent": "register_visitor",
            "entities": {
                "visitor_name": "Marcus Vance",
                "contact": "+1-555-9988",
                "purpose": "Book discussion",
                "visit_date": "2026-08-01",
                "visit_time": "14:00"
            },
            "student_id": 1
        }
        res = visitor_agent.process_request(req)
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["status"], "Approved")

    def test_04_room_agent(self):
        """Test room availability query and transfer."""
        res = room_agent.get_room(room_no="A-101")
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["room"]["room_no"], "A-101")

        # Test transfer
        tr_res = room_agent.transfer_room(student_id=5, to_room_no="B-201")
        self.assertTrue(tr_res["success"])

    def test_05_info_agent(self):
        """Test hostel information lookup."""
        res = info_agent.get_info(info_key="mess_timings")
        self.assertTrue(res["success"])
        self.assertIn("Breakfast", res["data"]["value"])

    def test_06_leave_agent(self):
        """Test leave application and approval."""
        req = {
            "intent": "apply_leave",
            "entities": {
                "leave_type": "Home Leave",
                "start_date": "2026-08-10",
                "end_date": "2026-08-15",
                "reason": "Family event"
            },
            "student_id": 2
        }
        res = leave_agent.process_request(req)
        self.assertTrue(res["success"])
        self.assertTrue(res["data"]["leave_id"].startswith("LV-"))

    def test_07_decision_agent_single_intent(self):
        """Test Decision Agent parsing single intent natural text."""
        res = decision_agent.process_chat("My room light is not working.", student_id=1)
        self.assertTrue(res["success"])
        self.assertIn("complaint_agent", res["agents_invoked"])

    def test_08_decision_agent_multi_intent(self):
        """Test Decision Agent parsing compound/multi-intent input."""
        res = decision_agent.process_chat("My AC is broken and my parents are visiting Sunday.", student_id=1)
        self.assertTrue(res["success"])
        self.assertIn("complaint_agent", res["agents_invoked"])
        self.assertIn("visitor_agent", res["agents_invoked"])

    def test_09_rest_api_endpoints(self):
        """Test REST API routes via Flask client."""
        # Chat API
        r_chat = self.client.post("/api/chat", json={"message": "What are today's mess timings?", "student_id": 1})
        self.assertEqual(r_chat.status_code, 200)
        self.assertTrue(r_chat.json["success"])

        # Stats API
        r_stats = self.client.get("/api/dashboard/stats")
        self.assertEqual(r_stats.status_code, 200)
        self.assertIn("open_complaints", r_stats.json["data"])

        # Info API
        r_info = self.client.get("/api/info")
        self.assertEqual(r_info.status_code, 200)

if __name__ == "__main__":
    unittest.main()
