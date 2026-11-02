"""
ClassPlanner - Automated Timetable Generation Interface
Provides full execution controls, constraint verification, utilization analysis, and regeneration.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QSpinBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal
from classplanner.database.db_manager import DatabaseManager
from classplanner.solver.timetable_generator import TimetableGenerator, TimetableGenerationResult
import random


class GeneratorThread(QThread):
    """Background worker thread for timetable generation to keep GUI responsive."""
    generation_finished = Signal(object)

    def __init__(self, db: DatabaseManager, name: str, year: str, sem_type: str,
                 dept_id=None, seed=None, attempts=5):
        super().__init__()
        self.db = db
        self.name = name
        self.year = year
        self.sem_type = sem_type
        self.dept_id = dept_id
        self.seed = seed
        self.attempts = attempts

    def run(self):
        engine = TimetableGenerator(self.db)
        result = engine.generate(
            timetable_name=self.name,
            academic_year=self.year,
            semester_type=self.sem_type,
            department_id=self.dept_id,
            random_seed=self.seed,
            max_attempts=self.attempts
        )
        self.generation_finished.emit(result)


class GeneratorWidget(QWidget):
    """Timetable Generator View."""
    view_timetable_requested = Signal()

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.last_result: Optional[TimetableGenerationResult] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Title
        lbl_title = QLabel("Automated College Timetable Generator")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")
        main_layout.addWidget(lbl_title)

        # Configuration Panel
        config_group = QGroupBox("Generation Parameters & Scope")
        form_lay = QFormLayout(config_group)

        self.txt_name = QLineEdit()
        self.txt_name.setText("Semester Timetable - " + self.db.get_setting("academic_year", "2026-2027"))

        self.txt_year = QLineEdit()
        self.txt_year.setText(self.db.get_setting("academic_year", "2026-2027"))

        self.cmb_sem_type = QComboBox()
        self.cmb_sem_type.addItems(["Even", "Odd", "All"])

        self.cmb_dept = QComboBox()
        self.cmb_dept.addItem("-- All Academic Departments --", None)
        for d in self.db.get_departments():
            self.cmb_dept.addItem(f"{d['code']} - {d['name']}", d["id"])

        self.spn_attempts = QSpinBox()
        self.spn_attempts.setRange(1, 20)
        self.spn_attempts.setValue(5)
        self.spn_attempts.setSuffix(" optimization rounds")

        form_lay.addRow("Timetable Title *:", self.txt_name)
        form_lay.addRow("Academic Year *:", self.txt_year)
        form_lay.addRow("Semester Scope *:", self.cmb_sem_type)
        form_lay.addRow("Target Department:", self.cmb_dept)
        form_lay.addRow("Solver Search Effort:", self.spn_attempts)

        main_layout.addWidget(config_group)

        # Action Buttons & Progress Bar
        action_bar = QHBoxLayout()
        action_bar.setAlignment(Qt.AlignVCenter)
        action_bar.setContentsMargins(0, 4, 0, 4)

        self.btn_generate = QPushButton("🚀 Generate Timetable")
        self.btn_generate.setObjectName("btn_primary")
        self.btn_generate.setFixedHeight(32)
        self.btn_generate.clicked.connect(self.on_start_generation)

        self.btn_regenerate = QPushButton("🎲 Regenerate Alternative Schedule")
        self.btn_regenerate.setFixedHeight(32)
        self.btn_regenerate.clicked.connect(self.on_regenerate_alternative)

        self.btn_view = QPushButton("📅 View Generated Timetable")
        self.btn_view.setFixedHeight(32)
        self.btn_view.setEnabled(False)
        self.btn_view.clicked.connect(lambda: self.view_timetable_requested.emit())

        action_bar.addWidget(self.btn_generate)
        action_bar.addWidget(self.btn_regenerate)
        action_bar.addWidget(self.btn_view)
        action_bar.addStretch()
        main_layout.addLayout(action_bar)

        self.prog_bar = QProgressBar()
        self.prog_bar.setRange(0, 0)
        self.prog_bar.setVisible(False)
        main_layout.addWidget(self.prog_bar)

        # Status & Results Tabs
        self.tabs = QTabWidget()

        # Tab 1: Execution Log & Status
        tab_log = QWidget()
        v_log = QVBoxLayout(tab_log)
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setPlaceholderText("Generation results and constraint diagnostics will appear here...")
        v_log.addWidget(self.txt_log)
        self.tabs.addTab(tab_log, "📋 Status & Diagnostics")

        # Tab 2: Faculty Utilization
        self.tbl_faculty = QTableWidget()
        self.tbl_faculty.setColumnCount(5)
        self.tbl_faculty.setHorizontalHeaderLabels(["Faculty Code", "Faculty Name", "Department", "Assigned Hours", "Utilization %"])
        self.tbl_faculty.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_faculty.verticalHeader().setVisible(False)
        self.tbl_faculty.verticalHeader().setDefaultSectionSize(34)
        self.tabs.addTab(self.tbl_faculty, "👨‍🏫 Faculty Utilization")

        # Tab 3: Classroom Utilization
        self.tbl_rooms = QTableWidget()
        self.tbl_rooms.setColumnCount(5)
        self.tbl_rooms.setHorizontalHeaderLabels(["Room Number", "Building", "Room Type", "Assigned Periods", "Utilization %"])
        self.tbl_rooms.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_rooms.verticalHeader().setVisible(False)
        self.tbl_rooms.verticalHeader().setDefaultSectionSize(34)
        self.tabs.addTab(self.tbl_rooms, "🏫 Classroom Utilization")

        # Tab 4: Unscheduled / Conflicts
        self.tbl_unscheduled = QTableWidget()
        self.tbl_unscheduled.setColumnCount(4)
        self.tbl_unscheduled.setHorizontalHeaderLabels(["Section", "Subject", "Periods", "Conflict / Unresolved Reason"])
        self.tbl_unscheduled.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_unscheduled.verticalHeader().setVisible(False)
        self.tbl_unscheduled.verticalHeader().setDefaultSectionSize(34)
        self.tabs.addTab(self.tbl_unscheduled, "⚠️ Unscheduled Subjects")

        main_layout.addWidget(self.tabs)

    def on_start_generation(self, seed=None):
        name = self.txt_name.text().strip()
        year = self.txt_year.text().strip()
        if not name or not year:
            QMessageBox.warning(self, "Validation Error", "Timetable Title and Academic Year are required.")
            return

        self.btn_generate.setEnabled(False)
        self.btn_regenerate.setEnabled(False)
        self.btn_view.setEnabled(False)
        self.prog_bar.setVisible(True)

        self.txt_log.clear()
        self.txt_log.append("Starting automated timetable generator engine...")
        self.txt_log.append(f"Applying mandatory hard constraints:\n"
                            f"  - Faculty availability and no double-booking\n"
                            f"  - Classroom capacity and no collision\n"
                            f"  - Section no overlap\n"
                            f"  - Consecutive periods for laboratories\n"
                            f"  - Lunch & tea breaks preserved free\n"
                            f"  - Workload limits per faculty\n")

        self.thread = GeneratorThread(
            db=self.db,
            name=name,
            year=year,
            sem_type=self.cmb_sem_type.currentText(),
            dept_id=self.cmb_dept.currentData(),
            seed=seed,
            attempts=self.spn_attempts.value()
        )
        self.thread.generation_finished.connect(self.on_generation_finished)
        self.thread.start()

    def on_regenerate_alternative(self):
        new_seed = random.randint(1, 999999)
        self.txt_log.append(f"\n[Regenerate] Using new randomization seed {new_seed} for alternative layout...")
        self.on_start_generation(seed=new_seed)

    def on_generation_finished(self, result: TimetableGenerationResult):
        self.last_result = result
        self.prog_bar.setVisible(False)
        self.btn_generate.setEnabled(True)
        self.btn_regenerate.setEnabled(True)
        self.btn_view.setEnabled(True)

        # Log details
        self.txt_log.append("=" * 60)
        self.txt_log.append(f"GENERATION RESULT: {'SUCCESS' if result.success else 'COMPLETED WITH WARNINGS'}")
        self.txt_log.append(f"Total Periods Required: {result.total_required_periods}")
        self.txt_log.append(f"Total Periods Successfully Scheduled: {result.total_scheduled_periods}")
        self.txt_log.append(f"Schedule Optimization Score (Fitness): {result.fitness_score}%")
        self.txt_log.append(f"Elapsed Time: {result.execution_time_seconds} seconds")
        self.txt_log.append("=" * 60)

        for msg in result.messages:
            self.txt_log.append(msg)

        # Fill Faculty Utilization Table
        fac_data = result.faculty_utilization
        self.tbl_faculty.setRowCount(len(fac_data))
        for row, (name, d) in enumerate(fac_data.items()):
            it0 = QTableWidgetItem(d["faculty_code"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_faculty.setItem(row, 0, it0)

            it1 = QTableWidgetItem(name)
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_faculty.setItem(row, 1, it1)

            it2 = QTableWidgetItem(d["department"])
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_faculty.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f"{d['assigned_hours']} / {d['max_hours']} hrs")
            it3.setTextAlignment(Qt.AlignCenter)
            self.tbl_faculty.setItem(row, 3, it3)

            it4 = QTableWidgetItem(f"{d['utilization_pct']}%")
            it4.setTextAlignment(Qt.AlignCenter)
            self.tbl_faculty.setItem(row, 4, it4)

        # Fill Classroom Utilization Table
        room_data = result.classroom_utilization
        self.tbl_rooms.setRowCount(len(room_data))
        for row, (rno, d) in enumerate(room_data.items()):
            it0 = QTableWidgetItem(rno)
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_rooms.setItem(row, 0, it0)

            it1 = QTableWidgetItem(d["building"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_rooms.setItem(row, 1, it1)

            it2 = QTableWidgetItem(d["room_type"])
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_rooms.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f"{d['assigned_periods']} periods")
            it3.setTextAlignment(Qt.AlignCenter)
            self.tbl_rooms.setItem(row, 3, it3)

            it4 = QTableWidgetItem(f"{d['utilization_pct']}%")
            it4.setTextAlignment(Qt.AlignCenter)
            self.tbl_rooms.setItem(row, 4, it4)

        # Fill Unscheduled Table
        unsched = result.unscheduled_items
        self.tbl_unscheduled.setRowCount(len(unsched))
        for row, u in enumerate(unsched):
            it0 = QTableWidgetItem(u.get("section", ""))
            it0.setTextAlignment(Qt.AlignCenter)
            self.tbl_unscheduled.setItem(row, 0, it0)

            it1 = QTableWidgetItem(u.get("subject", ""))
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_unscheduled.setItem(row, 1, it1)

            it2 = QTableWidgetItem(str(u.get("block_size", 1)))
            it2.setTextAlignment(Qt.AlignCenter)
            self.tbl_unscheduled.setItem(row, 2, it2)

            it3 = QTableWidgetItem(u.get("reason", ""))
            it3.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.tbl_unscheduled.setItem(row, 3, it3)

        if result.success:
            QMessageBox.information(
                self,
                "Generation Success",
                f"Automated timetable generated successfully!\n"
                f"Scheduled: {result.total_scheduled_periods}/{result.total_required_periods} periods without conflicts.\n"
                f"Click 'View Generated Timetable' to inspect."
            )
        else:
            QMessageBox.warning(
                self,
                "Generation Warnings",
                f"Generated timetable with {result.total_scheduled_periods}/{result.total_required_periods} periods scheduled.\n"
                f"{len(unsched)} items could not be placed due to tight constraints. Check 'Unscheduled Subjects' tab."
            )

