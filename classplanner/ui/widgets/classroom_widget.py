"""
ClassPlanner - Classroom Management Widget
Manages lecture halls, specialized laboratories, capacities, and availability.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox,
    QCheckBox
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager
from classplanner.config import ROOM_TYPES, ROOM_TYPE_REGULAR, ROOM_TYPE_LAB


class ClassroomDialog(QDialog):
    """Add / Edit Classroom Dialog."""
    def __init__(self, db: DatabaseManager, parent=None, room_data=None):
        super().__init__(parent)
        self.db = db
        self.room_data = room_data
        self.is_edit = room_data is not None
        self.setWindowTitle("Edit Classroom" if self.is_edit else "Add New Classroom")
        self.setFixedSize(460, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        self.txt_room_no = QLineEdit()
        self.txt_room_no.setPlaceholderText("e.g. LH-101, CS-LAB-1")

        self.txt_building = QLineEdit()
        self.txt_building.setPlaceholderText("e.g. Main Block Floor 1, Tech Wing")

        self.spn_capacity = QSpinBox()
        self.spn_capacity.setRange(10, 500)
        self.spn_capacity.setValue(70)
        self.spn_capacity.setSuffix(" students")

        self.cmb_type = QComboBox()
        self.cmb_type.addItems(ROOM_TYPES)

        self.cmb_dept = QComboBox()
        self.cmb_dept.addItem("-- General / Shared All Departments --", None)
        for d in self.db.get_departments():
            self.cmb_dept.addItem(f"{d['code']} - {d['name']}", d["id"])

        self.chk_available = QCheckBox("Available for Timetable Scheduling")
        self.chk_available.setChecked(True)

        if self.is_edit:
            self.txt_room_no.setText(self.room_data.get("room_number", ""))
            self.txt_building.setText(self.room_data.get("building_name", ""))
            self.spn_capacity.setValue(self.room_data.get("capacity", 70))
            self.cmb_type.setCurrentText(self.room_data.get("room_type", ROOM_TYPE_REGULAR))
            idx = self.cmb_dept.findData(self.room_data.get("department_id"))
            if idx >= 0:
                self.cmb_dept.setCurrentIndex(idx)
            self.chk_available.setChecked(bool(self.room_data.get("is_available", 1)))

        form.addRow("Room Number *:", self.txt_room_no)
        form.addRow("Building / Location *:", self.txt_building)
        form.addRow("Seating Capacity *:", self.spn_capacity)
        form.addRow("Room Type *:", self.cmb_type)
        form.addRow("Department Preference:", self.cmb_dept)
        form.addRow("", self.chk_available)

        layout.addLayout(form)

        # Buttons
        btn_bar = QHBoxLayout()
        btn_save = QPushButton("Save Classroom")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        r_no = self.txt_room_no.text().strip().upper()
        bldg = self.txt_building.text().strip()
        if not r_no or not bldg:
            QMessageBox.warning(self, "Validation Error", "Room Number and Building Location are required.")
            return
        self.accept()

    def get_data(self):
        return {
            "room_number": self.txt_room_no.text().strip().upper(),
            "building_name": self.txt_building.text().strip(),
            "capacity": self.spn_capacity.value(),
            "room_type": self.cmb_type.currentText(),
            "department_id": self.cmb_dept.currentData(),
            "is_available": 1 if self.chk_available.isChecked() else 0
        }


class ClassroomWidget(QWidget):
    """Main classroom management view."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_classrooms()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        top_bar = QHBoxLayout()
        lbl_title = QLabel("Classrooms & Laboratories")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        lbl_filter = QLabel("Filter Type:")
        self.cmb_filter_type = QComboBox()
        self.cmb_filter_type.setMinimumWidth(160)
        self.cmb_filter_type.setFixedHeight(28)
        self.cmb_filter_type.addItem("All Rooms & Labs", None)
        for t in ROOM_TYPES:
            self.cmb_filter_type.addItem(t, t)
        self.cmb_filter_type.currentIndexChanged.connect(self.load_classrooms)

        btn_add = QPushButton("➕ Add Classroom")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self.on_add_classroom)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_classrooms)

        top_bar.setAlignment(Qt.AlignVCenter)
        top_bar.addWidget(lbl_title)
        top_bar.addSpacing(15)
        top_bar.addWidget(lbl_filter)
        top_bar.addWidget(self.cmb_filter_type)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        # Classroom Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Room No.", "Building / Location", "Capacity", "Type", "Assigned Dept", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def load_classrooms(self):
        r_type = self.cmb_filter_type.currentData()
        rooms = self.db.get_classrooms(room_type=r_type)
        self.table.setRowCount(len(rooms))

        for row, r in enumerate(rooms):
            it0 = QTableWidgetItem(r["room_number"])
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(r["building_name"])
            it1.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(f"{r['capacity']} seats")
            it2.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(r["room_type"])
            it3.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, it3)

            it4 = QTableWidgetItem(r.get("dept_code") or "Shared")
            it4.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, it4)

            it5 = QTableWidgetItem("Active" if r["is_available"] else "Inactive")
            it5.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 5, it5)

            actions_widget = QWidget()
            act_lay = QHBoxLayout(actions_widget)
            act_lay.setContentsMargins(6, 2, 6, 2)
            act_lay.setSpacing(6)
            act_lay.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("tableAction", "true")
            btn_edit.setFixedSize(54, 24)
            btn_edit.clicked.connect(lambda ch, room=r: self.on_edit_classroom(room))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("tableDelete", "true")
            btn_del.setFixedSize(54, 24)
            btn_del.clicked.connect(lambda ch, rid=r["id"], rno=r["room_number"]: self.on_delete_classroom(rid, rno))

            act_lay.addWidget(btn_edit)
            act_lay.addWidget(btn_del)
            self.table.setCellWidget(row, 6, actions_widget)

    def on_add_classroom(self):
        dlg = ClassroomDialog(self.db, self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_classroom(
                    data["room_number"], data["building_name"], data["capacity"],
                    data["room_type"], data["department_id"], data["is_available"]
                )
                QMessageBox.information(self, "Success", f"Classroom '{data['room_number']}' added.")
                self.load_classrooms()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add classroom: {e}")

    def on_edit_classroom(self, room_data):
        dlg = ClassroomDialog(self.db, self, room_data)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.update_classroom(
                    room_data["id"], data["room_number"], data["building_name"], data["capacity"],
                    data["room_type"], data["department_id"], data["is_available"]
                )
                QMessageBox.information(self, "Success", f"Classroom '{data['room_number']}' updated.")
                self.load_classrooms()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update classroom: {e}")

    def on_delete_classroom(self, rid: int, rno: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete classroom '{rno}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_classroom(rid)
            if success:
                QMessageBox.information(self, "Deleted", msg)
                self.load_classrooms()
            else:
                QMessageBox.warning(self, "Cannot Delete", msg)

