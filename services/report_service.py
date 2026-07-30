import io
import datetime
from services.db_service import query_all, query_one
from utils.logger import logger

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    HAS_REPORTLAB = True
except Exception as _re:
    HAS_REPORTLAB = False

def get_report_data(start_date, end_date, category='all'):
    """
    Queries database for records falling between start_date and end_date (inclusive).
    Dates should be string formatted YYYY-MM-DD.
    """
    s_date = start_date if start_date else "2000-01-01"
    e_date = end_date if end_date else "2099-12-31"

    data = {
        "start_date": s_date,
        "end_date": e_date,
        "category": category,
        "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "complaints": [],
        "leaves": [],
        "visitors": [],
        "audit_logs": []
    }

    if category in ['all', 'complaints']:
        q = """
            SELECT c.complaint_id, s.name as student_name, s.roll_no, c.category, c.description, c.priority, c.status, c.created_at
            FROM complaints c
            JOIN students s ON c.student_id = s.student_id
            WHERE DATE(c.created_at) >= DATE(?) AND DATE(c.created_at) <= DATE(?)
            ORDER BY c.created_at DESC
        """
        data["complaints"] = query_all(q, (s_date, e_date))

    if category in ['all', 'leaves']:
        q = """
            SELECT l.leave_id, s.name as student_name, s.roll_no, l.leave_type, l.start_date, l.end_date, l.reason, l.status, l.applied_at
            FROM leaves l
            JOIN students s ON l.student_id = s.student_id
            WHERE DATE(l.applied_at) >= DATE(?) AND DATE(l.applied_at) <= DATE(?)
               OR (l.start_date >= ? AND l.end_date <= ?)
            ORDER BY l.applied_at DESC
        """
        data["leaves"] = query_all(q, (s_date, e_date, s_date, e_date))

    if category in ['all', 'visitors']:
        q = """
            SELECT v.visitor_id, v.name as visitor_name, v.contact, s.name as student_name, v.purpose, v.visit_date, v.visit_time, v.status
            FROM visitors v
            JOIN students s ON v.student_id = s.student_id
            WHERE DATE(v.visit_date) >= DATE(?) AND DATE(v.visit_date) <= DATE(?)
            ORDER BY v.visit_date DESC, v.visit_time DESC
        """
        data["visitors"] = query_all(q, (s_date, e_date))

    if category in ['all', 'audit']:
        q = """
            SELECT cl.log_id, COALESCE(s.name, 'Guest') as student_name, cl.message, cl.detected_intent, cl.agent_invoked, cl.timestamp
            FROM chat_logs cl
            LEFT JOIN students s ON cl.student_id = s.student_id
            WHERE DATE(cl.timestamp) >= DATE(?) AND DATE(cl.timestamp) <= DATE(?)
            ORDER BY cl.timestamp DESC
        """
        data["audit_logs"] = query_all(q, (s_date, e_date))

    return data


def generate_pdf_report(start_date, end_date, category='all'):
    """
    Generates a high-quality PDF report buffer for the given date range and category.
    Returns bytes buffer.
    """
    data = get_report_data(start_date, end_date, category)
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#059669")     # Emerald Green
    SECONDARY = colors.HexColor("#0f172a")   # Dark Navy
    MUTED = colors.HexColor("#64748b")       # Slate Gray
    BG_LIGHT = colors.HexColor("#f8fafc")    # Light background
    BORDER_COLOR = colors.HexColor("#e2e8f0")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=SECONDARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=MUTED,
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=SECONDARY
    )

    body_bold_style = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=SECONDARY
    )

    header_cell_style = ParagraphStyle(
        'TableHeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.white
    )

    story = []

    # Header Header Banner
    story.append(Paragraph("SmartHostel Management System", title_style))
    cat_title = category.upper() if category != 'all' else 'COMPREHENSIVE HOSTEL ACTIVITY'
    story.append(Paragraph(f"Official Audit & Operations Report • <b>{cat_title}</b>", subtitle_style))

    # Meta Info Table (2 Columns)
    meta_data = [
        [
            Paragraph(f"<b>Date Range:</b> {data['start_date']} to {data['end_date']}", body_style),
            Paragraph(f"<b>Generated On:</b> {data['generated_at']}", ParagraphStyle('RightMeta', parent=body_style, alignment=TA_RIGHT))
        ],
        [
            Paragraph(f"<b>Scope:</b> {category.capitalize()} Records", body_style),
            Paragraph(f"<b>Platform:</b> SmartHostel Enterprise Portal", ParagraphStyle('RightMeta2', parent=body_style, alignment=TA_RIGHT))
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # Metric Overview Cards
    total_complaints = len(data['complaints'])
    total_leaves = len(data['leaves'])
    total_visitors = len(data['visitors'])
    total_audits = len(data['audit_logs'])

    stats_data = [
        [
            Paragraph(f"<b>Total Complaints</b><br/><font size=12 color='#059669'><b>{total_complaints}</b></font>", ParagraphStyle('StatC1', parent=body_style, alignment=TA_CENTER)),
            Paragraph(f"<b>Leave Requests</b><br/><font size=12 color='#0284c7'><b>{total_leaves}</b></font>", ParagraphStyle('StatC2', parent=body_style, alignment=TA_CENTER)),
            Paragraph(f"<b>Visitor Gate Passes</b><br/><font size=12 color='#7c3aed'><b>{total_visitors}</b></font>", ParagraphStyle('StatC3', parent=body_style, alignment=TA_CENTER)),
            Paragraph(f"<b>AI Audit Logs</b><br/><font size=12 color='#d97706'><b>{total_audits}</b></font>", ParagraphStyle('StatC4', parent=body_style, alignment=TA_CENTER))
        ]
    ]
    stats_table = Table(stats_data, colWidths=[135, 135, 135, 135])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f1f5f9")),
        ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 14))

    # SECTION 1: Complaints
    if category in ['all', 'complaints']:
        story.append(Paragraph("1. Complaints Summary", section_style))
        if data['complaints']:
            comp_table_data = [[
                Paragraph("ID", header_cell_style),
                Paragraph("Student", header_cell_style),
                Paragraph("Category", header_cell_style),
                Paragraph("Description", header_cell_style),
                Paragraph("Priority", header_cell_style),
                Paragraph("Status", header_cell_style),
                Paragraph("Date", header_cell_style)
            ]]
            for c in data['complaints']:
                comp_table_data.append([
                    Paragraph(str(c.get('complaint_id', '')), body_bold_style),
                    Paragraph(f"{c.get('student_name', '')} ({c.get('roll_no', '')})", body_style),
                    Paragraph(str(c.get('category', '')), body_style),
                    Paragraph(str(c.get('description', '')[:50]) + ("..." if len(str(c.get('description', ''))) > 50 else ""), body_style),
                    Paragraph(str(c.get('priority', '')), body_style),
                    Paragraph(str(c.get('status', '')), body_style),
                    Paragraph(str(c.get('created_at', ''))[:10], body_style),
                ])
            t_comp = Table(comp_table_data, colWidths=[65, 95, 70, 140, 50, 60, 60])
            t_comp.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), PRIMARY),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                ('PADDING', (0,0), (-1,-1), 5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
            ]))
            story.append(t_comp)
        else:
            story.append(Paragraph("<i>No complaint records found in selected date range.</i>", subtitle_style))
        story.append(Spacer(1, 12))

    # SECTION 2: Leave Requests
    if category in ['all', 'leaves']:
        story.append(Paragraph("2. Leave Applications", section_style))
        if data['leaves']:
            leave_table_data = [[
                Paragraph("Leave ID", header_cell_style),
                Paragraph("Student", header_cell_style),
                Paragraph("Type", header_cell_style),
                Paragraph("Start Date", header_cell_style),
                Paragraph("End Date", header_cell_style),
                Paragraph("Reason", header_cell_style),
                Paragraph("Status", header_cell_style)
            ]]
            for l in data['leaves']:
                leave_table_data.append([
                    Paragraph(str(l.get('leave_id', '')), body_bold_style),
                    Paragraph(f"{l.get('student_name', '')} ({l.get('roll_no', '')})", body_style),
                    Paragraph(str(l.get('leave_type', '')), body_style),
                    Paragraph(str(l.get('start_date', '')), body_style),
                    Paragraph(str(l.get('end_date', '')), body_style),
                    Paragraph(str(l.get('reason', '')[:45]) + ("..." if len(str(l.get('reason', ''))) > 45 else ""), body_style),
                    Paragraph(str(l.get('status', '')), body_style),
                ])
            t_leave = Table(leave_table_data, colWidths=[65, 100, 70, 65, 65, 115, 60])
            t_leave.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0284c7")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                ('PADDING', (0,0), (-1,-1), 5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
            ]))
            story.append(t_leave)
        else:
            story.append(Paragraph("<i>No leave records found in selected date range.</i>", subtitle_style))
        story.append(Spacer(1, 12))

    # SECTION 3: Visitor Gate Passes
    if category in ['all', 'visitors']:
        story.append(Paragraph("3. Visitor Security Logs", section_style))
        if data['visitors']:
            vis_table_data = [[
                Paragraph("Visitor Name", header_cell_style),
                Paragraph("Contact", header_cell_style),
                Paragraph("Resident Student", header_cell_style),
                Paragraph("Purpose", header_cell_style),
                Paragraph("Date", header_cell_style),
                Paragraph("Time", header_cell_style),
                Paragraph("Status", header_cell_style)
            ]]
            for v in data['visitors']:
                vis_table_data.append([
                    Paragraph(str(v.get('visitor_name', '')), body_bold_style),
                    Paragraph(str(v.get('contact', '')), body_style),
                    Paragraph(str(v.get('student_name', '')), body_style),
                    Paragraph(str(v.get('purpose', '')[:40]), body_style),
                    Paragraph(str(v.get('visit_date', '')), body_style),
                    Paragraph(str(v.get('visit_time', '')), body_style),
                    Paragraph(str(v.get('status', '')), body_style),
                ])
            t_vis = Table(vis_table_data, colWidths=[90, 75, 95, 110, 65, 50, 55])
            t_vis.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#7c3aed")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                ('PADDING', (0,0), (-1,-1), 5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
            ]))
            story.append(t_vis)
        else:
            story.append(Paragraph("<i>No visitor security logs found in selected date range.</i>", subtitle_style))
        story.append(Spacer(1, 12))

    # SECTION 4: AI Audit Logs
    if category in ['all', 'audit']:
        story.append(Paragraph("4. AI Agent Audit Trail", section_style))
        if data['audit_logs']:
            audit_table_data = [[
                Paragraph("ID", header_cell_style),
                Paragraph("User", header_cell_style),
                Paragraph("Message", header_cell_style),
                Paragraph("Detected Intent", header_cell_style),
                Paragraph("Agent Invoked", header_cell_style),
                Paragraph("Timestamp", header_cell_style)
            ]]
            for a in data['audit_logs']:
                audit_table_data.append([
                    Paragraph(str(a.get('log_id', '')), body_bold_style),
                    Paragraph(str(a.get('student_name', '')), body_style),
                    Paragraph(str(a.get('message', '')[:45]), body_style),
                    Paragraph(str(a.get('detected_intent', '') or 'General'), body_style),
                    Paragraph(str(a.get('agent_invoked', '') or 'DecisionAgent'), body_style),
                    Paragraph(str(a.get('timestamp', ''))[:16], body_style),
                ])
            t_audit = Table(audit_table_data, colWidths=[40, 85, 140, 95, 90, 90])
            t_audit.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#d97706")),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
                ('PADDING', (0,0), (-1,-1), 5),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
            ]))
            story.append(t_audit)
        else:
            story.append(Paragraph("<i>No AI audit logs found in selected date range.</i>", subtitle_style))

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR, spaceAfter=8))
    footer_text = Paragraph(
        "SmartHostel Management System • Automated Audit & Reporting Module • Generated Securely",
        ParagraphStyle('FooterText', parent=subtitle_style, alignment=TA_CENTER, fontSize=8)
    )
    story.append(footer_text)

    # Build PDF
    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value
