from services.db_service import query_one, query_all
from utils.logger import logger

class InfoAgent:
    """
    Hostel Information Agent:
    Answers FAQs strictly from the `hostel_info` database table. Never fabricates information.
    """

    def __init__(self):
        self.name = "info_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "info_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent")
        entities = request_dict.get("entities", {})

        logger.info(f"[InfoAgent] Processing intent: {intent} with entities: {entities}")

        info_key = entities.get("info_key")
        query_term = entities.get("query_term", "")

        return self.get_info(info_key, query_term)

    def get_info(self, info_key=None, query_term=""):
        """
        Queries DB for requested info_key or performs keyword search on category/key/value.
        """
        if info_key:
            row = query_one("SELECT * FROM hostel_info WHERE info_key = ?", (info_key,))
            if row:
                return {
                    "success": True,
                    "agent": self.name,
                    "data": {"title": row["info_key"].replace("_", " ").title(), "category": row["category"], "value": row["value"]},
                    "message": row["value"]
                }

        # Keyword match search in DB
        term_pattern = f"%{query_term}%" if query_term else "%"
        rows = query_all("""SELECT * FROM hostel_info 
                            WHERE info_key LIKE ? OR category LIKE ? OR value LIKE ?""", 
                         (term_pattern, term_pattern, term_pattern))

        if rows:
            combined = "\n\n".join([f"**{r['info_key'].replace('_', ' ').title()}** ({r['category']}): {r['value']}" for r in rows])
            return {
                "success": True,
                "agent": self.name,
                "data": {"results": rows, "title": "Hostel Information Results", "value": combined},
                "message": combined
            }

        # If not found in DB
        logger.warning(f"[InfoAgent] Information not found in database for query: '{query_term}' / key: '{info_key}'")
        return {
            "success": False,
            "agent": self.name,
            "data": {},
            "message": "I could not find official information regarding your query in the hostel database. Please contact the Hostel Administrative Office or your Block Warden for official details."
        }

    def list_all_info(self):
        """Returns all hostel information entries from database."""
        rows = query_all("SELECT * FROM hostel_info ORDER BY category, info_key")
        return {
            "success": True,
            "agent": self.name,
            "data": {"info": rows, "count": len(rows)},
            "message": f"Retrieved {len(rows)} hostel info records."
        }

info_agent = InfoAgent()
