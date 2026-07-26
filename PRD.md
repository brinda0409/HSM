# Product Requirements Document (PRD)
## Smart Hostel Management System — Agentic AI Edition

**Version:** 1.0
**Author:** AI Solutions Architecture Team
**Date:** July 26, 2026
**Status:** Draft — Ready for Development (Google Antigravity build)

---

## 1. Executive Summary

The Smart Hostel Management System (SHMS) is a multi-agent, AI-orchestrated web application that automates core hostel administrative workflows — complaints, visitor management, room allocation, leave applications, and general hostel information — through a single natural-language chat interface. The system is powered by six purpose-built AI agents coordinated by a central **Decision Agent**, built on Python Flask, SQLite, and the Google Gemini API, and is designed to be fully implementable within one day using Google Antigravity. SHMS demonstrates a production-representative agentic AI architecture suitable for a hackathon submission or final-year engineering capstone, while remaining modular enough to extend into a real deployable product.

---

## 2. Background

Hostel administration in most educational institutions still relies on manual registers, physical complaint boxes, WhatsApp groups, or disconnected form-based portals. This creates friction for students (who must learn different processes for different needs) and for wardens/admin staff (who must manually triage, categorize, and respond to requests). Recent advances in LLM-based agentic systems — where an orchestrating agent can interpret intent and delegate execution to specialized sub-agents — make it possible to unify all these workflows behind one conversational interface without sacrificing the structure and reliability of a traditional database-backed system.

---

## 3. Problem Statement

Hostels lack a unified, intelligent, and conversational system to manage day-to-day student needs. Existing systems are either:
- Purely manual (registers, notice boards, in-person requests), or
- Digitized but form-heavy and disconnected (separate portals for complaints, leave, visitors), or
- Chatbots that only answer FAQs without performing real actions or state changes.

There is no system that combines **natural language understanding**, **intelligent task routing**, and **actual transactional execution** (creating records, updating occupancy, tracking status) in one coherent experience.

---

## 4. Project Objectives

1. Deliver a single conversational entry point for all hostel-related student requests.
2. Implement a true multi-agent architecture with clear separation between orchestration (Decision Agent) and execution (five specialized agents).
3. Automate complaint intake, categorization, prioritization, and status tracking.
4. Digitize visitor registration with rule-based validation.
5. Provide real-time room availability, allocation, and transfer handling.
6. Automate leave application, validation, and approval tracking.
7. Provide instant, accurate answers to hostel FAQs grounded in structured data (not hallucinated).
8. Provide a warden/admin dashboard for oversight of all agent-generated records.
9. Ensure the system is buildable end-to-end within a single day using Google Antigravity, with clean, modular, well-commented, production-quality code.

---

## 5. Scope

### In Scope
- Conversational chat interface (ChatGPT-style) for students
- Six AI agents: Decision, Complaint, Visitor, Room, Hostel Information, Leave
- REST API layer (Flask) covering all agent operations
- SQLite database with full schema for students, rooms, complaints, visitors, leaves, hostel info, wardens, chat logs
- Admin/warden dashboard for viewing and managing records
- Gemini-based intent detection and natural language response generation
- Basic logging and error handling across all layers
- Responsive frontend (desktop + mobile)

### Out of Scope (v1)
- Payment/fee processing
- Real push notifications (SMS/email/WebSocket)
- Multi-hostel / multi-campus support
- Native mobile applications
- Role-based authentication with full user management (v1 assumes a simplified/mock login)
- Voice input or image-based complaint submission

---

## 6. Target Users

| User Type | Description | Primary Needs |
|---|---|---|
| **Student** | Hostel resident | Raise complaints, apply leave, check room info, register visitors, get quick answers |
| **Warden** | Hostel supervisory staff | View/manage complaints, approve/reject leave, monitor visitor logs, oversee room occupancy |
| **Admin** | Hostel administration/back office | System-wide visibility into all records, room allocation oversight, reporting |

---

## 7. Functional Requirements

### FR-1: Conversational Interface
- FR-1.1 The system shall provide a chat-based UI where students can type free-text requests.
- FR-1.2 The system shall display conversation history within a session.
- FR-1.3 The system shall render agent responses in natural, readable language within 3–5 seconds under normal load.

### FR-2: Decision Agent
- FR-2.1 The system shall parse every incoming message and classify it into one of the defined intents (complaint, visitor, room, leave, info, or multi-intent).
- FR-2.2 The system shall extract structured entities relevant to the detected intent (e.g., room number, dates, category keywords).
- FR-2.3 The system shall route the request to the correct specialized agent(s) based on detected intent.
- FR-2.4 The system shall support multi-intent messages by invoking multiple agents and merging their results into a single coherent response.
- FR-2.5 The system shall gracefully handle unrecognized or ambiguous intents by asking a clarifying question rather than failing silently.
- FR-2.6 The system shall log every interaction (input, detected intent, agent(s) invoked, output, timestamp).

### FR-3: Complaint Management Agent
- FR-3.1 The system shall allow students to register a complaint via chat or a direct form.
- FR-3.2 The system shall automatically categorize each complaint (Electrical, Plumbing, Furniture, Internet, Cleanliness, Other).
- FR-3.3 The system shall assign a priority level (Low, Medium, High, Urgent) based on category and keyword analysis.
- FR-3.4 The system shall generate a unique, human-readable complaint ID (format: `CMP-YYYY-NNNN`).
- FR-3.5 The system shall allow students to query the status of a complaint by ID or by asking naturally ("What's the status of my complaint?").
- FR-3.6 The system shall support status transitions: Open → In Progress → Resolved → Closed, updatable by wardens via the dashboard.

### FR-4: Visitor Management Agent
- FR-4.1 The system shall allow students to register an upcoming visitor via chat, capturing name, contact, purpose, and visit date/time.
- FR-4.2 The system shall validate visitor details (non-empty name, valid phone format, valid future date).
- FR-4.3 The system shall check the requested visit time/date against configured hostel visiting rules (e.g., permitted hours) and warn or reject if outside policy.
- FR-4.4 The system shall persist visitor records linked to the hosting student.
- FR-4.5 The system shall allow wardens to view all visitor logs on the dashboard, filterable by date.

### FR-5: Room Management Agent
- FR-5.1 The system shall allow students to check the availability of a specific room by number.
- FR-5.2 The system shall retrieve full room details (block, floor, capacity, current occupancy, amenities) on request.
- FR-5.3 The system shall support room allocation requests, validating remaining capacity before confirming.
- FR-5.4 The system shall update the `occupied_count` and `status` fields of the `rooms` table on every allocation, vacancy, or transfer.
- FR-5.5 The system shall support room transfer requests, validating that the destination room has available capacity before approving.

### FR-6: Hostel Information Agent
- FR-6.1 The system shall answer FAQ-style queries (hostel rules, mess timings, office timings, warden contact) using data stored in the `hostel_info` table.
- FR-6.2 The system shall not fabricate information not present in the database; if a queried key doesn't exist, it shall respond that the information is unavailable and suggest contacting the warden.
- FR-6.3 The system shall allow admins to update `hostel_info` entries via the dashboard or a seed/config file.

### FR-7: Leave Management Agent
- FR-7.1 The system shall allow students to apply for leave via natural language, extracting leave type, start date, end date, and reason.
- FR-7.2 The system shall validate leave requests for logical date ranges (end date ≥ start date) and minimum notice period (configurable, default 1 day).
- FR-7.3 The system shall generate a unique leave ID (format: `LV-YYYY-NNNN`) and default status `Pending`.
- FR-7.4 The system shall allow wardens to approve or reject leave requests via the dashboard, updating status to `Approved` or `Rejected`.
- FR-7.5 The system shall allow students to query their leave history and current leave status via chat.

### FR-8: Dashboard
- FR-8.1 The system shall provide a warden/admin dashboard displaying live counts and lists of complaints, visitors, leave requests, and room occupancy.
- FR-8.2 The dashboard shall allow status updates for complaints and leave requests.
- FR-8.3 The dashboard shall be accessible via a distinct route (`/dashboard`) separate from the student chat interface.

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Performance** | Chat response time under 5 seconds for 95% of requests under normal load |
| **Scalability** | Modular agent design must allow adding new agents without modifying existing agent code |
| **Reliability** | All agent actions must be atomic — a failed DB write must not leave partial state |
| **Maintainability** | Code must be organized by clear separation of concerns (routes / agents / services / models); all functions documented with docstrings |
| **Usability** | UI must be intuitive enough for a first-time student user with no onboarding |
| **Portability** | Must run locally with `python app.py` with no external services beyond the Gemini API |
| **Logging** | All agent invocations, errors, and API requests must be logged with timestamps and severity levels |
| **Error Handling** | All API endpoints must return structured JSON errors with appropriate HTTP status codes (400/404/500) |
| **Responsiveness** | UI must render correctly on screens from 320px (mobile) to 1920px (desktop) |
| **Security** | Basic input sanitization on all endpoints; no raw SQL string interpolation (parameterized queries only) |
| **Data Integrity** | Foreign key constraints enforced between students, rooms, complaints, visitors, and leaves |

---

## 9. User Stories

| ID | As a... | I want to... | So that... |
|---|---|---|---|
| US-1 | Student | type a complaint in plain language | I don't have to fill out a rigid form |
| US-2 | Student | know my complaint's priority and ID | I can track it later |
| US-3 | Student | tell the system my parents are visiting | the visit is logged without visiting the warden's office |
| US-4 | Student | check if a specific room has availability | I can decide about a transfer request |
| US-5 | Student | apply for leave by just describing my plan | I don't need to know exact leave form fields |
| US-6 | Student | ask about mess timings anytime | I don't need to check a notice board |
| Warden | Warden | see all open complaints sorted by priority | I can act on urgent issues first |
| US-8 | Warden | approve or reject leave requests from a dashboard | I don't need to track requests manually |
| US-9 | Admin | view real-time room occupancy | I can plan allocations for new students |
| US-10 | Student | ask a request that spans two needs (e.g., complaint + visitor) in one message | I don't need to send multiple separate messages |

---

## 10. Acceptance Criteria (Sample)

**US-1 / US-2 — Complaint Registration**
- Given a student sends a message describing a hostel issue,
- When the Decision Agent detects a complaint intent,
- Then the Complaint Agent creates a new record with a unique ID, correct category, and assigned priority,
- And the chat response includes the complaint ID, category, and priority.

**US-5 — Leave Application**
- Given a student requests leave with relative dates ("this weekend"),
- When the Decision Agent resolves the relative date expression to absolute dates,
- Then the Leave Agent validates and stores the leave request with status `Pending`,
- And the response confirms the resolved date range and leave ID.

**US-10 — Multi-Intent Handling**
- Given a student message contains two distinct actionable requests,
- When the Decision Agent detects both intents,
- Then both corresponding agents execute independently,
- And the final response addresses both outcomes in a single coherent reply.

---

## 11. System Architecture

### 11.1 High-Level Architecture

```
Frontend (HTML/CSS/JS)
        │  REST/JSON
        ▼
Flask API Layer (routes/*.py)
        │
        ▼
Decision Agent (agents/decision_agent.py)
   │ calls Gemini for intent detection
   │ routes to specialized agent(s)
        │
   ┌────┼─────┬─────────┬──────────┬───────────┐
   ▼    ▼     ▼         ▼          ▼           ▼
Complaint Visitor   Room       Leave       Info
 Agent    Agent     Agent      Agent       Agent
   │       │         │          │           │
   └───────┴─────────┴──────────┴───────────┘
                    │
                    ▼
          SQLite Database (hostel.db)
```

### 11.2 Agent Communication Pattern

- Communication between the Decision Agent and specialized agents is **in-process function calls** (not network calls), using a standardized request/response contract:

```python
# Standard request to a specialized agent
{
  "intent": "register_complaint",
  "entities": {"room_no": "B-203", "description": "light not working"},
  "student_id": 42
}

# Standard response from a specialized agent
{
  "success": true,
  "agent": "complaint_agent",
  "data": {"complaint_id": "CMP-2026-0012", "category": "Electrical", "priority": "Medium", "status": "Open"},
  "message": null
}
```

- This contract keeps agents independently unit-testable and allows the Decision Agent to aggregate multiple agent responses uniformly.

### 11.3 Sequence Diagram (Text Form) — Single-Intent Request

```
Student → Frontend: types message
Frontend → Flask (/api/chat): POST {message, student_id}
Flask → DecisionAgent: process(message, student_id)
DecisionAgent → Gemini: detect_intent(message)
Gemini → DecisionAgent: {intent, entities}
DecisionAgent → SpecializedAgent: execute(entities)
SpecializedAgent → DB: query/insert/update
DB → SpecializedAgent: result
SpecializedAgent → DecisionAgent: structured response
DecisionAgent → Gemini: generate_natural_reply(structured response)
Gemini → DecisionAgent: reply text
DecisionAgent → Flask: {reply, agent_used, data}
Flask → Frontend: JSON response
Frontend → Student: renders chat bubble
```

---

## 12. Database Design

### 12.1 Entity Relationship Overview

```
students (1) ───< (M) complaints
students (1) ───< (M) visitors
students (1) ───< (M) leaves
students (M) >─── (1) rooms
rooms (1) ───< (M) students
wardens (1) ───< (M) rooms   [block_assigned]
```

### 12.2 Table Definitions

```sql
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    roll_no TEXT UNIQUE NOT NULL,
    room_id INTEGER,
    contact TEXT NOT NULL,
    email TEXT,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_no TEXT UNIQUE NOT NULL,
    block TEXT NOT NULL,
    floor INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    occupied_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'Available',   -- Available / Full / Maintenance
    amenities TEXT
);

CREATE TABLE complaints (
    complaint_id TEXT PRIMARY KEY,     -- e.g., CMP-2026-0001
    student_id INTEGER NOT NULL,
    category TEXT NOT NULL,            -- Electrical, Plumbing, Furniture, Internet, Cleanliness, Other
    description TEXT NOT NULL,
    priority TEXT NOT NULL,            -- Low, Medium, High, Urgent
    status TEXT DEFAULT 'Open',        -- Open, In Progress, Resolved, Closed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE visitors (
    visitor_id TEXT PRIMARY KEY,       -- e.g., VIS-2026-0001
    student_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    purpose TEXT,
    visit_date DATE NOT NULL,
    visit_time TEXT,
    status TEXT DEFAULT 'Registered',  -- Registered, Checked-In, Checked-Out, Rejected
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE leaves (
    leave_id TEXT PRIMARY KEY,         -- e.g., LV-2026-0001
    student_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,          -- Home, Medical, Personal, Other
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'Pending',     -- Pending, Approved, Rejected
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);

CREATE TABLE hostel_info (
    info_key TEXT PRIMARY KEY,         -- e.g., 'mess_timing_breakfast', 'curfew_time'
    category TEXT NOT NULL,            -- rules, mess, office, warden
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wardens (
    warden_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    block_assigned TEXT,
    office_hours TEXT
);

CREATE TABLE chat_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    message TEXT NOT NULL,
    detected_intent TEXT,
    agent_invoked TEXT,
    response TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id)
);
```

---

## 13. API Design

### 13.1 `POST /api/chat`
**Request:**
```json
{ "student_id": 42, "message": "My room light is not working." }
```
**Response:**
```json
{
  "success": true,
  "agent_used": ["complaint_agent"],
  "reply": "I've logged your complaint (ID: CMP-2026-0012) under Electrical issues with Medium priority.",
  "data": {"complaint_id": "CMP-2026-0012", "category": "Electrical", "priority": "Medium"}
}
```

### 13.2 Complaint Endpoints
- `POST /api/complaints` → create complaint directly `{student_id, description}`
- `GET /api/complaints/<complaint_id>` → returns full complaint record
- `GET /api/complaints?status=Open` → list/filter complaints
- `PUT /api/complaints/<complaint_id>/status` → warden updates status

### 13.3 Visitor Endpoints
- `POST /api/visitors` → `{student_id, name, contact, purpose, visit_date, visit_time}`
- `GET /api/visitors?date=2026-08-01` → list visitors for a date

### 13.4 Room Endpoints
- `GET /api/rooms/<room_no>` → room details + availability
- `POST /api/rooms/allocate` → `{student_id, room_no}`
- `POST /api/rooms/transfer` → `{student_id, from_room, to_room}`

### 13.5 Leave Endpoints
- `POST /api/leaves` → `{student_id, leave_type, start_date, end_date, reason}`
- `GET /api/leaves/<student_id>` → leave history
- `PUT /api/leaves/<leave_id>/status` → `{status: "Approved"}`

### 13.6 Info Endpoints
- `GET /api/info` → all hostel info entries grouped by category
- `GET /api/info/<key>` → single entry (e.g., `mess_timing_breakfast`)

All endpoints return standardized error responses:
```json
{ "success": false, "error": "ROOM_NOT_FOUND", "message": "Room B-999 does not exist." }
```

---

## 14. UI/UX Requirements

- **Chat Interface (`/`)**: ChatGPT-style layout — message bubbles (user right-aligned, agent left-aligned), typing indicator while waiting for a response, timestamp per message, persistent scroll-to-latest behavior.
- **Dashboard (`/dashboard`)**: Card-based summary (Open Complaints, Pending Leaves, Today's Visitors, Room Occupancy %), with tabbed or sectioned tables for detailed records and inline status-update controls.
- **Design language**: Clean, modern, minimal — rounded cards, soft shadows, a calm primary color palette, clear typographic hierarchy.
- **Responsiveness**: Single-column chat on mobile; dashboard collapses tables into stacked cards below 768px width.
- **Accessibility**: Sufficient color contrast, readable font sizes (minimum 14px body text), keyboard-navigable form controls.
- **Feedback states**: Loading indicators for agent processing, clear success/error toasts for dashboard actions.

---

## 15. Security Requirements

- All database queries must use parameterized statements (no string-concatenated SQL) to prevent SQL injection.
- API keys (Gemini) must be loaded from environment variables, never hardcoded or committed to source control.
- Input validation on every endpoint (type checks, length limits, date format validation).
- Basic rate-limiting consideration on `/api/chat` to prevent abuse (documented as a v1.1 enhancement if not implemented in the hackathon build).
- CORS configuration restricted to the application's own frontend origin.
- Error messages returned to the client must not leak stack traces or internal system details.
- Dashboard actions (status updates) should, at minimum, be gated behind a simple warden/admin identifier even in the simplified v1 auth model.

---

## 16. Assumptions

- A single hostel/block is managed per deployment instance (multi-hostel support is future scope).
- Students are pre-seeded in the database (self-registration is out of scope for v1).
- The Gemini API key provided will have sufficient quota for hackathon/demo-level usage.
- Relative date expressions ("tomorrow," "this weekend") are resolved server-side using the system's current date.
- Development and demo will run on a single local machine/server (no distributed deployment needed for v1).

---

## 17. Constraints

- Must be built using the specified stack only: HTML/CSS/JS frontend, Python Flask backend, SQLite database, Google Gemini API, developed via Google Antigravity.
- Must be completable within a one-day build window.
- No paid third-party services beyond the Gemini API.
- SQLite's single-writer limitation means the system is not designed for high-concurrency production traffic in v1 — acceptable for hackathon/demo scope.

---

## 18. Future Scope

- Migrate from SQLite to PostgreSQL/MySQL for multi-instance, high-concurrency deployment.
- Add a Fee Management Agent and Mess Feedback Agent as new specialized agents.
- Introduce JWT-based authentication with distinct student/warden/admin roles.
- Real-time updates via WebSockets for dashboard and chat notifications.
- Image-based complaint submission with Gemini Vision for automatic visual categorization.
- Agent-to-agent negotiation capability (e.g., automated room-swap matching between two students).
- Analytics agent for predictive maintenance and occupancy forecasting.

---

## 19. How the Six Agents Collaborate (Summary)

The **Decision Agent** is the only agent exposed to the user. It performs three jobs for every request: **understand**, **route**, **respond**. It never executes hostel business logic itself — that is always delegated to one of the five specialized agents (Complaint, Visitor, Room, Leave, Information), each of which owns a distinct table (or set of tables) and a distinct set of business rules. For single-domain requests, the Decision Agent makes one call and relays one result. For compound requests, it identifies multiple intents, invokes each relevant agent in sequence, collects their independent structured outputs, and synthesizes them into a single natural-language reply — this fan-out/fan-in coordination pattern is what distinguishes SHMS as a genuine **agentic AI system** rather than a single-purpose chatbot.
