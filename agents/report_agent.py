from datetime import datetime, timedelta
from services.report_service import get_report_data
from utils.validators import parse_date
from utils.logger import logger

class ReportAgent:
    """
    Report Generation Agent:
    Handles administrative report generation, statistical metrics compilation, 
    date-filtered audit summaries, and downloadable PDF report generation.
    """

    def __init__(self):
        self.name = "report_agent"

    def process_request(self, request_dict):
        """
        Main entrypoint adhering to agent contract.
        
        :param request_dict: {"intent": str, "entities": dict, "student_id": int}
        :return: {"success": bool, "agent": "report_agent", "data": dict, "message": str}
        """
        intent = request_dict.get("intent", "generate_report")
        entities = request_dict.get("entities", {})
        student_id = request_dict.get("student_id", 1)

        logger.info(f"[ReportAgent] Processing intent: {intent} for student/warden: {student_id}")

        if intent in ["generate_report", "get_report_summary", "export_pdf_report", "get_report"]:
            return self.generate_report_summary(entities)
        else:
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Unsupported report intent: {intent}"
            }

    def generate_report_summary(self, entities):
        """
        Compiles summary metrics for complaints, leaves, visitors, and generates PDF download link.
        """
        raw_start = entities.get("start_date")
        raw_end = entities.get("end_date")
        category = entities.get("category", "all")

        now = datetime.now()
        start_date = parse_date(raw_start) or (now - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = parse_date(raw_end) or now.strftime("%Y-%m-%d")

        try:
            report_data = get_report_data(start_date, end_date, category)
            
            complaint_count = len(report_data.get("complaints", []))
            leave_count = len(report_data.get("leaves", []))
            visitor_count = len(report_data.get("visitors", []))

            # Generate direct PDF download endpoint URL
            pdf_download_url = f"/api/reports/download-pdf?start_date={start_date}&end_date={end_date}&category={category}"

            summary_info = {
                "start_date": start_date,
                "end_date": end_date,
                "category": category,
                "complaint_count": complaint_count,
                "leave_count": leave_count,
                "visitor_count": visitor_count,
                "pdf_download_url": pdf_download_url,
                "generated_at": now.strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"[ReportAgent] Report compiled successfully for period {start_date} to {end_date}")
            return {
                "success": True,
                "agent": self.name,
                "data": summary_info,
                "message": (
                    f"Report generated for period **{start_date}** to **{end_date}** (Category: **{category}**).\n"
                    f"📊 **Summary**: {complaint_count} Complaints, {leave_count} Leave Applications, {visitor_count} Visitor Passes registered.\n"
                    f"📄 [Click here to Download PDF Audit Report]({pdf_download_url})"
                )
            }
        except Exception as e:
            logger.error(f"[ReportAgent] Failed to generate report: {e}")
            return {
                "success": False,
                "agent": self.name,
                "data": {},
                "message": f"Error generating report: {str(e)}"
            }

report_agent = ReportAgent()
