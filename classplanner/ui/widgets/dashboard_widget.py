"""
ClassPlanner - Dashboard Widget
Classic overview with summary metrics and quick access actions.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGridLayout, QGroupBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from classplanner.database.db_manager import DatabaseManager
from classplanner.database.sample_data import load_sample_college_data


class DashboardWidget(QWidget):
    """Dashboard view displaying system counts and quick access buttons."""
    navigate_requested = Signal(str)

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_stats()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header Title
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.StyledPanel)
        header_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #A0A0A0; padding: 10px; }")
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(5, 5, 5, 5)

        lbl_inst = QLabel(self.db.get_setting("institution_name", "Government Engineering College"))
        f_inst = QFont("Segoe UI", 13, QFont.Bold)
        lbl_inst.setFont(f_inst)
        lbl_inst.setStyleSheet("color: #1A2B4C;")
        self.lbl_inst = lbl_inst

        lbl_sub = QLabel("Automated College Timetable Management System — Control Center")
        lbl_sub.setStyleSheet("color: #555555; font-size: 9.5pt;")

        h_layout.addWidget(lbl_inst)
        h_layout.addWidget(lbl_sub)
        main_layout.addWidget(header_frame)

        # 1. Statistics Summary Grid (Traditional border boxes)
        stats_group = QGroupBox("College Master Data Summary")
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(10)

        self.card_depts = self._create_stat_box("Departments", "0", "#004080")
        self.card_faculty = self._create_stat_box("Faculty Members", "0", "#004080")
        self.card_subjects = self._create_stat_box("Total Subjects", "0", "#004080")
        self.card_rooms = self._create_stat_box("Classrooms & Labs", "0", "#004080")
        self.card_sections = self._create_stat_box("Student Sections", "0", "#004080")
        self.card_timetables = self._create_stat_box("Generated Timetables", "0", "#006600")

        stats_layout.addWidget(self.card_depts, 0, 0)
        stats_layout.addWidget(self.card_faculty, 0, 1)
        stats_layout.addWidget(self.card_subjects, 0, 2)
        stats_layout.addWidget(self.card_rooms, 1, 0)
        stats_layout.addWidget(self.card_sections, 1, 1)
        stats_layout.addWidget(self.card_timetables, 1, 2)

        main_layout.addWidget(stats_group)

        # 2. Active Timetable Status
        tt_group = QGroupBox("Active Timetable Status")
        tt_layout = QVBoxLayout(tt_group)

        self.lbl_tt_status = QLabel("No active timetable generated yet.")
        self.lbl_tt_status.setStyleSheet("font-size: 10pt; padding: 5px;")
        tt_layout.addWidget(self.lbl_tt_status)

        main_layout.addWidget(tt_group)

        # 3. Quick Access Buttons
        quick_group = QGroupBox("Quick Access Operations")
        quick_layout = QGridLayout(quick_group)
        quick_layout.setSpacing(10)

        btn_gen = QPushButton("⚡ Generate Automated Timetable")
        btn_gen.setObjectName("btn_primary")
        btn_gen.setMinimumHeight(35)
        btn_gen.clicked.connect(lambda: self.navigate_requested.emit("generator"))

        btn_view_tt = QPushButton("📅 View Active Timetables")
        btn_view_tt.setMinimumHeight(35)
        btn_view_tt.clicked.connect(lambda: self.navigate_requested.emit("timetable_view"))

        btn_edit_tt = QPushButton("✏️ Manual Timetable Editor")
        btn_edit_tt.setMinimumHeight(35)
        btn_edit_tt.clicked.connect(lambda: self.navigate_requested.emit("timetable_edit"))

        btn_fac = QPushButton("👨‍🏫 Faculty Management")
        btn_fac.setMinimumHeight(35)
        btn_fac.clicked.connect(lambda: self.navigate_requested.emit("faculty"))

        btn_sub = QPushButton("📚 Subject Management")
        btn_sub.setMinimumHeight(35)
        btn_sub.clicked.connect(lambda: self.navigate_requested.emit("subjects"))

        btn_room = QPushButton("🏫 Classroom Management")
        btn_room.setMinimumHeight(35)
        btn_room.clicked.connect(lambda: self.navigate_requested.emit("classrooms"))

        btn_sec = QPushButton("👥 Student Sections")
        btn_sec.setMinimumHeight(35)
        btn_sec.clicked.connect(lambda: self.navigate_requested.emit("sections"))

        btn_rep = QPushButton("📊 Reports && Workload")
        btn_rep.setMinimumHeight(35)
        btn_rep.clicked.connect(lambda: self.navigate_requested.emit("reports"))

        btn_sample = QPushButton("📥 Load Sample College Data")
        btn_sample.setMinimumHeight(35)
        btn_sample.clicked.connect(self.on_load_sample_data)

        quick_layout.addWidget(btn_gen, 0, 0)
        quick_layout.addWidget(btn_view_tt, 0, 1)
        quick_layout.addWidget(btn_edit_tt, 0, 2)
        quick_layout.addWidget(btn_fac, 1, 0)
        quick_layout.addWidget(btn_sub, 1, 1)
        quick_layout.addWidget(btn_room, 1, 2)
        quick_layout.addWidget(btn_sec, 2, 0)
        quick_layout.addWidget(btn_rep, 2, 1)
        quick_layout.addWidget(btn_sample, 2, 2)

        main_layout.addWidget(quick_group)
        main_layout.addStretch()

    def _create_stat_box(self, title: str, initial_value: str, color_hex: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid #A0A0A0;
                padding: 6px;
            }}
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(4)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 8.5pt; color: #555555; text-transform: uppercase;")

        lbl_val = QLabel(initial_value)
        lbl_val.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_val.setStyleSheet(f"color: {color_hex};")
        lbl_val.setAlignment(Qt.AlignCenter)

        vbox.addWidget(lbl_title, alignment=Qt.AlignCenter)
        vbox.addWidget(lbl_val, alignment=Qt.AlignCenter)
        frame.lbl_val = lbl_val
        return frame

    def refresh_stats(self):
        """Refreshes all summary metrics from database."""
        stats = self.db.get_dashboard_stats()
        self.card_depts.lbl_val.setText(str(stats["total_departments"]))
        self.card_faculty.lbl_val.setText(str(stats["total_faculty"]))
        self.card_subjects.lbl_val.setText(str(stats["total_subjects"]))
        self.card_rooms.lbl_val.setText(str(stats["total_classrooms"]))
        self.card_sections.lbl_val.setText(str(stats["total_sections"]))
        self.card_timetables.lbl_val.setText(str(stats["total_timetables"]))

        active_col = self.db.get_active_college()
        if active_col:
            self.lbl_inst.setText(f"{active_col['college_name']} [{active_col['college_code']}]")
        else:
            self.lbl_inst.setText(self.db.get_setting("institution_name", "Government Engineering College"))

        active_tt = stats["active_timetable"]
        if active_tt:
            text = (
                f"<b>Active Timetable:</b> {active_tt['name']} &nbsp;|&nbsp; "
                f"<b>Academic Year:</b> {active_tt['academic_year']} &nbsp;|&nbsp; "
                f"<b>Term:</b> {active_tt['semester_type']} Semester &nbsp;|&nbsp; "
                f"<b>Scheduled Periods:</b> {stats['total_scheduled_entries']}"
            )
            self.lbl_tt_status.setText(text)
            self.lbl_tt_status.setStyleSheet("color: #006600; font-size: 9.5pt; padding: 4px; background: #FFFFFF; border: 1px solid #C0C0C0;")
        else:
            self.lbl_tt_status.setText("No active timetable generated yet. Click 'Generate Automated Timetable' to create one.")
            self.lbl_tt_status.setStyleSheet("color: #666666; font-size: 9.5pt; padding: 4px; background: #FFFFFF; border: 1px solid #C0C0C0;")

    def on_load_sample_data(self):
        reply = QMessageBox.question(
            self,
            "Load Sample College Dataset",
            "Are you sure you want to load sample college data?\n"
            "This will populate CSE, ECE and MECH departments with faculty, subjects, and classrooms.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            success, msg = load_sample_college_data(self.db, force=True)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh_stats()
            else:
                QMessageBox.warning(self, "Notice", msg)

