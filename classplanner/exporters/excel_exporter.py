"""
ClassPlanner - Excel Exporter
Generates styled Microsoft Excel (.xlsx) workbooks using openpyxl.
"""

from typing import List, Dict, Any, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter


class ExcelExporter:
    """Exports college timetables and reports to formatted Excel spreadsheets."""

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
        grid_data: Dict[Tuple[str, int], Dict[str, Any]]
    ) -> str:
        """
        Exports a formatted timetable grid into an Excel workbook.
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Timetable"

        # Styles
        font_inst = Font(name="Segoe UI", size=14, bold=True, color="1A2B4C")
        font_sub = Font(name="Segoe UI", size=10, italic=True, color="555555")
        font_title = Font(name="Segoe UI", size=11, bold=True, color="0D47A1")
        font_header = Font(name="Segoe UI", size=10, bold=True, color="000000")
        font_cell_bold = Font(name="Segoe UI", size=9, bold=True)
        font_cell = Font(name="Segoe UI", size=8.5)
        font_break = Font(name="Segoe UI", size=9, bold=True, color="333333")
        font_free = Font(name="Segoe UI", size=8, color="888888")

        fill_header = PatternFill(start_color="D6DFEB", end_color="D6DFEB", fill_type="solid")
        fill_break = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
        fill_cell = PatternFill(start_color="FAFAFA", end_color="FAFAFA", fill_type="solid")

        thin_side = Side(border_style="thin", color="808080")
        box_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

        align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
        align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

        # Header rows
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(days) + 1)
        ws.cell(row=1, column=1, value=self.institution_name).font = font_inst
        ws.cell(row=1, column=1).alignment = align_center

        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(days) + 1)
        ws.cell(row=2, column=1, value=f"{self.institution_address} | Academic Year: {self.academic_year}").font = font_sub
        ws.cell(row=2, column=1).alignment = align_center

        ws.merge_cells(start_row=3, start_column=1, end_row=3, end_column=len(days) + 1)
        ws.cell(row=3, column=1, value=f"{title} — {subtitle}").font = font_title
        ws.cell(row=3, column=1).alignment = align_center

        # Table Header Row (Row 5)
        header_row = 5
        ws.cell(row=header_row, column=1, value="Time / Period").font = font_header
        ws.cell(row=header_row, column=1).fill = fill_header
        ws.cell(row=header_row, column=1).border = box_border
        ws.cell(row=header_row, column=1).alignment = align_center

        for col_idx, day in enumerate(days, start=2):
            c = ws.cell(row=header_row, column=col_idx, value=day)
            c.font = font_header
            c.fill = fill_header
            c.border = box_border
            c.alignment = align_center

        # Table Content Rows
        current_row = header_row + 1
        for slot in time_slots:
            s_num = slot["slot_number"]
            s_name = slot["slot_name"]
            s_time = f"{slot['start_time']} - {slot['end_time']}"
            is_break = bool(slot.get("is_break"))

            # First column: Period & Time
            c_time = ws.cell(row=current_row, column=1, value=f"{s_name}\n({s_time})")
            c_time.font = font_cell_bold
            c_time.border = box_border
            c_time.alignment = align_center

            if is_break:
                # Merge across days
                ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=len(days) + 1)
                for col_idx in range(2, len(days) + 2):
                    cell = ws.cell(row=current_row, column=col_idx)
                    cell.border = box_border
                    cell.fill = fill_break
                c_break = ws.cell(row=current_row, column=2, value=f"*** {s_name.upper()} ({s_time}) ***")
                c_break.font = font_break
                c_break.alignment = align_center
            else:
                for col_idx, day in enumerate(days, start=2):
                    cell = ws.cell(row=current_row, column=col_idx)
                    cell.border = box_border
                    cell.fill = fill_cell
                    cell.alignment = align_center

                    entry = grid_data.get((day, s_num))
                    if entry:
                        parts = [
                            entry.get("subject_code", "") or entry.get("subject_name", ""),
                            entry.get("faculty_name", ""),
                            f"Room: {entry.get('room_number', '')}"
                        ]
                        if entry.get("section_name") and entry.get("section_name") not in title:
                            parts.insert(1, f"Sec: {entry.get('section_name')}")
                        cell.value = "\n".join([p for p in parts if p])
                        cell.font = font_cell
                    else:
                        cell.value = "- Free -"
                        cell.font = font_free

            ws.row_dimensions[current_row].height = 45 if not is_break else 25
            current_row += 1

        # Adjust column widths
        ws.column_dimensions["A"].width = 20
        for col_idx in range(2, len(days) + 2):
            col_letter = get_column_letter(col_idx)
            ws.column_dimensions[col_letter].width = 22

        wb.save(output_path)
        return output_path

    def export_comprehensive_report(
        self,
        output_path: str,
        faculty_workload: List[Dict[str, Any]],
        classroom_utilization: List[Dict[str, Any]],
        unscheduled_items: List[Dict[str, Any]]
    ) -> str:
        """
        Creates multi-tab workbook with Workload, Room Utilization, and Unscheduled Reports.
        """
        wb = openpyxl.Workbook()

        # Tab 1: Faculty Workload
        ws1 = wb.active
        ws1.title = "Faculty Workload"
        font_h = Font(name="Segoe UI", size=10, bold=True)
        fill_h = PatternFill(start_color="D6DFEB", end_color="D6DFEB", fill_type="solid")

        headers1 = ["Faculty ID", "Faculty Name", "Department", "Designation", "Assigned Hours", "Max Hours/Week", "Utilization %"]
        for col, h in enumerate(headers1, 1):
            c = ws1.cell(row=1, column=col, value=h)
            c.font = font_h
            c.fill = fill_h

        for row, f in enumerate(faculty_workload, 2):
            assigned = f.get("assigned_hours", 0)
            max_h = f.get("max_hours", 18)
            pct = round((assigned / max(1, max_h)) * 100, 1)
            ws1.cell(row=row, column=1, value=f.get("faculty_code", ""))
            ws1.cell(row=row, column=2, value=f.get("name", ""))
            ws1.cell(row=row, column=3, value=f.get("department", ""))
            ws1.cell(row=row, column=4, value=f.get("designation", ""))
            ws1.cell(row=row, column=5, value=assigned)
            ws1.cell(row=row, column=6, value=max_h)
            ws1.cell(row=row, column=7, value=f"{pct}%")

        # Tab 2: Classroom Utilization
        ws2 = wb.create_sheet(title="Classroom Utilization")
        headers2 = ["Room Number", "Building Name", "Room Type", "Assigned Periods", "Total Week Slots", "Utilization %"]
        for col, h in enumerate(headers2, 1):
            c = ws2.cell(row=1, column=col, value=h)
            c.font = font_h
            c.fill = fill_h

        for row, r in enumerate(classroom_utilization, 2):
            ws2.cell(row=row, column=1, value=r.get("room_number", ""))
            ws2.cell(row=row, column=2, value=r.get("building", ""))
            ws2.cell(row=row, column=3, value=r.get("room_type", ""))
            ws2.cell(row=row, column=4, value=r.get("assigned_periods", 0))
            ws2.cell(row=row, column=5, value=r.get("total_slots", 0))
            ws2.cell(row=row, column=6, value=f"{r.get('utilization_pct', 0)}%")

        # Tab 3: Unscheduled Subjects
        ws3 = wb.create_sheet(title="Unscheduled Subjects")
        headers3 = ["Section", "Subject", "Periods", "Type", "Conflict / Reason"]
        for col, h in enumerate(headers3, 1):
            c = ws3.cell(row=1, column=col, value=h)
            c.font = font_h
            c.fill = fill_h

        for row, u in enumerate(unscheduled_items, 2):
            ws3.cell(row=row, column=1, value=u.get("section", ""))
            ws3.cell(row=row, column=2, value=u.get("subject", ""))
            ws3.cell(row=row, column=3, value=u.get("block_size", 1))
            ws3.cell(row=row, column=4, value="Practical" if u.get("is_lab") else "Theory")
            ws3.cell(row=row, column=5, value=u.get("reason", ""))

        # Auto fit column widths for all sheets
        for sheet in wb.worksheets:
            for col in sheet.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = get_column_letter(col[0].column)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

        wb.save(output_path)
        return output_path

