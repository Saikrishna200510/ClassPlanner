"""
ClassPlanner - Student Section Management Widget
Manages student cohorts, section strength, and assigned home lecture classrooms.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager


class SectionDialog(QDialog):
    """Add / Edit Section Dialog."""
    def __init__(self, db: DatabaseManager, parent=None, section_data=None):
        super().__init__(parent)
        self.db = db
        self.section_data = section_data
        self.is_edit = section_data is not None
        self.setWindowTitle("Edit Section" if self.is_edit else "Add New Section")
        self.setFixedSize(460, 340)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.cmb_dept = QComboBox()
        self.depts = self.db.get_departments()
        for d in self.depts:
            self.cmb_dept.addItem(f"{d['code']} - {d['name']}", d["id"])

        self.txt_year = QLineEdit()
        self.txt_year.setText(self.db.get_setting("academic_year", "2026-2027"))

        self.spn_sem = QSpinBox()
        self.spn_sem.setRange(1, 8)
        self.spn_sem.setValue(4)
        self.spn_sem.setPrefix("Semester ")

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. CSE-4A, MECH-2B")

        self.spn_strength = QSpinBox()
        self.spn_strength.setRange(10, 200)
        self.spn_strength.setValue(60)
        self.spn_strength.setSuffix(" students")

        self.cmb_room = QComboBox()
        self.cmb_room.addItem("-- None / Assign Dynamically --", None)
        for r in self.db.get_classrooms():
            self.cmb_room.addItem(f"{r['room_number']} ({r['capacity']} seats - {r['room_type']})", r["id"])

        if self.is_edit:
            idx = self.cmb_dept.findData(self.section_data.get("department_id"))
            if idx >= 0:
                self.cmb_dept.setCurrentIndex(idx)
            self.txt_year.setText(self.section_data.get("academic_year", ""))
            self.spn_sem.setValue(self.section_data.get("semester", 4))
            self.txt_name.setText(self.section_data.get("section_name", ""))
            self.spn_strength.setValue(self.section_data.get("student_count", 60))
            r_idx = self.cmb_room.findData(self.section_data.get("assigned_classroom_id"))
            if r_idx >= 0:
                self.cmb_room.setCurrentIndex(r_idx)

        form.addRow("Department *:", self.cmb_dept)
        form.addRow("Academic Year *:", self.txt_year)
        form.addRow("Semester *:", self.spn_sem)
        form.addRow("Section Name *:", self.txt_name)
        form.addRow("Number of Students *:", self.spn_strength)
        form.addRow("Default Home Classroom:", self.cmb_room)

        layout.addLayout(form)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_save = QPushButton("Save Section")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        name = self.txt_name.text().strip().upper()
        year = self.txt_year.text().strip()
        if not name or not year:
            QMessageBox.warning(self, "Validation Error", "Section Name and Academic Year are required.")
            return
        self.accept()

    def get_data(self):
        return {
            "department_id": self.cmb_dept.currentData(),
            "academic_year": self.txt_year.text().strip(),
            "semester": self.spn_sem.value(),
            "section_name": self.txt_name.text().strip().upper(),
            "student_count": self.spn_strength.value(),
            "assigned_classroom_id": self.cmb_room.currentData()
        }


class SectionWidget(QWidget):
    """Main student sections management table view."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_sections()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        lbl_title = QLabel("Student Sections")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        lbl_filter = QLabel("Department:")
        self.cmb_filter_dept = QComboBox()
        self.cmb_filter_dept.setMinimumWidth(140)
        self.cmb_filter_dept.setFixedHeight(28)
        self.cmb_filter_dept.addItem("All Departments", None)
        for d in self.db.get_departments():
            self.cmb_filter_dept.addItem(d["code"], d["id"])
        self.cmb_filter_dept.currentIndexChanged.connect(self.load_sections)

        btn_add = QPushButton("➕ Add Section")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self.on_add_section)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_sections)

        top_bar.setAlignment(Qt.AlignVCenter)
        top_bar.addWidget(lbl_title)
        top_bar.addSpacing(15)
        top_bar.addWidget(lbl_filter)
        top_bar.addWidget(self.cmb_filter_dept)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        # Sections Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Section Name", "Department", "Semester", "Academic Year", "Strength", "Assigned Home Room", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def load_sections(self):
        dept_id = self.cmb_filter_dept.currentData()
        sections = self.db.get_sections(department_id=dept_id)
        self.table.setRowCount(len(sections))

        for row, s in enumerate(sections):
            it0 = QTableWidgetItem(s["section_name"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(s.get("dept_code") or "")
            it1.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(f"Sem {s['semester']}")
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(s["academic_year"])
            it3.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, it3)

            it4 = QTableWidgetItem(f"{s['student_count']} students")
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            it5 = QTableWidgetItem(s.get("room_number") or "- Not Set -")
            it5.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 5, it5)

            actions_widget = QWidget()
            act_lay = QHBoxLayout(actions_widget)
            act_lay.setContentsMargins(6, 2, 6, 2)
            act_lay.setSpacing(6)
            act_lay.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("tableAction", "true")
            btn_edit.setFixedSize(54, 24)
            btn_edit.clicked.connect(lambda ch, sec=s: self.on_edit_section(sec))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("tableDelete", "true")
            btn_del.setFixedSize(54, 24)
            btn_del.clicked.connect(lambda ch, sid=s["id"], sname=s["section_name"]: self.on_delete_section(sid, sname))

            act_lay.addWidget(btn_edit)
            act_lay.addWidget(btn_del)
            self.table.setCellWidget(row, 6, actions_widget)

    def on_add_section(self):
        if not self.db.get_departments():
            QMessageBox.warning(self, "No Departments", "Please add departments before creating student sections.")
            return

        dlg = SectionDialog(self.db, self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_section(
                    data["department_id"], data["academic_year"], data["semester"],
                    data["section_name"], data["student_count"], data["assigned_classroom_id"]
                )
                QMessageBox.information(self, "Success", f"Section '{data['section_name']}' created.")
                self.load_sections()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add section: {e}")

    def on_edit_section(self, sec_data):
        dlg = SectionDialog(self.db, self, sec_data)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.update_section(
                    sec_data["id"], data["department_id"], data["academic_year"], data["semester"],
                    data["section_name"], data["student_count"], data["assigned_classroom_id"]
                )
                QMessageBox.information(self, "Success", f"Section '{data['section_name']}' updated.")
                self.load_sections()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update section: {e}")

    def on_delete_section(self, sid: int, sname: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete section '{sname}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_section(sid)
            if success:
                QMessageBox.information(self, "Deleted", msg)
                self.load_sections()
            else:
                QMessageBox.warning(self, "Cannot Delete", msg)

