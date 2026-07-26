import os
import json
import re
from datetime import datetime, timedelta
from utils.logger import logger

# Try importing google.generativeai
try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        if HAS_GENAI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Primary model gemini-2.0-flash, fallback to gemini-1.5-flash
                for model_name in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        logger.info(f"Gemini API configured successfully using model: {model_name}")
                        break
                    except Exception as me:
                        logger.warning(f"Could not load model {model_name}: {me}")
            except Exception as e:
                logger.error(f"Failed to configure Gemini API: {e}")
                self.model = None
        else:
            logger.info("GEMINI_API_KEY not found or google-generativeai module missing. Running in Heuristic NLU Mode.")

    def parse_intent_and_entities(self, user_message, student_context=None):
        """
        Parses raw user input into structured JSON intent and entities.
        Uses Gemini API if available, else falls back to Heuristic Rule-Based NLP.
        """
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        current_day_name = datetime.now().strftime("%A")

        if self.model:
            try:
                prompt = f"""
You are the Decision Agent for Smart Hostel Management System.
Current System Date: {current_date_str} ({current_day_name}).

Analyze the user's message and return a SINGLE JSON object with the following schema:
{{
  "intents": [
    {{
      "intent": "register_complaint | get_complaint_status | register_visitor | get_room_info | allocate_room | transfer_room | apply_leave | get_leave_status | get_hostel_info | unknown",
      "category": "Electrical | Plumbing | Furniture | Internet | Cleanliness | Other",
      "entities": {{
         // complaint entities: description, category, priority (Low/Medium/High/Urgent)
         // visitor entities: visitor_name, contact, purpose, visit_date (YYYY-MM-DD), visit_time (HH:MM)
         // room entities: room_no, to_room_no
         // leave entities: leave_type, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), reason
         // info entities: info_key, category, query_term
         // complaint status entities: complaint_id
      }}
    }}
  ]
}}

Guidelines for Relative Dates (Current Date is {current_date_str}):
- "today": {current_date_str}
- "tomorrow": {(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")}
- "this weekend": Saturday {(datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)).strftime("%Y-%m-%d")} to Sunday {(datetime.now() + timedelta(days=(6 - datetime.now().weekday()) % 7)).strftime("%Y-%m-%d")}
- "next Monday": {(datetime.now() + timedelta(days=(7 - datetime.now().weekday()) % 7)).strftime("%Y-%m-%d")}

If the message contains MULTIPLE requests (e.g., complaint AND visitor/leave), include multiple items in the "intents" array.

Message: "{user_message}"

Respond ONLY with valid JSON inside ```json ``` block or raw JSON string. Do not add markdown text outside JSON.
"""
                response = self.model.generate_content(prompt)
                raw_text = response.text.strip()
                
                # Extract JSON from markdown block if present
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()

                parsed = json.loads(raw_text)
                if "intents" in parsed and isinstance(parsed["intents"], list) and len(parsed["intents"]) > 0:
                    logger.info(f"Gemini Intent Parsing Success: {parsed['intents']}")
                    return parsed["intents"]
            except Exception as e:
                logger.error(f"Gemini intent parsing failed, falling back to heuristic NLU: {e}")

        # Fallback to Heuristic NLP
        return self._heuristic_parse(user_message, current_date_str)

    def _heuristic_parse(self, user_message, current_date_str):
        """
        Rule-based NLP parser to handle intent and entity extraction reliably when API key is offline/unavailable.
        """
        msg_lower = user_message.lower()
        intents = []

        now = datetime.now()
        tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        # Saturday & Sunday calculation
        saturday = now + timedelta(days=(5 - now.weekday()) % 7)
        sunday = saturday + timedelta(days=1)
        weekend_start = saturday.strftime("%Y-%m-%d")
        weekend_end = sunday.strftime("%Y-%m-%d")

        # 1. Complaint Check
        if any(w in msg_lower for w in ["light", "fan", "ac", "air condition", "water", "tap", "sink", "leak", "door", "bed", "chair", "table", "wifi", "internet", "broken", "not working", "clean", "dirty", "complaint", "repair", "fix"]):
            category = "Other"
            priority = "Medium"

            if any(w in msg_lower for w in ["light", "fan", "ac", "switch", "electricity", "socket", "power"]):
                category = "Electrical"
                if "ac" in msg_lower or "spark" in msg_lower:
                    priority = "High"
            elif any(w in msg_lower for w in ["water", "tap", "sink", "leak", "flush", "toilet", "pipe"]):
                category = "Plumbing"
                priority = "High"
            elif any(w in msg_lower for w in ["wifi", "internet", "network", "router"]):
                category = "Internet"
                priority = "High"
            elif any(w in msg_lower for w in ["bed", "chair", "table", "door", "cupboard", "desk", "window"]):
                category = "Furniture"
            elif any(w in msg_lower for w in ["clean", "dirty", "dustbin", "trash", "garbage"]):
                category = "Cleanliness"

            if any(w in msg_lower for w in ["urgent", "emergency", "fire", "danger", "smoke"]):
                priority = "Urgent"

            intents.append({
                "intent": "register_complaint",
                "category": category,
                "entities": {
                    "description": user_message,
                    "category": category,
                    "priority": priority
                }
            })

        # 2. Leave Check
        if any(w in msg_lower for w in ["leave", "going home", "outpass", "outing", "absence", "absent", "vacation"]):
            leave_type = "Home Leave"
            if "medical" in msg_lower or "doctor" in msg_lower or "sick" in msg_lower:
                leave_type = "Medical"
            elif "outing" in msg_lower or "day out" in msg_lower:
                leave_type = "Outing"
            elif "emergency" in msg_lower:
                leave_type = "Emergency"

            start_d = current_date_str
            end_d = tomorrow_str

            if "weekend" in msg_lower:
                start_d = weekend_start
                end_d = weekend_end
            elif "tomorrow" in msg_lower:
                start_d = tomorrow_str
                end_d = (now + timedelta(days=2)).strftime("%Y-%m-%d")

            intents.append({
                "intent": "apply_leave",
                "entities": {
                    "leave_type": leave_type,
                    "start_date": start_d,
                    "end_date": end_d,
                    "reason": user_message
                }
            })

        # 3. Visitor Check
        if any(w in msg_lower for w in ["visitor", "guest", "parent", "parents", "father", "mother", "friend", "visiting"]):
            v_date = current_date_str
            if "tomorrow" in msg_lower:
                v_date = tomorrow_str
            elif "sunday" in msg_lower:
                v_date = sunday.strftime("%Y-%m-%d")
            elif "saturday" in msg_lower:
                v_date = saturday.strftime("%Y-%m-%d")

            # Extract possible name or relative
            visitor_name = "Parent / Guest"
            if "parents" in msg_lower or "father" in msg_lower or "mother" in msg_lower:
                visitor_name = "Parents"
            elif "friend" in msg_lower:
                visitor_name = "Guest / Friend"

            intents.append({
                "intent": "register_visitor",
                "entities": {
                    "visitor_name": visitor_name,
                    "contact": "+1-555-0000",
                    "purpose": "Personal Visit / Meeting Student",
                    "visit_date": v_date,
                    "visit_time": "11:00"
                }
            })

        # 4. Room Info / Check / Transfer
        room_match = re.search(r'([a-bA-B]-?\d{3})', user_message)
        room_no = room_match.group(1).upper() if room_match else None
        if "-" not in room_no if room_no else False:
            room_no = room_no[0] + "-" + room_no[1:]

        if any(w in msg_lower for w in ["room", "availability", "available", "occupancy", "vacant", "capacity"]):
            if "transfer" in msg_lower or "change room" in msg_lower:
                intents.append({
                    "intent": "transfer_room",
                    "entities": {
                        "to_room_no": room_no or "B-201"
                    }
                })
            else:
                intents.append({
                    "intent": "get_room_info",
                    "entities": {
                        "room_no": room_no or "A-101"
                    }
                })

        # 5. Hostel Info / FAQ Check
        if any(w in msg_lower for w in ["mess", "food", "timing", "timings", "office", "warden", "curfew", "rules", "wifi", "laundry", "contact", "breakfast", "lunch", "dinner"]):
            key = "mess_timings"
            if "office" in msg_lower:
                key = "office_timings"
            elif "rule" in msg_lower or "curfew" in msg_lower or "time limit" in msg_lower:
                key = "curfew_rules"
            elif "visitor" in msg_lower and "hour" in msg_lower:
                key = "visiting_hours"
            elif "warden" in msg_lower or "contact" in msg_lower:
                key = "warden_contact"
            elif "wifi" in msg_lower or "internet" in msg_lower:
                key = "wifi_policy"
            elif "laundry" in msg_lower:
                key = "laundry_schedule"

            intents.append({
                "intent": "get_hostel_info",
                "entities": {
                    "info_key": key,
                    "query_term": user_message
                }
            })

        # If no specific intent found
        if not intents:
            intents.append({
                "intent": "unknown",
                "entities": {}
            })

        logger.info(f"Heuristic Intent Parsing Result: {[i['intent'] for i in intents]}")
        return intents

    def synthesize_response(self, user_message, agent_results):
        """
        Synthesizes a friendly, natural language response based on agent execution outputs.
        """
        if self.model:
            try:
                prompt = f"""
You are the helpful AI Assistant for Smart Hostel Management System.
User asked: "{user_message}"

The internal specialized worker agent(s) performed the following database actions and returned these structured results:
{json.dumps(agent_results, indent=2)}

Task: Write a concise, natural, polite, and reassuring response summarizing the results for the student.
Rules:
- State complaint IDs, leave IDs, visit dates, room details, or timing answers clearly if present in results.
- If an operation failed or requires clarification, explain gently.
- Do not mention internal JSON structure or worker agent names.

Response:
"""
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                logger.error(f"Gemini response synthesis error: {e}")

        # Template-based synthesis fallback
        responses = []
        for res in agent_results:
            agent = res.get("agent")
            success = res.get("success", False)
            data = res.get("data", {})
            msg = res.get("message", "")

            if agent == "complaint_agent":
                if success:
                    responses.append(f"✅ Complaint registered successfully! Reference ID: **{data.get('complaint_id')}**. Priority level set to **{data.get('priority')}** for category **{data.get('category')}**.")
                else:
                    responses.append(f"⚠️ Could not register complaint: {msg}")

            elif agent == "visitor_agent":
                if success:
                    responses.append(f"✅ Visitor **{data.get('name')}** registered for **{data.get('visit_date')}** at **{data.get('visit_time')}**. Status: Approved.")
                else:
                    responses.append(f"⚠️ Visitor registration issue: {msg}")

            elif agent == "room_agent":
                if success:
                    if "room" in data:
                        r = data["room"]
                        responses.append(f"🏠 Room **{r['room_no']}** ({r['block']}, Floor {r['floor']}): Capacity is {r['capacity']}, currently occupied by {r['occupied_count']} student(s). Status: **{r['status']}**.")
                    else:
                        responses.append(f"🏠 {msg}")
                else:
                    responses.append(f"⚠️ Room query issue: {msg}")

            elif agent == "leave_agent":
                if success:
                    responses.append(f"📝 Leave request submitted! Leave ID: **{data.get('leave_id')}** ({data.get('leave_type')}) from **{data.get('start_date')}** to **{data.get('end_date')}**. Status: Pending Warden Approval.")
                else:
                    responses.append(f"⚠️ Leave application error: {msg}")

            elif agent == "info_agent":
                if success:
                    responses.append(f"ℹ️ **{data.get('title', 'Hostel Info')}**:\n{data.get('value')}")
                else:
                    responses.append(f"ℹ️ {msg}")

            elif agent == "decision_agent":
                responses.append(msg)

        return "\n\n".join(responses) if responses else "I have processed your request. How else can I assist you today?"

gemini_service = GeminiService()
