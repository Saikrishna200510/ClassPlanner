"""
ClassPlanner - PDF Exporter
Generates formal, printable timetable and workload reports using ReportLab.
"""

import os
from typing import List, Dict, Any, Optional
from reportlab.lib.pagesizes import letter, landscape, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.lib.units import inch
from datetime import datetime


class PDFExporter:
    """Exports college timetables and reports to professional PDF documents."""

    def __init__(self, institution_name: str = "Government Engineering College",
                 institution_address: str = "College Campus, University Road",
                 academic_year: str = "2026-2027"):
        self.institution_name = institution_name
        self.institution_address = institution_address
        self.academic_year = academic_year

    def export_timetable_grid(
        self,
        output_path: str,
        title: str,
        subtitle: str,
        days: List[str],
        time_slots: List[Dict[str, Any]],
        grid_data: Dict[Tuple[str, int], Dict[str, Any]],
        notes: str = ""
    ) -> str:
        """
        Exports a single timetable grid (Section, Faculty, or Classroom).
        Orientation: Landscape A4 / Letter.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20
        )

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            alignment=1,  # Center
            textColor=colors.HexColor("#1A2B4C"),
            spaceAfter=2
        )
        sub_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            alignment=1,
            textColor=colors.HexColor("#4A4A4A"),
            spaceAfter=6
        )
        meta_style = ParagraphStyle(
            "DocMeta",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            alignment=1,
            textColor=colors.HexColor("#0D47A1"),
            spaceAfter=10
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            alignment=1,
            textColor=colors.HexColor("#000000"),
            fontName="Helvetica-Bold"
        )
        cell_sub = ParagraphStyle(
            "CellSub",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
            alignment=1,
            textColor=colors.HexColor("#333333")
        )
        cell_dim = ParagraphStyle(
            "CellDim",
            parent=styles["Normal"],
            fontSize=7,
            leading=8.5,
            alignment=1,
            textColor=colors.HexColor("#555555")
        )
        break_style = ParagraphStyle(
            "BreakStyle",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            alignment=1,
            textColor=colors.HexColor("#424242"),
            fontName="Helvetica-Bold"
        )

        # Header elements
        elements.append(Paragraph(self.institution_name, title_style))
        elements.append(Paragraph(f"{self.institution_address} | Academic Year: {self.academic_year}", sub_style))
        elements.append(Paragraph(f"<b>{title}</b> — {subtitle}", meta_style))

        # Build Table Data
        # Header Row: [ "Period / Time", "Monday", "Tuesday", ... ]
        header_row = ["Time / Period"] + days
        table_data = [[Paragraph(f"<b>{col}</b>", cell_bold) for col in header_row]]

        table_styles = [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0E4E8")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#808080")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]

        row_idx = 1
        for slot in time_slots:
            s_num = slot["slot_number"]
            s_name = slot["slot_name"]
            s_time = f"{slot['start_time']} - {slot['end_time']}"
            is_break = bool(slot.get("is_break"))

            if is_break:
                # Merge across all columns for breaks (Tea, Lunch)
                break_text = f"*** {s_name.upper()} ({s_time}) ***"
                row_cells = [Paragraph(f"<b>{s_name}</b><br/>{s_time}", cell_bold)]
                for _ in days:
                    row_cells.append(Paragraph(break_text, break_style))

                table_data.append(row_cells)
                table_styles.append(("SPAN", (1, row_idx), (len(days), row_idx)))
                table_styles.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#F2F2F2")))
            else:
                row_cells = [Paragraph(f"<b>{s_name}</b><br/>{s_time}", cell_bold)]
                for day in days:
                    entry = grid_data.get((day, s_num))
                    if entry:
                        sub_text = entry.get("subject_code", "") or entry.get("subject_name", "")
                        sub_name = entry.get("subject_name", "")
                        fac_name = entry.get("faculty_name", "")
                        room_no = entry.get("room_number", "")
                        sec_name = entry.get("section_name", "")

                        # Show content depending on view
                        parts = []
                        parts.append(f"<b>{sub_text}</b>")
                        if sec_name and sec_name not in title:
                            parts.append(f"Sec: {sec_name}")
                        if fac_name and fac_name not in subtitle:
                            parts.append(f"Fac: {fac_name}")
                        if room_no and room_no not in subtitle:
                            parts.append(f"Room: {room_no}")

                        cell_content = "<br/>".join(parts)
                        row_cells.append(Paragraph(cell_content, cell_sub))
                    else:
                        row_cells.append(Paragraph("<font color='#888888'>- Free -</font>", cell_dim))

                table_data.append(row_cells)

            row_idx += 1

        # Calculate column widths
        page_width = 841.89 - 40  # A4 Landscape width minus margins
        time_col_w = 95
        day_col_w = (page_width - time_col_w) / max(1, len(days))
        col_widths = [time_col_w] + [day_col_w] * len(days)

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle(table_styles))
        elements.append(t)

        elements.append(Spacer(1, 25))

        # Signatures block
        sig_data = [
            [
                Paragraph("<b>Prepared by:</b><br/>Timetable Coordinator", cell_bold),
                Paragraph("<b>Verified by:</b><br/>Head of Department (HOD)", cell_bold),
                Paragraph("<b>Approved by:</b><br/>Principal / Dean", cell_bold),
                Paragraph(f"<b>Generated:</b><br/>{datetime.now().strftime('%d-%b-%Y %I:%M %p')}", cell_bold)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[page_width / 4.0] * 4)
        sig_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#AAAAAA")),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(KeepTogether(sig_table))

        doc.build(elements)
        return output_path

    def export_workload_report(
        self,
        output_path: str,
        faculty_workload_data: List[Dict[str, Any]]
    ) -> str:
        """
        Exports faculty workload summary report.
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "RepTitle",
            parent=styles["Heading1"],
            fontSize=15,
            alignment=1,
            textColor=colors.HexColor("#1A2B4C"),
            spaceAfter=3
        )
        meta_style = ParagraphStyle(
            "RepMeta",
            parent=styles["Normal"],
            fontSize=10,
            alignment=1,
            textColor=colors.HexColor("#555555"),
            spaceAfter=15
        )
        cell_bold = ParagraphStyle("CB", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", alignment=1)
        cell_norm = ParagraphStyle("CN", parent=styles["Normal"], fontSize=8.5, alignment=0)
        cell_center = ParagraphStyle("CC", parent=styles["Normal"], fontSize=8.5, alignment=1)

        elements.append(Paragraph(self.institution_name, title_style))
        elements.append(Paragraph(f"<b>FACULTY TEACHING WORKLOAD REPORT</b> | Academic Year: {self.academic_year}", meta_style))

        headers = ["Faculty ID", "Faculty Name", "Department", "Designation", "Assigned Hrs", "Max Limit", "Utilization %"]
        table_data = [[Paragraph(f"<b>{h}</b>", cell_bold) for h in headers]]

        for item in faculty_workload_data:
            assigned = item.get("assigned_hours", 0)
            max_h = item.get("max_hours", 18)
            pct = round((assigned / max(1, max_h)) * 100, 1)

            pct_color = "#007A00" if pct <= 100 else "#D32F2F"
            table_data.append([
                Paragraph(item.get("faculty_code", ""), cell_center),
                Paragraph(item.get("name", ""), cell_norm),
                Paragraph(item.get("department", ""), cell_center),
                Paragraph(item.get("designation", ""), cell_norm),
                Paragraph(str(assigned), cell_center),
                Paragraph(str(max_h), cell_center),
                Paragraph(f"<font color='{pct_color}'><b>{pct}%</b></font>", cell_center),
            ])

        page_w = 595.27 - 60
        col_w = [65, 120, 55, 115, 60, 55, 65]
        t = Table(table_data, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E0E4E8")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAAAAA")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t)
        doc.build(elements)
        return output_path

