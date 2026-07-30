import os
import unittest
import io
from services.db_service import init_db, query_one, query_all
from agents.complaint_agent import complaint_agent
from agents.visitor_agent import visitor_agent
from agents.room_agent import room_agent
from agents.info_agent import info_agent
from agents.leave_agent import leave_agent
from agents.report_agent import report_agent
from agents.decision_agent import decision_agent
from app import create_app

class TestSHMSSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize database."""
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "hostel.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
        init_db(reset=True)
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
        self.assertEqual(res["data"]["status"], "Pending")

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
        self.assertTrue(r_chat.get_json()["success"])

        # Stats API
        r_stats = self.client.get("/api/dashboard/stats")
        self.assertEqual(r_stats.status_code, 200)
        self.assertIn("open_complaints", r_stats.get_json()["data"])

        # Info API
        r_info = self.client.get("/api/info")
        self.assertEqual(r_info.status_code, 200)

    def test_10_pdf_report_endpoint(self):
        """Test PDF Report generation endpoint."""
        res = self.client.get("/api/reports/download-pdf?start_date=2026-01-01&end_date=2026-12-31&category=all")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/pdf")
        self.assertGreater(len(res.data), 1000)

    def test_11_student_crud_and_csv_upload(self):
        """Test Student CRUD endpoints and CSV Dataset upload."""
        # 1. Create Student
        new_student = {
            "name": "Test Student",
            "roll_no": "2026-TEST-999",
            "email": "test999@hostel.edu",
            "contact": "+91-9999900000",
            "room_id": 1,
            "password": "password123"
        }
        res_create = self.client.post("/api/students", json=new_student)
        self.assertEqual(res_create.status_code, 201)
        st_id = res_create.get_json()["student_id"]

        # 2. Get Student
        res_get = self.client.get(f"/api/students/{st_id}")
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.get_json()["data"]["name"], "Test Student")

        # 3. Update Student
        res_upd = self.client.put(f"/api/students/{st_id}", json={"name": "Updated Test Student", "contact": "+91-8888800000"})
        self.assertEqual(res_upd.status_code, 200)

        # 4. Delete Student
        res_del = self.client.delete(f"/api/students/{st_id}")
        self.assertEqual(res_del.status_code, 200)

        # 5. CSV Dataset Upload
        csv_data = (
            "roll_no,name,email,contact,room_no,password\n"
            "2026-CSV-001,CSV Student One,csv1@hostel.edu,+91-7777711111,A-101,password123\n"
            "2026-CSV-002,CSV Student Two,csv2@hostel.edu,+91-7777722222,A-102,password123\n"
        )
        data = {
            'file': (io.BytesIO(csv_data.encode('utf-8')), 'test_students.csv')
        }
        res_csv = self.client.post('/api/students/upload-csv', data=data, content_type='multipart/form-data')
        self.assertEqual(res_csv.status_code, 200)
        self.assertTrue(res_csv.get_json()["success"])
        self.assertGreaterEqual(res_csv.get_json()["created"], 2)

    def test_12_report_agent(self):
        """Test Report Agent summary compilation and decision routing."""
        req = {
            "intent": "generate_report",
            "entities": {
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
                "category": "all"
            },
            "student_id": 1
        }
        res = report_agent.process_request(req)
        self.assertTrue(res["success"])
        self.assertIn("pdf_download_url", res["data"])

        # Decision Agent delegation test for report intent
        chat_res = decision_agent.process_chat("Generate an administrative report for this week", student_id=1)
        self.assertTrue(chat_res["success"])
        self.assertIn("report_agent", chat_res["agents_invoked"])

    def test_13_warden_copilot_automation(self):
        """Test Warden AI Copilot administrative prompts (batch approval & complaint resolution)."""
        warden_res = decision_agent.process_chat("Approve all pending leave requests", student_id=1)
        self.assertTrue(warden_res["success"])
        self.assertIn("leave_agent", warden_res["agents_invoked"])

        res_res = self.client.post("/api/chat", json={"message": "Resolve complaint CMP-2026-0001", "student_id": 1, "role": "warden"})
        self.assertEqual(res_res.status_code, 200)
        self.assertIn("complaint_agent", res_res.get_json()["agents_invoked"])

    def test_14_room_availability_query(self):
        """Test asking 'how many rooms are available' in chat."""
        r_chat = self.client.post("/api/chat", json={"message": "how many rooms are available", "student_id": 1})
        self.assertEqual(r_chat.status_code, 200)
        self.assertTrue(r_chat.get_json()["success"])
        self.assertIn("room_agent", r_chat.get_json()["agents_invoked"])
        self.assertIn("Room Vacancy Report", r_chat.get_json()["message"])

    def test_15_recommendation_agent(self):
        """Test Recommendation Agent (Agent #7) for student & warden suggestions."""
        r_rec = self.client.post("/api/chat", json={"message": "give me recommendations", "student_id": 1})
        self.assertEqual(r_rec.status_code, 200)
        self.assertTrue(r_rec.get_json()["success"])
        self.assertIn("recommendation_agent", r_rec.get_json()["agents_invoked"])
        self.assertIn("Personalized AI Recommendations", r_rec.get_json()["message"])

if __name__ == "__main__":
    unittest.main()
