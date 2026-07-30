-- Seed Data for Smart Hostel Management System (SHMS)

-- 1. Insert Rooms (11 rooms across Block A, Block B, and Block C)
INSERT OR IGNORE INTO rooms (room_id, room_no, block, floor, capacity, occupied_count, status, amenities) VALUES
(1, 'A-101', 'Block A', 1, 2, 2, 'Occupied', 'AC, Study Desks, Attached Bathroom, High-speed Wi-Fi'),
(2, 'A-102', 'Block A', 1, 2, 2, 'Occupied', 'AC, Study Desks, Attached Bathroom, High-speed Wi-Fi'),
(3, 'A-103', 'Block A', 1, 2, 1, 'Available', 'Non-AC, Study Desks, Shared Bathroom, Wi-Fi'),
(4, 'A-201', 'Block A', 2, 2, 2, 'Occupied', 'AC, Balcony, Attached Bathroom, Wi-Fi'),
(5, 'A-202', 'Block A', 2, 2, 0, 'Available', 'AC, Balcony, Attached Bathroom, Wi-Fi'),
(6, 'B-101', 'Block B', 1, 2, 2, 'Occupied', 'Non-AC, Study Desks, Attached Bathroom, Wi-Fi'),
(7, 'B-102', 'Block B', 1, 2, 1, 'Available', 'Non-AC, Study Desks, Attached Bathroom, Wi-Fi'),
(8, 'B-201', 'Block B', 2, 2, 0, 'Available', 'AC, Study Desks, Attached Bathroom, Wi-Fi'),
(9, 'B-202', 'Block B', 2, 2, 0, 'Available', 'AC, Study Desks, Attached Bathroom, Wi-Fi'),
(10, 'B-203', 'Block B', 2, 2, 0, 'Available', 'AC, Study Desks, Attached Bathroom, Wi-Fi'),
(11, 'C-101', 'Block C', 1, 2, 1, 'Available', 'AC, Study Desks, Attached Bathroom, Wi-Fi');

-- 2. Insert Students (with different blocks & rooms for test accounts)
-- Alex Johnson: Block A, Room A-101
-- Arjun Verma: Block B, Room B-101
-- Priya Patel: Block C, Room C-101
INSERT OR IGNORE INTO students (student_id, name, roll_no, room_id, contact, email, password) VALUES
(1, 'Alex Johnson', 'CS2024-001', 1, '+1-555-0101', 'alex.j@hostel.edu', 'password123'),
(2, 'Rahul Sharma', 'CS2024-002', 1, '+1-555-0102', 'rahul.s@hostel.edu', 'password123'),
(3, 'Priya Patel', 'EC2024-015', 11, '+1-555-0103', 'priya.p@hostel.edu', 'password123'),
(4, 'Sneha Gupta', 'EC2024-016', 2, '+1-555-0104', 'sneha.g@hostel.edu', 'password123'),
(5, 'David Chen', 'ME2024-042', 3, '+1-555-0105', 'david.c@hostel.edu', 'password123'),
(6, 'Michael Brown', 'EE2024-008', 4, '+1-555-0106', 'michael.b@hostel.edu', 'password123'),
(7, 'Emily Davis', 'EE2024-009', 4, '+1-555-0107', 'emily.d@hostel.edu', 'password123'),
(8, 'Arjun Verma', 'CS2024-088', 6, '+1-555-0108', 'arjun.v@hostel.edu', 'password123'),
(9, 'Karan Malhotra', 'CS2024-089', 6, '+1-555-0109', 'karan.m@hostel.edu', 'password123'),
(10, 'Ananya Sen', 'EC2024-099', 7, '+1-555-0110', 'ananya.s@hostel.edu', 'password123'),
(11, 'Siddharth Rao', 'CS2024-101', 5, '+1-555-0111', 'siddharth.r@hostel.edu', 'password123'),
(12, 'Rohan Kapoor', 'ME2024-102', 5, '+1-555-0112', 'rohan.k@hostel.edu', 'password123'),
(13, 'Kavya Reddy', 'EC2024-103', 7, '+1-555-0113', 'kavya.r@hostel.edu', 'password123'),
(14, 'Vikram Singh', 'CS2024-104', 8, '+1-555-0114', 'vikram.s@hostel.edu', 'password123'),
(15, 'Aditi Nair', 'EE2024-105', 8, '+1-555-0115', 'aditi.n@hostel.edu', 'password123'),
(16, 'Nikhil Joshi', 'ME2024-106', 9, '+1-555-0116', 'nikhil.j@hostel.edu', 'password123'),
(17, 'Tarun Verma', 'CS2024-107', 9, '+1-555-0117', 'tarun.v@hostel.edu', 'password123'),
(18, 'Pooja Sharma', 'EC2024-108', 10, '+1-555-0118', 'pooja.s@hostel.edu', 'password123'),
(19, 'Rishi Kumar', 'EE2024-109', 10, '+1-555-0119', 'rishi.k@hostel.edu', 'password123'),
(20, 'Meera Deshmukh', 'CS2024-110', 11, '+1-555-0120', 'meera.d@hostel.edu', 'password123');

-- 3. Insert Wardens (with warden@hostel.edu / password123 credentials)
INSERT OR IGNORE INTO wardens (warden_id, name, contact, email, password, block_assigned, office_hours) VALUES
(1, 'Dr. Robert Vance', '+1-555-9001', 'warden@hostel.edu', 'password123', 'Block A & B', '09:00 AM - 05:00 PM (Mon-Sat)'),
(2, 'Prof. Sarah Jenkins', '+1-555-9002', 'sarah.j@hostel.edu', 'password123', 'Block C', '09:00 AM - 05:00 PM (Mon-Sat)');

-- 4. Insert Hostel Information (FAQs, Rules, Timings)
INSERT OR IGNORE INTO hostel_info (info_key, category, value) VALUES
('mess_timings', 'Mess', 'Breakfast: 07:30 AM - 09:30 AM | Lunch: 12:30 PM - 02:30 PM | Snacks: 05:00 PM - 06:00 PM | Dinner: 07:30 PM - 09:30 PM'),
('office_timings', 'Office', 'Hostel Administrative Office is open Monday to Saturday from 09:00 AM to 05:00 PM. Closed on Sundays and Public Holidays.'),
('visiting_hours', 'Visitors', 'Visiting hours for guests/parents are from 09:00 AM to 08:00 PM daily. Visitors must register at the reception gate.'),
('curfew_rules', 'Rules', 'Night curfew is 10:00 PM daily. All students must be inside their respective blocks by 10:00 PM unless prior out-pass approval is granted.'),
('warden_contact', 'Contact', 'Block A Warden: Dr. Robert Vance (+1-555-9001) | Block B Warden: Prof. Sarah Jenkins (+1-555-9002)'),
('wifi_policy', 'Facilities', 'High-speed Wi-Fi is available 24/7. Bandwidth limit per student is 100 GB/month. Support desk: wifi-help@hostel.edu'),
('laundry_schedule', 'Facilities', 'Laundry collection is available on Mondays and Thursdays between 08:00 AM and 11:00 AM at the basement laundry desk.'),
('emergency_contact', 'Contact', 'Hostel Emergency Control Room: +1-555-9999 (Available 24/7) | Medical Center: +1-555-8888');

-- 5. Insert Initial Complaints
INSERT OR IGNORE INTO complaints (complaint_id, student_id, category, description, priority, status, created_at) VALUES
('CMP-2026-0001', 1, 'Electrical', 'Ceiling light flickers continuously in Room A-101.', 'Medium', 'Open', '2026-07-24 10:15:00'),
('CMP-2026-0002', 3, 'Plumbing', 'Water leaking from bathroom sink pipe in Room C-101.', 'High', 'In Progress', '2026-07-25 08:30:00'),
('CMP-2026-0003', 8, 'Internet', 'Wi-Fi router down on 1st Floor Block B.', 'Urgent', 'Open', '2026-07-26 09:00:00');

-- 6. Insert Initial Visitors
INSERT OR IGNORE INTO visitors (visitor_id, student_id, name, contact, purpose, visit_date, visit_time, status) VALUES
(1, 1, 'Richard Johnson', '+1-555-4321', 'Parent Visit', '2026-07-27', '11:00', 'Approved'),
(2, 5, 'Marcus Vance', '+1-555-8765', 'Academic Project Collaboration', '2026-07-26', '15:30', 'Approved');

-- 7. Insert Initial Leaves
INSERT OR IGNORE INTO leaves (leave_id, student_id, leave_type, start_date, end_date, reason, status, applied_at) VALUES
('LV-2026-0001', 2, 'Home Leave', '2026-08-01', '2026-08-05', 'Family function at hometown', 'Approved', '2026-07-22 14:00:00'),
('LV-2026-0002', 4, 'Medical', '2026-07-28', '2026-07-30', 'Dental treatment appointment', 'Pending', '2026-07-25 16:45:00');

-- 8. Insert Initial Chat Logs
INSERT OR IGNORE INTO chat_logs (log_id, student_id, message, detected_intent, agent_invoked, response, timestamp) VALUES
(1, 1, 'My ceiling light flickers', 'register_complaint', 'complaint_agent', 'I have logged your Electrical complaint (CMP-2026-0001) for Room A-101. Priority: Medium.', '2026-07-24 10:15:00');
