"""
ClassPlanner - Reports & Analytics Widget
Comprehensive reports for Faculty Workload, Classroom Utilization, and Unscheduled Subjects.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget,
    QComboBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager
from classplanner.exporters.pdf_exporter import PDFExporter
from classplanner.exporters.excel_exporter import ExcelExporter


class ReportsWidget(QWidget):
    """Institutional reports and analytics center."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_reports()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        lbl_title = QLabel("College Institutional Reports")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        lbl_tt = QLabel("Timetable:")
        self.cmb_timetables = QComboBox()
        self.cmb_timetables.setMinimumWidth(220)
        timetables = self.db.get_timetables()
        for idx, tt in enumerate(timetables):
            name = f"{tt['name']} ({tt['academic_year']})"
            if tt["is_active"]:
                name += " [ACTIVE]"
            self.cmb_timetables.addItem(name, tt["id"])
        self.cmb_timetables.currentIndexChanged.connect(self.load_reports)

        btn_pdf_workload = QPushButton("📄 Export Workload PDF")
        btn_pdf_workload.setFixedHeight(28)
        btn_pdf_workload.clicked.connect(self.export_workload_pdf)

        btn_excel_all = QPushButton("📊 Export All Reports to Excel")
        btn_excel_all.setObjectName("btn_primary")
        btn_excel_all.setFixedHeight(28)
        btn_excel_all.clicked.connect(self.export_all_excel)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_reports)

        top_bar.setAlignment(Qt.AlignVCenter)
        top_bar.addWidget(lbl_title)
        top_bar.addSpacing(15)
        top_bar.addWidget(lbl_tt)
        top_bar.addWidget(self.cmb_timetables)
        top_bar.addStretch()
        top_bar.addWidget(btn_pdf_workload)
        top_bar.addWidget(btn_excel_all)
        top_bar.addWidget(btn_refresh)
        main_layout.addLayout(top_bar)

        # Tabs for Reports
        self.tabs = QTabWidget()

        # Tab 1: Faculty Workload Report
        self.tbl_workload = QTableWidget()
        self.tbl_workload.setColumnCount(7)
        self.tbl_workload.setHorizontalHeaderLabels([
            "Faculty ID", "Name", "Department", "Designation", "Assigned Hours", "Max Limit", "Utilization %"
        ])
        self.tbl_workload.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_workload.verticalHeader().setVisible(False)
        self.tbl_workload.verticalHeader().setDefaultSectionSize(34)
        self.tbl_workload.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.tbl_workload, "👨‍🏫 Faculty Workload Report")

        # Tab 2: Classroom Utilization Report
        self.tbl_utilization = QTableWidget()
        self.tbl_utilization.setColumnCount(6)
        self.tbl_utilization.setHorizontalHeaderLabels([
            "Room Number", "Building", "Type", "Assigned Periods", "Weekly Total Slots", "Utilization %"
        ])
        self.tbl_utilization.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_utilization.verticalHeader().setVisible(False)
        self.tbl_utilization.verticalHeader().setDefaultSectionSize(34)
        self.tbl_utilization.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.tbl_utilization, "🏫 Classroom Utilization Report")

        # Tab 3: Department Summary Report
        self.tbl_dept_summary = QTableWidget()
        self.tbl_dept_summary.setColumnCount(6)
        self.tbl_dept_summary.setHorizontalHeaderLabels([
            "Dept Code", "Department Name", "Faculty Count", "Sections", "Subjects", "Total Periods Scheduled"
        ])
        self.tbl_dept_summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_dept_summary.verticalHeader().setVisible(False)
        self.tbl_dept_summary.verticalHeader().setDefaultSectionSize(34)
        self.tbl_dept_summary.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabs.addTab(self.tbl_dept_summary, "🏢 Department Timetable Summary")

        main_layout.addWidget(self.tabs)

    def load_reports(self):
        tt_id = self.cmb_timetables.currentData()
        if not tt_id:
            return

        entries = self.db.get_timetable_entries(tt_id)
        faculty_list = self.db.get_faculty_list()
        classrooms = self.db.get_classrooms()
        departments = self.db.get_departments()
        working_days = self.db.get_active_working_days()
        teaching_slots = self.db.get_teaching_slots()
        total_week_slots = len(working_days) * len(teaching_slots)

        # Faculty Workload
        fac_loads = {}
        room_loads = {}
        dept_loads = {}
        for e in entries:
            fac_loads[e["faculty_id"]] = fac_loads.get(e["faculty_id"], 0) + 1
            room_loads[e["classroom_id"]] = room_loads.get(e["classroom_id"], 0) + 1
            d_id = e.get("department_id") or e.get("dept_code")
            dept_loads[d_id] = dept_loads.get(d_id, 0) + 1

        # Populate Workload Table
        self.cached_workload_data = []
        self.tbl_workload.setRowCount(len(faculty_list))
        for row, f in enumerate(faculty_list):
            assigned = fac_loads.get(f["id"], 0)
            max_h = f.get("max_hours_per_week", 18)
            pct = round((assigned / max(1, max_h)) * 100, 1)

            item_data = {
                "faculty_code": f["faculty_id"],
                "name": f["name"],
                "department": f.get("dept_code", ""),
                "designation": f.get("designation", ""),
                "assigned_hours": assigned,
                "max_hours": max_h,
                "utilization_pct": pct
            }
            self.cached_workload_data.append(item_data)

            it0 = QTableWidgetItem(f["faculty_id"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_workload.setItem(row, 0, it0)

            it1 = QTableWidgetItem(f["name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_workload.setItem(row, 1, it1)

            it2 = QTableWidgetItem(f.get("dept_code", ""))
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_workload.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f.get("designation", ""))
            it3.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_workload.setItem(row, 3, it3)

            it4 = QTableWidgetItem(f"{assigned} hrs")
            it4.setTextAlignment(Qt.AlignCenter)
            self.tbl_workload.setItem(row, 4, it4)

            it5 = QTableWidgetItem(f"{max_h} hrs")
            it5.setTextAlignment(Qt.AlignCenter)
            self.tbl_workload.setItem(row, 5, it5)

            it6 = QTableWidgetItem(f"{pct}%")
            it6.setTextAlignment(Qt.AlignCenter)
            self.tbl_workload.setItem(row, 6, it6)

        # Populate Classroom Utilization Table
        self.cached_room_data = []
        self.tbl_utilization.setRowCount(len(classrooms))
        for row, r in enumerate(classrooms):
            assigned = room_loads.get(r["id"], 0)
            pct = round((assigned / max(1, total_week_slots)) * 100, 1)

            item_data = {
                "room_number": r["room_number"],
                "building": r["building_name"],
                "room_type": r["room_type"],
                "assigned_periods": assigned,
                "total_slots": total_week_slots,
                "utilization_pct": pct
            }
            self.cached_room_data.append(item_data)

            it0 = QTableWidgetItem(r["room_number"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_utilization.setItem(row, 0, it0)

            it1 = QTableWidgetItem(r["building_name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_utilization.setItem(row, 1, it1)

            it2 = QTableWidgetItem(r["room_type"])
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_utilization.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f"{assigned} periods")
            it3.setTextAlignment(Qt.AlignCenter)
            self.tbl_utilization.setItem(row, 3, it3)

            it4 = QTableWidgetItem(str(total_week_slots))
            it4.setTextAlignment(Qt.AlignCenter)
            self.tbl_utilization.setItem(row, 4, it4)

            it5 = QTableWidgetItem(f"{pct}%")
            it5.setTextAlignment(Qt.AlignCenter)
            self.tbl_utilization.setItem(row, 5, it5)

        # Populate Department Summary Table
        self.tbl_dept_summary.setRowCount(len(departments))
        for row, d in enumerate(departments):
            f_count = len(self.db.get_faculty_list(department_id=d["id"]))
            sec_count = len(self.db.get_sections(department_id=d["id"]))
            sub_count = len(self.db.get_subjects(department_id=d["id"]))
            scheduled_count = sum(1 for e in entries if e.get("dept_code") == d["code"])

            it0 = QTableWidgetItem(d["code"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_dept_summary.setItem(row, 0, it0)

            it1 = QTableWidgetItem(d["name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_dept_summary.setItem(row, 1, it1)

            it2 = QTableWidgetItem(str(f_count))
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_dept_summary.setItem(row, 2, it2)

            it3 = QTableWidgetItem(str(sec_count))
            it3.setTextAlignment(Qt.AlignCenter)
            self.tbl_dept_summary.setItem(row, 3, it3)

            it4 = QTableWidgetItem(str(sub_count))
            it4.setTextAlignment(Qt.AlignCenter)
            self.tbl_dept_summary.setItem(row, 4, it4)

            it5 = QTableWidgetItem(f"{scheduled_count} periods")
            it5.setTextAlignment(Qt.AlignCenter)
            self.tbl_dept_summary.setItem(row, 5, it5)

    def export_workload_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Faculty Workload PDF",
            "Faculty_Workload_Report.pdf",
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        inst_name = self.db.get_setting("institution_name", "Government Engineering College")
        acad_year = self.db.get_setting("academic_year", "2026-2027")
        exporter = PDFExporter(institution_name=inst_name, academic_year=acad_year)
        try:
            exporter.export_workload_report(file_path, self.cached_workload_data)
            QMessageBox.information(self, "Export Complete", f"Workload PDF exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not export PDF: {e}")

    def export_all_excel(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save College Reports Excel",
            "College_Timetable_Reports.xlsx",
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        inst_name = self.db.get_setting("institution_name", "Government Engineering College")
        acad_year = self.db.get_setting("academic_year", "2026-2027")
        exporter = ExcelExporter(institution_name=inst_name, academic_year=acad_year)
        try:
            exporter.export_comprehensive_report(
                file_path,
                self.cached_workload_data,
                self.cached_room_data,
                []
            )
            QMessageBox.information(self, "Export Complete", f"All Reports exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not export Excel: {e}")

