"""
ClassPlanner - Timetable Grid View & Manual Editing Widget
Traditional college schedule grid with Section, Faculty, and Classroom views,
plus PDF/Excel export and in-place slot editing.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QMessageBox, QFileDialog, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor, QBrush
from classplanner.database.db_manager import DatabaseManager
from classplanner.ui.dialogs.edit_cell_dialog import EditCellDialog
from classplanner.exporters.pdf_exporter import PDFExporter
from classplanner.exporters.excel_exporter import ExcelExporter
import os


class TimetableGridWidget(QWidget):
    """Timetable Grid Display and Manual Editing Interface."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_entries = []
        self.cell_entry_map = {}  # (day, slot_number) -> entry dict
        self.init_ui()
        self.load_timetables_dropdown()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Top Control Bar (View Mode & Filters)
        self.top_group = QGroupBox("Timetable View Controls")
        top_layout = QHBoxLayout(self.top_group)
        top_layout.setSpacing(12)

        # Timetable selector
        lbl_tt = QLabel("Timetable:")
        self.cmb_timetables = QComboBox()
        self.cmb_timetables.setMinimumWidth(240)
        self.cmb_timetables.setFixedHeight(28)
        self.cmb_timetables.currentIndexChanged.connect(self.on_filter_changed)

        # View Mode selector
        lbl_mode = QLabel("View Type:")
        self.cmb_view_mode = QComboBox()
        self.cmb_view_mode.setMinimumWidth(160)
        self.cmb_view_mode.setFixedHeight(28)
        self.cmb_view_mode.addItems(["Section-wise", "Faculty-wise", "Classroom-wise"])
        self.cmb_view_mode.currentIndexChanged.connect(self.on_mode_changed)

        # Entity selector (Section / Faculty / Room)
        self.lbl_target = QLabel("Section:")
        self.cmb_target = QComboBox()
        self.cmb_target.setMinimumWidth(240)
        self.cmb_target.setFixedHeight(28)
        self.cmb_target.currentIndexChanged.connect(self.on_filter_changed)

        top_layout.addWidget(lbl_tt)
        top_layout.addWidget(self.cmb_timetables)
        top_layout.addSpacing(12)
        top_layout.addWidget(lbl_mode)
        top_layout.addWidget(self.cmb_view_mode)
        top_layout.addSpacing(12)
        top_layout.addWidget(self.lbl_target)
        top_layout.addWidget(self.cmb_target)
        top_layout.addStretch()

        main_layout.addWidget(self.top_group)

        # Action Toolbar (Export, Edit, Refresh)
        act_bar = QHBoxLayout()
        act_bar.setAlignment(Qt.AlignVCenter)
        act_bar.setContentsMargins(0, 0, 0, 4)

        self.btn_edit = QPushButton("✏️ Edit Selected Slot")
        self.btn_edit.setFixedHeight(28)
        self.btn_edit.clicked.connect(self.on_edit_selected_cell)

        self.btn_pdf = QPushButton("📄 Export to PDF")
        self.btn_pdf.setFixedHeight(28)
        self.btn_pdf.clicked.connect(self.on_export_pdf)

        self.btn_excel = QPushButton("📊 Export to Excel")
        self.btn_excel.setFixedHeight(28)
        self.btn_excel.clicked.connect(self.on_export_excel)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.setFixedHeight(28)
        self.btn_refresh.clicked.connect(self.load_grid)

        act_bar.addWidget(self.btn_edit)
        act_bar.addSpacing(15)
        act_bar.addWidget(self.btn_pdf)
        act_bar.addWidget(self.btn_excel)
        act_bar.addStretch()
        act_bar.addWidget(self.btn_refresh)
        main_layout.addLayout(act_bar)

        # Timetable Grid Table
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        main_layout.addWidget(self.table)

        # Bottom Legend / Help note
        lbl_hint = QLabel("💡 Tip: Double-click any period cell or click 'Edit Selected Slot' to change subjects, faculty, or classrooms.")
        lbl_hint.setStyleSheet("color: #555555; font-style: italic;")
        main_layout.addWidget(lbl_hint)

    def load_timetables_dropdown(self):
        self.cmb_timetables.blockSignals(True)
        self.cmb_timetables.clear()
        timetables = self.db.get_timetables()
        active_idx = 0
        for idx, tt in enumerate(timetables):
            name = f"{tt['name']} ({tt['academic_year']})"
            if tt["is_active"]:
                name += " [ACTIVE]"
                active_idx = idx
            self.cmb_timetables.addItem(name, tt["id"])

        if timetables:
            self.cmb_timetables.setCurrentIndex(active_idx)
        self.cmb_timetables.blockSignals(False)
        self.on_mode_changed()

    def on_mode_changed(self):
        mode = self.cmb_view_mode.currentText()
        self.cmb_target.blockSignals(True)
        self.cmb_target.clear()

        if mode == "Section-wise":
            self.lbl_target.setText("Select Section:")
            sections = self.db.get_sections()
            for s in sections:
                self.cmb_target.addItem(f"{s['section_name']} ({s['dept_code']} Sem {s['semester']})", s["id"])

        elif mode == "Faculty-wise":
            self.lbl_target.setText("Select Faculty:")
            faculties = self.db.get_faculty_list()
            for f in faculties:
                self.cmb_target.addItem(f"{f['name']} ({f['faculty_id']} - {f['dept_code']})", f["id"])

        elif mode == "Classroom-wise":
            self.lbl_target.setText("Select Classroom:")
            rooms = self.db.get_classrooms()
            for r in rooms:
                self.cmb_target.addItem(f"{r['room_number']} ({r['room_type']})", r["id"])

        self.cmb_target.blockSignals(False)
        self.load_grid()

    def on_filter_changed(self):
        self.load_grid()

    def load_grid(self):
        tt_id = self.cmb_timetables.currentData()
        if not tt_id:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        working_days = self.db.get_active_working_days()
        all_slots = self.db.get_all_time_slots()
        mode = self.cmb_view_mode.currentText()
        target_id = self.cmb_target.currentData()

        if not target_id:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        # Fetch entries based on mode
        if mode == "Section-wise":
            entries = self.db.get_timetable_entries(tt_id, section_id=target_id)
        elif mode == "Faculty-wise":
            entries = self.db.get_timetable_entries(tt_id, faculty_id=target_id)
        elif mode == "Classroom-wise":
            entries = self.db.get_timetable_entries(tt_id, classroom_id=target_id)
        else:
            entries = []

        self.current_entries = entries
        self.cell_entry_map = {(e["day_name"], e["slot_number"]): e for e in entries}

        # Configure Table Columns and Rows
        self.table.setColumnCount(len(working_days))
        self.table.setHorizontalHeaderLabels(working_days)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.table.setRowCount(len(all_slots))
        slot_labels = [f"{s['slot_name']}\n{s['start_time']} - {s['end_time']}" for s in all_slots]
        self.table.setVerticalHeaderLabels(slot_labels)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Cell Font
        bold_font = QFont("Segoe UI", 9, QFont.Bold)
        normal_font = QFont("Segoe UI", 8.5)

        for row_idx, slot in enumerate(all_slots):
            s_num = slot["slot_number"]
            is_break = bool(slot.get("is_break"))

            if is_break:
                # Break row formatting
                break_name = f"*** {slot['slot_name'].upper()} ***"
                for col_idx, day in enumerate(working_days):
                    item = QTableWidgetItem(break_name)
                    item.setFont(bold_font)
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setBackground(QBrush(QColor("#E8E8E8")))
                    item.setForeground(QBrush(QColor("#404040")))
                    self.table.setItem(row_idx, col_idx, item)
            else:
                for col_idx, day in enumerate(working_days):
                    entry = self.cell_entry_map.get((day, s_num))
                    if entry:
                        # Construct cell text
                        text_lines = [
                            f"【{entry['subject_code']}】",
                            entry["subject_name"]
                        ]
                        if mode != "Faculty-wise":
                            text_lines.append(f"👨‍🏫 {entry['faculty_name']}")
                        if mode != "Classroom-wise":
                            text_lines.append(f"🏫 Room: {entry['room_number']}")
                        if mode != "Section-wise":
                            text_lines.append(f"👥 Sec: {entry['section_name']}")

                        cell_text = "\n".join(text_lines)
                        item = QTableWidgetItem(cell_text)
                        item.setTextAlignment(Qt.AlignCenter)

                        # Highlight practical lab sessions
                        if entry.get("requires_lab") or entry.get("subject_type") == "Practical / Laboratory":
                            item.setBackground(QBrush(QColor("#E6F2FF")))  # Subtle light blue for labs
                        else:
                            item.setBackground(QBrush(QColor("#FFFFFF")))

                        item.setFont(normal_font)
                        self.table.setItem(row_idx, col_idx, item)
                    else:
                        item = QTableWidgetItem("- Free -")
                        item.setTextAlignment(Qt.AlignCenter)
                        item.setForeground(QBrush(QColor("#999999")))
                        item.setBackground(QBrush(QColor("#FAFAFA")))
                        item.setFont(normal_font)
                        self.table.setItem(row_idx, col_idx, item)

    def on_cell_double_clicked(self, row: int, col: int):
        self._edit_cell(row, col)

    def on_edit_selected_cell(self):
        row = self.table.currentRow()
        col = self.table.currentColumn()
        if row < 0 or col < 0:
            QMessageBox.information(self, "Select Cell", "Please click on a timetable cell to edit.")
            return
        self._edit_cell(row, col)

    def _edit_cell(self, row: int, col: int):
        all_slots = self.db.get_all_time_slots()
        working_days = self.db.get_active_working_days()

        if row >= len(all_slots) or col >= len(working_days):
            return

        slot = all_slots[row]
        day = working_days[col]

        if slot["is_break"]:
            QMessageBox.information(self, "Break Period", f"{slot['slot_name']} cannot be edited as it is reserved for breaks.")
            return

        mode = self.cmb_view_mode.currentText()
        if mode != "Section-wise":
            QMessageBox.information(
                self,
                "Switch to Section View",
                "Manual editing is performed from the Section-wise view.\n"
                "Please switch to 'Section-wise' view to edit this section's periods."
            )
            return

        tt_id = self.cmb_timetables.currentData()
        section_id = self.cmb_target.currentData()
        current_entry = self.cell_entry_map.get((day, slot["slot_number"]))

        dlg = EditCellDialog(
            db=self.db,
            timetable_id=tt_id,
            section_id=section_id,
            day_name=day,
            slot_number=slot["slot_number"],
            current_entry=current_entry,
            parent=self
        )
        if dlg.exec():
            self.load_grid()

    def on_export_pdf(self):
        target_name = self.cmb_target.currentText()
        mode = self.cmb_view_mode.currentText()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Timetable PDF",
            f"Timetable_{mode}_{target_name.split()[0]}.pdf",
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        working_days = self.db.get_active_working_days()
        all_slots = self.db.get_all_time_slots()
        inst_name = self.db.get_setting("institution_name", "Government Engineering College")
        inst_addr = self.db.get_setting("institution_address", "College Campus, University Road")
        acad_year = self.db.get_setting("academic_year", "2026-2027")

        exporter = PDFExporter(inst_name, inst_addr, acad_year)
        try:
            exporter.export_timetable_grid(
                output_path=file_path,
                title=f"COLLEGE TIMETABLE ({mode.upper()})",
                subtitle=target_name,
                days=working_days,
                time_slots=all_slots,
                grid_data=self.cell_entry_map
            )
            QMessageBox.information(self, "Export Complete", f"Timetable PDF exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not export PDF: {e}")

    def on_export_excel(self):
        target_name = self.cmb_target.currentText()
        mode = self.cmb_view_mode.currentText()
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Timetable Excel",
            f"Timetable_{mode}_{target_name.split()[0]}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        working_days = self.db.get_active_working_days()
        all_slots = self.db.get_all_time_slots()
        inst_name = self.db.get_setting("institution_name", "Government Engineering College")
        inst_addr = self.db.get_setting("institution_address", "College Campus, University Road")
        acad_year = self.db.get_setting("academic_year", "2026-2027")

        exporter = ExcelExporter(inst_name, inst_addr, acad_year)
        try:
            exporter.export_timetable_grid(
                output_path=file_path,
                title=f"COLLEGE TIMETABLE ({mode.upper()})",
                subtitle=target_name,
                days=working_days,
                time_slots=all_slots,
                grid_data=self.cell_entry_map
            )
            QMessageBox.information(self, "Export Complete", f"Timetable Excel workbook exported successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not export Excel: {e}")

