"""
ClassPlanner - Faculty Management Widget
Handles faculty member details, maximum teaching limits, and weekly slot availability matrix.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QCheckBox, QGroupBox, QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager
from classplanner.config import FACULTY_DESIGNATIONS, DAYS_OF_WEEK


class FacultyAvailabilityDialog(QDialog):
    """Interactive grid for setting faculty available days and periods."""
    def __init__(self, faculty_id: int, faculty_name: str, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.faculty_id = faculty_id
        self.faculty_name = faculty_name
        self.db = db
        self.setWindowTitle(f"Availability Matrix — {faculty_name}")
        self.setMinimumSize(680, 420)
        self.checkboxes = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_desc = QLabel(
            f"Configure working slots for <b>{self.faculty_name}</b>.<br/>"
            "Uncheck periods where faculty is on leave, engaged in administrative duties, or off-duty."
        )
        layout.addWidget(lbl_desc)

        # Quick action buttons
        quick_bar = QHBoxLayout()
        btn_all = QPushButton("Select All Slots")
        btn_all.clicked.connect(self.select_all)
        btn_clear = QPushButton("Clear All Slots")
        btn_clear.clicked.connect(self.clear_all)

        quick_bar.addWidget(btn_all)
        quick_bar.addWidget(btn_clear)
        quick_bar.addStretch()
        layout.addLayout(quick_bar)

        # Matrix Table
        working_days = self.db.get_active_working_days()
        teaching_slots = self.db.get_teaching_slots()
        current_avail = self.db.get_faculty_availability(self.faculty_id)

        self.table = QTableWidget()
        self.table.setRowCount(len(teaching_slots))
        self.table.setColumnCount(len(working_days))
        self.table.setHorizontalHeaderLabels(working_days)
        self.table.setVerticalHeaderLabels([f"{s['slot_name']}\n({s['start_time']}-{s['end_time']})" for s in teaching_slots])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        for col, day in enumerate(working_days):
            for row, slot in enumerate(teaching_slots):
                s_num = slot["slot_number"]
                is_avail = current_avail.get((day, s_num), True)

                cb = QCheckBox("Available")
                cb.setChecked(is_avail)
                self.checkboxes[(day, s_num)] = cb

                # Center align widget in cell
                cell_w = QWidget()
                cell_lay = QHBoxLayout(cell_w)
                cell_lay.setContentsMargins(4, 2, 4, 2)
                cell_lay.setAlignment(Qt.AlignCenter)
                cell_lay.addWidget(cb)
                self.table.setCellWidget(row, col, cell_w)

        layout.addWidget(self.table)

        # Dialog buttons
        bottom_bar = QHBoxLayout()
        btn_save = QPushButton("Save Availability")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        bottom_bar.addStretch()
        bottom_bar.addWidget(btn_cancel)
        bottom_bar.addWidget(btn_save)
        layout.addLayout(bottom_bar)

    def select_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def clear_all(self):
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def on_save(self):
        avail_map = {key: cb.isChecked() for key, cb in self.checkboxes.items()}
        self.db.set_faculty_availability(self.faculty_id, avail_map)
        QMessageBox.information(self, "Saved", "Faculty availability schedule saved.")
        self.accept()


class FacultyDialog(QDialog):
    """Add / Edit Faculty Details Dialog."""
    def __init__(self, db: DatabaseManager, parent=None, faculty_data=None):
        super().__init__(parent)
        self.db = db
        self.faculty_data = faculty_data
        self.is_edit = faculty_data is not None
        self.setWindowTitle("Edit Faculty Member" if self.is_edit else "Add New Faculty Member")
        self.setFixedSize(480, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.txt_fac_id = QLineEdit()
        self.txt_fac_id.setPlaceholderText("e.g. FAC-CSE-01")

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Dr. Arvind Sharma")

        self.cmb_dept = QComboBox()
        self.depts = self.db.get_departments()
        for d in self.depts:
            self.cmb_dept.addItem(f"{d['code']} - {d['name']}", d["id"])

        self.cmb_desig = QComboBox()
        self.cmb_desig.addItems(FACULTY_DESIGNATIONS)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("e.g. sharma@college.edu")

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("e.g. 9876543210")

        self.spn_day_hours = QSpinBox()
        self.spn_day_hours.setRange(1, 8)
        self.spn_day_hours.setValue(4)
        self.spn_day_hours.setSuffix(" hrs/day")

        self.spn_week_hours = QSpinBox()
        self.spn_week_hours.setRange(1, 40)
        self.spn_week_hours.setValue(18)
        self.spn_week_hours.setSuffix(" hrs/week")

        self.chk_active = QCheckBox("Active for Timetable Scheduling")
        self.chk_active.setChecked(True)

        if self.is_edit:
            self.txt_fac_id.setText(self.faculty_data.get("faculty_id", ""))
            self.txt_name.setText(self.faculty_data.get("name", ""))
            idx = self.cmb_dept.findData(self.faculty_data.get("department_id"))
            if idx >= 0:
                self.cmb_dept.setCurrentIndex(idx)
            self.cmb_desig.setCurrentText(self.faculty_data.get("designation", ""))
            self.txt_email.setText(self.faculty_data.get("email", ""))
            self.txt_phone.setText(self.faculty_data.get("phone", ""))
            self.spn_day_hours.setValue(self.faculty_data.get("max_hours_per_day", 4))
            self.spn_week_hours.setValue(self.faculty_data.get("max_hours_per_week", 18))
            self.chk_active.setChecked(bool(self.faculty_data.get("is_active", 1)))

        form.addRow("Faculty ID *:", self.txt_fac_id)
        form.addRow("Full Name *:", self.txt_name)
        form.addRow("Department *:", self.cmb_dept)
        form.addRow("Designation *:", self.cmb_desig)
        form.addRow("Email Address:", self.txt_email)
        form.addRow("Phone Number:", self.txt_phone)
        form.addRow("Max Teaching Hours/Day *:", self.spn_day_hours)
        form.addRow("Max Teaching Hours/Week *:", self.spn_week_hours)
        form.addRow("", self.chk_active)

        layout.addLayout(form)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_save = QPushButton("Save Faculty")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        fid = self.txt_fac_id.text().strip()
        name = self.txt_name.text().strip()
        if not fid or not name:
            QMessageBox.warning(self, "Validation Error", "Faculty ID and Full Name are required.")
            return
        if self.cmb_dept.currentIndex() < 0:
            QMessageBox.warning(self, "Validation Error", "Please select a department.")
            return
        self.accept()

    def get_data(self):
        return {
            "faculty_id": self.txt_fac_id.text().strip(),
            "name": self.txt_name.text().strip(),
            "department_id": self.cmb_dept.currentData(),
            "designation": self.cmb_desig.currentText(),
            "email": self.txt_email.text().strip(),
            "phone": self.txt_phone.text().strip(),
            "max_hours_per_day": self.spn_day_hours.value(),
            "max_hours_per_week": self.spn_week_hours.value(),
            "is_active": 1 if self.chk_active.isChecked() else 0
        }


class FacultyWidget(QWidget):
    """Main faculty members management table and controls."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_faculty()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Top Control Bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 4)
        top_bar.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel("Faculty Members")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        lbl_filter = QLabel("Filter Department:")
        self.cmb_filter_dept = QComboBox()
        self.cmb_filter_dept.setMinimumWidth(180)
        self.cmb_filter_dept.setFixedHeight(28)
        self.cmb_filter_dept.addItem("All Departments", None)
        for d in self.db.get_departments():
            self.cmb_filter_dept.addItem(f"{d['code']} - {d['name']}", d["id"])
        self.cmb_filter_dept.currentIndexChanged.connect(self.load_faculty)

        btn_add = QPushButton("➕ Add Faculty")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self.on_add_faculty)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_faculty)

        top_bar.addWidget(lbl_title)
        top_bar.addSpacing(20)
        top_bar.addWidget(lbl_filter)
        top_bar.addWidget(self.cmb_filter_dept)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        # Faculty Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Faculty ID", "Name", "Department", "Designation",
            "Max Daily", "Max Weekly", "Availability", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 120)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def load_faculty(self):
        dept_id = self.cmb_filter_dept.currentData()
        faculty_list = self.db.get_faculty_list(department_id=dept_id)
        self.table.setRowCount(len(faculty_list))

        for row, f in enumerate(faculty_list):
            it0 = QTableWidgetItem(f["faculty_id"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(f["name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(f.get("dept_code") or "")
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(f.get("designation") or "")
            it3.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 3, it3)

            it4 = QTableWidgetItem(f"{f['max_hours_per_day']} hrs")
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            it5 = QTableWidgetItem(f"{f['max_hours_per_week']} hrs")
            it5.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, it5)

            # Availability button
            btn_avail = QPushButton("Availability...")
            btn_avail.setProperty("tableAction", "true")
            btn_avail.setFixedSize(100, 24)
            btn_avail.clicked.connect(lambda ch, fid=f["id"], fname=f["name"]: self.on_open_availability(fid, fname))
            
            w_avail = QWidget()
            lay_avail = QHBoxLayout(w_avail)
            lay_avail.setContentsMargins(4, 2, 4, 2)
            lay_avail.setAlignment(Qt.AlignCenter)
            lay_avail.addWidget(btn_avail)
            self.table.setCellWidget(row, 6, w_avail)

            # Actions Widget
            actions_widget = QWidget()
            act_lay = QHBoxLayout(actions_widget)
            act_lay.setContentsMargins(6, 2, 6, 2)
            act_lay.setSpacing(6)
            act_lay.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("tableAction", "true")
            btn_edit.setFixedSize(54, 24)
            btn_edit.clicked.connect(lambda ch, fac=f: self.on_edit_faculty(fac))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("tableDelete", "true")
            btn_del.setFixedSize(54, 24)
            btn_del.clicked.connect(lambda ch, fid=f["id"], fname=f["name"]: self.on_delete_faculty(fid, fname))

            act_lay.addWidget(btn_edit)
            act_lay.addWidget(btn_del)
            self.table.setCellWidget(row, 7, actions_widget)

    def on_add_faculty(self):
        if not self.db.get_departments():
            QMessageBox.warning(self, "No Departments", "Please add at least one department first.")
            return

        dlg = FacultyDialog(self.db, self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_faculty(
                    data["faculty_id"], data["name"], data["department_id"],
                    data["designation"], data["email"], data["phone"],
                    data["max_hours_per_day"], data["max_hours_per_week"], data["is_active"]
                )
                QMessageBox.information(self, "Success", f"Faculty member '{data['name']}' added.")
                self.load_faculty()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add faculty: {e}")

    def on_edit_faculty(self, fac_data):
        dlg = FacultyDialog(self.db, self, fac_data)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.update_faculty(
                    fac_data["id"], data["faculty_id"], data["name"], data["department_id"],
                    data["designation"], data["email"], data["phone"],
                    data["max_hours_per_day"], data["max_hours_per_week"], data["is_active"]
                )
                QMessageBox.information(self, "Success", f"Faculty member '{data['name']}' updated.")
                self.load_faculty()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update faculty: {e}")

    def on_delete_faculty(self, fid: int, fname: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete faculty member '{fname}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_faculty(fid)
            if success:
                QMessageBox.information(self, "Deleted", msg)
                self.load_faculty()
            else:
                QMessageBox.warning(self, "Cannot Delete", msg)

    def on_open_availability(self, faculty_id: int, faculty_name: str):
        dlg = FacultyAvailabilityDialog(faculty_id, faculty_name, self.db, self)
        dlg.exec()

