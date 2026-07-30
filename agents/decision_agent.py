from services.gemini_service import gemini_service
from services.db_service import execute_query
from agents.complaint_agent import complaint_agent
from agents.visitor_agent import visitor_agent
from agents.room_agent import room_agent
from agents.hostel_information_agent import hostel_information_agent
from agents.leave_agent import leave_agent
from utils.logger import logger

class DecisionAgent:
    """
    Decision Agent (Central Orchestrator):
    - Parses intent & entities from raw student messages via Gemini / Heuristic NLU.
    - Routes requests to specialized worker agents (Complaint, Visitor, Room, Info, Leave).
    - Merges results for compound / multi-intent requests.
    - Synthesizes friendly natural language response.
    - Logs execution audit trail in `chat_logs`.
    """

    def __init__(self):
        self.name = "decision_agent"
        self.worker_map = {
            "register_complaint": complaint_agent,
            "get_complaint_status": complaint_agent,
            "list_complaints": complaint_agent,

            "register_visitor": visitor_agent,
            "list_visitors": visitor_agent,

            "get_room_info": room_agent,
            "allocate_room": room_agent,
            "transfer_room": room_agent,
            "list_rooms": room_agent,

            "get_hostel_info": hostel_information_agent,

            "apply_leave": leave_agent,
            "get_leave_status": leave_agent,
            "list_leaves": leave_agent
        }

    def process_chat(self, user_message, student_id=1):
        """
        Orchestrates full chat pipeline end-to-end.
        
        :param user_message: raw string typed by student
        :param student_id: int student ID
        :return: dict response containing final natural message and execution metadata
        """
        logger.info(f"[DecisionAgent] Processing message from student {student_id}: '{user_message}'")

        if not user_message or not user_message.strip():
            return {
                "success": False,
                "message": "Please enter a valid message.",
                "agents_invoked": [],
                "detected_intents": []
            }

        # Step 1: Intent & Entity Parsing
        parsed_intents = gemini_service.parse_intent_and_entities(user_message)

        agents_invoked = []
        agent_results = []
        detected_intent_names = []

        # Step 2: Route to specialized agents
        for intent_item in parsed_intents:
            intent_name = intent_item.get("intent", "unknown")
            entities = intent_item.get("entities", {})
            detected_intent_names.append(intent_name)

            if intent_name == "unknown":
                clarifying_res = {
                    "success": True,
                    "agent": "decision_agent",
                    "data": {},
                    "message": "I'm not quite sure what you'd like to do. You can ask me about raising complaints, applying for leave, registering visitors, checking room status, or hostel mess/curfew timings!"
                }
                agent_results.append(clarifying_res)
                agents_invoked.append("decision_agent")
            else:
                target_agent = self.worker_map.get(intent_name)
                if target_agent:
                    worker_req = {
                        "intent": intent_name,
                        "entities": entities,
                        "student_id": student_id
                    }
                    logger.info(f"[DecisionAgent] Delegating to {target_agent.name} with intent '{intent_name}'")
                    res = target_agent.process_request(worker_req)
                    agent_results.append(res)
                    if target_agent.name not in agents_invoked:
                        agents_invoked.append(target_agent.name)
                else:
                    logger.warning(f"[DecisionAgent] Unmapped intent '{intent_name}'")

        # Step 3: Response Synthesis
        final_response_text = gemini_service.synthesize_response(user_message, agent_results)

        # Step 4: Audit Logging into Database `chat_logs`
        try:
            execute_query(
                """INSERT INTO chat_logs (student_id, message, detected_intent, agent_invoked, response)
                   VALUES (?, ?, ?, ?, ?)""",
                (student_id, user_message, ",".join(detected_intent_names), ",".join(agents_invoked), final_response_text)
            )
        except Exception as e:
            logger.error(f"[DecisionAgent] Failed to log chat to DB: {e}")

        logger.info(f"[DecisionAgent] Orchestration complete. Invoked agents: {agents_invoked}")

        return {
            "success": True,
            "message": final_response_text,
            "detected_intents": detected_intent_names,
            "agents_invoked": agents_invoked,
            "agent_results": agent_results,
            "student_id": student_id
        }

decision_agent = DecisionAgent()
