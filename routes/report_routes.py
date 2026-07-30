from flask import Blueprint, request, Response, jsonify
from services.report_service import generate_pdf_report
from utils.logger import logger

report_bp = Blueprint("report_bp", __name__)

@report_bp.route("/api/reports/download-pdf", methods=["GET", "POST"])
def download_pdf():
    """
    Generates and downloads a formatted PDF report based on start_date, end_date, and category.
    Supports GET query parameters or POST JSON payload.
    """
    try:
        if request.method == "POST":
            data = request.get_json() or {}
            start_date = data.get("start_date")
            end_date = data.get("end_date")
            category = data.get("category", "all")
        else:
            start_date = request.args.get("start_date")
            end_date = request.args.get("end_date")
            category = request.args.get("category", "all")

        logger.info(f"Generating PDF Report: Start={start_date}, End={end_date}, Category={category}")

        pdf_bytes = generate_pdf_report(start_date, end_date, category)

        filename = f"SmartHostel_Report_{start_date or 'all'}_to_{end_date or 'today'}.pdf"

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
