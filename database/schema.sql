-- Smart Hostel Management System (SHMS) Database Schema

PRAGMA foreign_keys = ON;

-- 1. Rooms Table
CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_no TEXT NOT NULL UNIQUE,
    block TEXT NOT NULL,
    floor INTEGER NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 2,
    occupied_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Available', -- Available, Occupied, Maintenance
    amenities TEXT DEFAULT 'AC, Study Desk, Attached Bathroom, Wi-Fi'
);

-- 2. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT NOT NULL UNIQUE,
    room_id INTEGER,
    contact TEXT NOT NULL,
    email TEXT NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE SET NULL
);

-- 3. Wardens Table
CREATE TABLE IF NOT EXISTS wardens (
    warden_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    block_assigned TEXT NOT NULL,
    office_hours TEXT NOT NULL
);

-- 4. Complaints Table
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id TEXT PRIMARY KEY, -- CMP-YYYY-NNNN
    student_id INTEGER NOT NULL,
    category TEXT NOT NULL, -- Electrical, Plumbing, Furniture, Internet, Cleanliness, Other
    description TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'Medium', -- Low, Medium, High, Urgent
    status TEXT NOT NULL DEFAULT 'Open', -- Open, In Progress, Resolved, Closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- 5. Visitors Table
CREATE TABLE IF NOT EXISTS visitors (
    visitor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    purpose TEXT NOT NULL,
    visit_date TEXT NOT NULL, -- YYYY-MM-DD
    visit_time TEXT NOT NULL, -- HH:MM
    status TEXT NOT NULL DEFAULT 'Approved', -- Approved, Rejected, Completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- 6. Leaves Table
CREATE TABLE IF NOT EXISTS leaves (
    leave_id TEXT PRIMARY KEY, -- LV-YYYY-NNNN
    student_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL DEFAULT 'Home Leave', -- Home Leave, Emergency, Outing, Medical
    start_date TEXT NOT NULL, -- YYYY-MM-DD
    end_date TEXT NOT NULL, -- YYYY-MM-DD
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending', -- Pending, Approved, Rejected
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- 7. Hostel Info Table (FAQs, Rules, Timings)
CREATE TABLE IF NOT EXISTS hostel_info (
    info_key TEXT PRIMARY KEY,
    category TEXT NOT NULL, -- Mess, Timings, Rules, Contact, Facilities
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Chat Logs Table
CREATE TABLE IF NOT EXISTS chat_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    message TEXT NOT NULL,
    detected_intent TEXT,
    agent_invoked TEXT,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE SET NULL
);
