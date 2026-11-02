"""
ClassPlanner - Subject Management Widget
Handles course curriculum subjects, theory vs practical types, weekly hours, and faculty assignments.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager
from classplanner.config import SUBJECT_TYPES, SUBJECT_TYPE_THEORY, SUBJECT_TYPE_PRACTICAL


class SubjectDialog(QDialog):
    """Add / Edit Subject Dialog."""
    def __init__(self, db: DatabaseManager, parent=None, subject_data=None):
        super().__init__(parent)
        self.db = db
        self.subject_data = subject_data
        self.is_edit = subject_data is not None
        self.setWindowTitle("Edit Subject" if self.is_edit else "Add New Subject")
        self.setFixedSize(500, 480)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. CS401, EC402")

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Operating Systems")

        self.cmb_dept = QComboBox()
        self.depts = self.db.get_departments()
        for d in self.depts:
            self.cmb_dept.addItem(f"{d['code']} - {d['name']}", d["id"])
        self.cmb_dept.currentIndexChanged.connect(self.on_dept_changed)

        self.spn_semester = QSpinBox()
        self.spn_semester.setRange(1, 8)
        self.spn_semester.setValue(4)
        self.spn_semester.setPrefix("Semester ")

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(SUBJECT_TYPES)
        self.cmb_type.currentIndexChanged.connect(self.on_type_changed)

        self.spn_hours = QSpinBox()
        self.spn_hours.setRange(1, 10)
        self.spn_hours.setValue(4)
        self.spn_hours.setSuffix(" periods/week")

        self.spn_consec = QSpinBox()
        self.spn_consec.setRange(1, 4)
        self.spn_consec.setValue(1)
        self.spn_consec.setSuffix(" consecutive period(s)")

        self.chk_lab = QCheckBox("Requires Laboratory Classroom")

        self.cmb_faculty = QComboBox()
        self.on_dept_changed()

        if self.is_edit:
            self.txt_code.setText(self.subject_data.get("code", ""))
            self.txt_name.setText(self.subject_data.get("name", ""))
            idx = self.cmb_dept.findData(self.subject_data.get("department_id"))
            if idx >= 0:
                self.cmb_dept.setCurrentIndex(idx)
            self.spn_semester.setValue(self.subject_data.get("semester", 4))
            self.cmb_type.setCurrentText(self.subject_data.get("subject_type", SUBJECT_TYPE_THEORY))
            self.spn_hours.setValue(self.subject_data.get("weekly_hours", 4))
            self.spn_consec.setValue(self.subject_data.get("consecutive_periods", 1))
            self.chk_lab.setChecked(bool(self.subject_data.get("requires_lab", 0)))
            f_idx = self.cmb_faculty.findData(self.subject_data.get("default_faculty_id"))
            if f_idx >= 0:
                self.cmb_faculty.setCurrentIndex(f_idx)

        form.addRow("Subject Code *:", self.txt_code)
        form.addRow("Subject Name *:", self.txt_name)
        form.addRow("Department *:", self.cmb_dept)
        form.addRow("Semester *:", self.spn_semester)
        form.addRow("Subject Type *:", self.cmb_type)
        form.addRow("Weekly Hours/Periods *:", self.spn_hours)
        form.addRow("Consecutive Periods:", self.spn_consec)
        form.addRow("", self.chk_lab)
        form.addRow("Assigned Faculty *:", self.cmb_faculty)

        layout.addLayout(form)

        # Dialog Buttons
        btn_bar = QHBoxLayout()
        btn_save = QPushButton("Save Subject")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_type_changed(self):
        is_practical = self.cmb_type.currentText() == SUBJECT_TYPE_PRACTICAL
        if is_practical:
            self.chk_lab.setChecked(True)
            self.spn_consec.setValue(3)
            self.spn_hours.setValue(3)
        else:
            self.chk_lab.setChecked(False)
            self.spn_consec.setValue(1)
            self.spn_hours.setValue(4)

    def on_dept_changed(self):
        dept_id = self.cmb_dept.currentData()
        self.cmb_faculty.clear()
        if dept_id:
            fac_list = self.db.get_faculty_list(department_id=dept_id)
            for f in fac_list:
                self.cmb_faculty.addItem(f"{f['name']} ({f['faculty_id']})", f["id"])

    def on_save(self):
        code = self.txt_code.text().strip().upper()
        name = self.txt_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Validation Error", "Subject Code and Name are required.")
            return
        if self.cmb_faculty.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please assign a faculty member to this subject.")
            return
        self.accept()

    def get_data(self):
        return {
            "code": self.txt_code.text().strip().upper(),
            "name": self.txt_name.text().strip(),
            "department_id": self.cmb_dept.currentData(),
            "semester": self.spn_semester.value(),
            "subject_type": self.cmb_type.currentText(),
            "weekly_hours": self.spn_hours.value(),
            "consecutive_periods": self.spn_consec.value(),
            "requires_lab": 1 if self.chk_lab.isChecked() else 0,
            "default_faculty_id": self.cmb_faculty.currentData()
        }


class SubjectWidget(QWidget):
    """Main subject management table view and filtering."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_subjects()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Filters and Action Bar
        top_bar = QHBoxLayout()
        lbl_title = QLabel("Subject Curriculum")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        lbl_filter_dept = QLabel("Department:")
        self.cmb_filter_dept = QComboBox()
        self.cmb_filter_dept.setMinimumWidth(140)
        self.cmb_filter_dept.setFixedHeight(28)
        self.cmb_filter_dept.addItem("All Departments", None)
        for d in self.db.get_departments():
            self.cmb_filter_dept.addItem(f"{d['code']}", d["id"])
        self.cmb_filter_dept.currentIndexChanged.connect(self.load_subjects)

        lbl_filter_sem = QLabel("Semester:")
        self.cmb_filter_sem = QComboBox()
        self.cmb_filter_sem.setMinimumWidth(120)
        self.cmb_filter_sem.setFixedHeight(28)
        self.cmb_filter_sem.addItem("All Semesters", None)
        for s in range(1, 9):
            self.cmb_filter_sem.addItem(f"Sem {s}", s)
        self.cmb_filter_sem.currentIndexChanged.connect(self.load_subjects)

        btn_add = QPushButton("➕ Add Subject")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self.on_add_subject)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_subjects)

        top_bar.setAlignment(Qt.AlignVCenter)
        top_bar.addWidget(lbl_title)
        top_bar.addSpacing(15)
        top_bar.addWidget(lbl_filter_dept)
        top_bar.addWidget(self.cmb_filter_dept)
        top_bar.addWidget(lbl_filter_sem)
        top_bar.addWidget(self.cmb_filter_sem)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        # Subject Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Code", "Subject Name", "Dept", "Sem", "Type", "Hrs/Wk", "Assigned Faculty", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def load_subjects(self):
        dept_id = self.cmb_filter_dept.currentData()
        sem = self.cmb_filter_sem.currentData()
        subjects = self.db.get_subjects(department_id=dept_id, semester=sem)
        self.table.setRowCount(len(subjects))

        for row, s in enumerate(subjects):
            it0 = QTableWidgetItem(s["code"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(s["name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(s.get("dept_code") or "")
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f"Sem {s['semester']}")
            it3.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, it3)

            it4 = QTableWidgetItem(s["subject_type"])
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            it5 = QTableWidgetItem(f"{s['weekly_hours']} hrs")
            it5.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, it5)

            it6 = QTableWidgetItem(s.get("faculty_name") or "- Not Assigned -")
            it6.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 6, it6)

            # Actions
            actions_widget = QWidget()
            act_lay = QHBoxLayout(actions_widget)
            act_lay.setContentsMargins(6, 2, 6, 2)
            act_lay.setSpacing(6)
            act_lay.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("tableAction", "true")
            btn_edit.setFixedSize(54, 24)
            btn_edit.clicked.connect(lambda ch, sub=s: self.on_edit_subject(sub))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("tableDelete", "true")
            btn_del.setFixedSize(54, 24)
            btn_del.clicked.connect(lambda ch, sid=s["id"], sname=s["name"]: self.on_delete_subject(sid, sname))

            act_lay.addWidget(btn_edit)
            act_lay.addWidget(btn_del)
            self.table.setCellWidget(row, 7, actions_widget)

    def on_add_subject(self):
        if not self.db.get_departments():
            QMessageBox.warning(self, "No Departments", "Please add departments before creating subjects.")
            return

        dlg = SubjectDialog(self.db, self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_subject(
                    data["code"], data["name"], data["department_id"], data["semester"],
                    data["subject_type"], data["weekly_hours"], data["consecutive_periods"],
                    data["requires_lab"], data["default_faculty_id"]
                )
                QMessageBox.information(self, "Success", f"Subject '{data['code']}' added.")
                self.load_subjects()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add subject: {e}")

    def on_edit_subject(self, sub_data):
        dlg = SubjectDialog(self.db, self, sub_data)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.update_subject(
                    sub_data["id"], data["code"], data["name"], data["department_id"], data["semester"],
                    data["subject_type"], data["weekly_hours"], data["consecutive_periods"],
                    data["requires_lab"], data["default_faculty_id"]
                )
                QMessageBox.information(self, "Success", f"Subject '{data['code']}' updated.")
                self.load_subjects()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update subject: {e}")

    def on_delete_subject(self, sid: int, sname: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete subject '{sname}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_subject(sid)
            if success:
                QMessageBox.information(self, "Deleted", msg)
                self.load_subjects()
            else:
                QMessageBox.warning(self, "Cannot Delete", msg)

