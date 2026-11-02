"""
ClassPlanner - Academic Courses, Branches & Semesters Widget
Enables College Admins to configure degree programs, branches, and semesters.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QDialog, QFormLayout, QMessageBox, QTabWidget,
    QSpinBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from typing import Dict, Any, Optional
from classplanner.database.db_manager import DatabaseManager


class AddCourseDialog(QDialog):
    """Dialog for creating a new degree course / academic branch."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Add Academic Course / Program")
        self.setFixedSize(400, 240)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. BTECH-CSE")

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. B.Tech in Computer Science & Engineering")

        self.cmb_dept = QComboBox()
        depts = self.db.get_departments()
        for d in depts:
            self.cmb_dept.addItem(f"{d['code']} — {d['name']}", d["id"])

        self.spn_duration = QSpinBox()
        self.spn_duration.setRange(1, 6)
        self.spn_duration.setValue(4)

        form.addRow("Course Code *:", self.txt_code)
        form.addRow("Course Name *:", self.txt_name)
        form.addRow("Department:", self.cmb_dept)
        form.addRow("Duration (Years):", self.spn_duration)
        layout.addLayout(form)

        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Course")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        if not self.txt_code.text().strip() or not self.txt_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Course Code and Name are required.")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "course_code": self.txt_code.text().strip().upper(),
            "course_name": self.txt_name.text().strip(),
            "department_id": self.cmb_dept.currentData(),
            "duration_years": self.spn_duration.value()
        }


class AddSemesterDialog(QDialog):
    """Dialog for creating an academic semester record."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Academic Semester")
        self.setFixedSize(380, 200)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.spn_sem = QSpinBox()
        self.spn_sem.setRange(1, 12)
        self.spn_sem.setValue(1)

        self.txt_year = QLineEdit("2026-2027")

        self.cmb_term = QComboBox()
        self.cmb_term.addItems(["Even", "Odd"])

        form.addRow("Semester Number *:", self.spn_sem)
        form.addRow("Academic Year *:", self.txt_year)
        form.addRow("Term Type *:", self.cmb_term)
        layout.addLayout(form)

        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Save Semester")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        if not self.txt_year.text().strip():
            QMessageBox.warning(self, "Validation Error", "Academic Year is required.")
            return
        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "semester_number": self.spn_sem.value(),
            "academic_year": self.txt_year.text().strip(),
            "term_type": self.cmb_term.currentText()
        }


class CourseSemesterWidget(QWidget):
    """Tabbed management interface for Courses and Semesters."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_all()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        lbl_title = QLabel("Academic Courses, Branches & Semesters")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")
        main_layout.addWidget(lbl_title)

        self.tabs = QTabWidget()

        # Tab 1: Courses & Branches
        tab_courses = QWidget()
        lay_c = QVBoxLayout(tab_courses)
        lay_c.setContentsMargins(10, 10, 10, 10)
        lay_c.setSpacing(10)

        h_c_bar = QHBoxLayout()
        h_c_bar.addWidget(QLabel("Degree Programs & Academic Branches:"))
        h_c_bar.addStretch()

        btn_add_course = QPushButton("+ Add Course / Branch")
        btn_add_course.setObjectName("btn_primary")
        btn_add_course.clicked.connect(self.on_add_course)
        h_c_bar.addWidget(btn_add_course)
        lay_c.addLayout(h_c_bar)

        self.tbl_courses = QTableWidget()
        self.tbl_courses.setColumnCount(5)
        self.tbl_courses.setHorizontalHeaderLabels(["ID", "Code", "Course / Program Name", "Department", "Duration"])
        self.tbl_courses.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tbl_courses.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tbl_courses.verticalHeader().setDefaultSectionSize(36)
        self.tbl_courses.verticalHeader().setVisible(False)
        lay_c.addWidget(self.tbl_courses)

        self.tabs.addTab(tab_courses, "🎓 Courses && Branches")

        # Tab 2: Semesters
        tab_sems = QWidget()
        lay_s = QVBoxLayout(tab_sems)
        lay_s.setContentsMargins(10, 10, 10, 10)
        lay_s.setSpacing(10)

        h_s_bar = QHBoxLayout()
        h_s_bar.addWidget(QLabel("Configured Academic Semesters:"))
        h_s_bar.addStretch()

        btn_add_sem = QPushButton("+ Add Semester")
        btn_add_sem.setObjectName("btn_primary")
        btn_add_sem.clicked.connect(self.on_add_semester)
        h_s_bar.addWidget(btn_add_sem)
        lay_s.addLayout(h_s_bar)

        self.tbl_semesters = QTableWidget()
        self.tbl_semesters.setColumnCount(5)
        self.tbl_semesters.setHorizontalHeaderLabels(["ID", "Semester", "Academic Year", "Term Type", "Status"])
        self.tbl_semesters.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_semesters.verticalHeader().setDefaultSectionSize(36)
        self.tbl_semesters.verticalHeader().setVisible(False)
        lay_s.addWidget(self.tbl_semesters)

        self.tabs.addTab(tab_sems, "📅 Semesters")

        main_layout.addWidget(self.tabs)

    def refresh_all(self):
        self.refresh_courses()
        self.refresh_semesters()

    def refresh_courses(self):
        courses = self.db.get_courses()
        self.tbl_courses.setRowCount(len(courses))
        for row, c in enumerate(courses):
            it_id = QTableWidgetItem(str(c["id"]))
            it_id.setTextAlignment(Qt.AlignCenter)
            it_code = QTableWidgetItem(c["course_code"])
            it_code.setTextAlignment(Qt.AlignCenter)
            it_code.setFont(QFont("Segoe UI", 9, QFont.Bold))
            it_name = QTableWidgetItem(c["course_name"])
            it_dept = QTableWidgetItem(c.get("department_name") or "General")
            it_dur = QTableWidgetItem(f"{c.get('duration_years', 4)} Years")
            it_dur.setTextAlignment(Qt.AlignCenter)

            self.tbl_courses.setItem(row, 0, it_id)
            self.tbl_courses.setItem(row, 1, it_code)
            self.tbl_courses.setItem(row, 2, it_name)
            self.tbl_courses.setItem(row, 3, it_dept)
            self.tbl_courses.setItem(row, 4, it_dur)

    def refresh_semesters(self):
        sems = self.db.get_semesters()
        self.tbl_semesters.setRowCount(len(sems))
        for row, s in enumerate(sems):
            it_id = QTableWidgetItem(str(s["id"]))
            it_id.setTextAlignment(Qt.AlignCenter)
            it_num = QTableWidgetItem(f"Semester {s['semester_number']}")
            it_num.setTextAlignment(Qt.AlignCenter)
            it_num.setFont(QFont("Segoe UI", 9, QFont.Bold))
            it_yr = QTableWidgetItem(s["academic_year"])
            it_yr.setTextAlignment(Qt.AlignCenter)
            it_term = QTableWidgetItem(f"{s.get('term_type', 'Even')} Term")
            it_term.setTextAlignment(Qt.AlignCenter)
            it_status = QTableWidgetItem("ACTIVE" if s.get("is_active", 1) == 1 else "INACTIVE")
            it_status.setTextAlignment(Qt.AlignCenter)

            self.tbl_semesters.setItem(row, 0, it_id)
            self.tbl_semesters.setItem(row, 1, it_num)
            self.tbl_semesters.setItem(row, 2, it_yr)
            self.tbl_semesters.setItem(row, 3, it_term)
            self.tbl_semesters.setItem(row, 4, it_status)

    def on_add_course(self):
        dlg = AddCourseDialog(self.db, self)
        if dlg.exec():
            d = dlg.get_data()
            try:
                self.db.add_course(
                    course_code=d["course_code"],
                    course_name=d["course_name"],
                    department_id=d["department_id"],
                    duration_years=d["duration_years"]
                )
                self.refresh_courses()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add course: {e}")

    def on_add_semester(self):
        dlg = AddSemesterDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            try:
                self.db.add_semester(
                    semester_number=d["semester_number"],
                    academic_year=d["academic_year"],
                    term_type=d["term_type"]
                )
                self.refresh_semesters()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add semester: {e}")
