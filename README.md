# Smart Hostel Management System (SHMS) — Agentic AI Edition

A production-quality, full-stack, multi-agent AI-powered hostel management application. Powered by Python Flask, SQLite, and Google Gemini API (with heuristic NLU fallbacks).

---

## 🌟 Key Features

1. **Multi-Agent Architecture**:
   - **Decision Agent (Central Orchestrator)**: Parses intents & entities, delegates to worker agents, merges multi-intent requests, and synthesizes natural responses.
   - **Complaint Management Agent**: Auto-categorizes issues (Electrical, Plumbing, Furniture, Internet, Cleanliness), assigns priority (Low/Medium/High/Urgent), and tracks `CMP-YYYY-NNNN`.
   - **Visitor Management Agent**: Validates visiting hours (09:00 - 20:00) and registers guest visits.
   - **Room Management Agent**: Checks availability, specs, allocates rooms, and handles transfers.
   - **Hostel Information Agent**: Answers FAQs strictly from DB without hallucinating.
   - **Leave Management Agent**: Resolves relative dates ("this weekend", "tomorrow"), validates range logic, and tracks `LV-YYYY-NNNN`.

2. **ChatGPT-Style Student UI**:
   - Modern glassmorphism design.
   - Student switcher to simulate multi-student interactions.
   - Quick prompt test buttons.
   - Typing indicator and real-time response rendering with agent metadata tags.

3. **Warden & Admin Management Dashboard**:
   - Live summary stats: Open Complaints, Pending Leaves, Today's Visitors, Room Occupancy %.
   - Sectioned tabbed management for Complaints, Leaves, Visitors, Rooms, and AI Chat Audit Logs.
   - Inline status updates (Approve/Reject leaves, resolve complaints).

---

## 📁 Directory Structure

```
d:/HSM/
├── agents/                  # The 6 AI Agents
│   ├── decision_agent.py    # Central Orchestrator
│   ├── complaint_agent.py   # Complaint Management Agent
│   ├── visitor_agent.py     # Visitor Management Agent
│   ├── room_agent.py        # Room Management Agent
│   ├── info_agent.py        # Hostel Information Agent
│   └── leave_agent.py       # Leave Management Agent
├── database/                # SQLite database setup & seed scripts
│   ├── schema.sql           # Schema definition for 8 tables
│   ├── seed_data.sql        # Realistic initial data
│   └── init_db.py           # DB initialization script
├── services/                # Backend services
│   ├── db_service.py        # Parameterized SQLite query engine
│   └── gemini_service.py    # Gemini API wrapper + Heuristic NLU fallback
├── routes/                  # Flask REST API endpoints
│   ├── chat_routes.py       # POST /api/chat & GET /api/chat_logs
│   ├── complaint_routes.py  # /api/complaints
│   ├── visitor_routes.py    # /api/visitors
│   ├── room_routes.py       # /api/rooms
│   ├── leave_routes.py      # /api/leaves
│   ├── info_routes.py       # /api/info
│   └── student_routes.py    # /api/students & /api/dashboard/stats
├── static/                  # Styles & Client JavaScript
│   ├── css/                 # Glassmorphic & Dashboard CSS
│   └── js/                  # Chat & Dashboard JS logic
├── templates/               # HTML5 templates
│   ├── index.html           # Chat Interface
│   └── dashboard.html       # Admin Dashboard
├── utils/                   # Logging, error handling & validators
│   ├── logger.py            # Dual console & rotating file logger
│   ├── validators.py        # Input sanitization
│   └── error_handlers.py    # Standardized Flask JSON errors
├── app.py                   # Main Flask application entrypoint
├── requirements.txt         # Dependencies
├── .env.example             # Environment configuration template
└── README.md                # Comprehensive documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- Pip package manager

### 2. Installation
Install project dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Setup (Optional for Gemini LLM)
Copy `.env.example` to `.env` and set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_actual_gemini_api_key
```
*Note: If `GEMINI_API_KEY` is not set, the system automatically uses its embedded Heuristic NLP engine so all features work seamlessly offline!*

### 4. Database Initialization
Initialize and seed the SQLite database:
```bash
python database/init_db.py
```

### 5. Running the Application
Launch the Flask development server:
```bash
python app.py
```

Access the application in your browser:
- **Student Chat Interface**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Warden Admin Dashboard**: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)

---

## 🧪 Verification & Testing

Run the system verification test suite:
```bash
python test_system.py
```
This tests all specialized worker agents, the central orchestrator, multi-intent queries, database transactions, and REST API endpoints.
