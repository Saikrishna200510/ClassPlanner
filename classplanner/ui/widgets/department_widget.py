"""
ClassPlanner - Department Management Widget
Provides full CRUD operations for college academic departments.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QLineEdit, QGroupBox
)
from PySide6.QtCore import Qt
from classplanner.database.db_manager import DatabaseManager


class DepartmentDialog(QDialog):
    """Dialog for adding or editing a department."""
    def __init__(self, parent=None, dept_data=None):
        super().__init__(parent)
        self.dept_data = dept_data
        self.is_edit = dept_data is not None
        self.setWindowTitle("Edit Department" if self.is_edit else "Add New Department")
        self.setFixedSize(420, 220)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. CSE, ECE, MECH")
        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Computer Science & Engineering")
        self.txt_hod = QLineEdit()
        self.txt_hod.setPlaceholderText("e.g. Dr. Arvind Sharma")

        if self.is_edit:
            self.txt_code.setText(self.dept_data.get("code", ""))
            self.txt_name.setText(self.dept_data.get("name", ""))
            self.txt_hod.setText(self.dept_data.get("hod_name", ""))

        form.addRow("Department Code *:", self.txt_code)
        form.addRow("Department Name *:", self.txt_name)
        form.addRow("Head of Department (HOD):", self.txt_hod)
        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save Department")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def on_save(self):
        code = self.txt_code.text().strip().upper()
        name = self.txt_name.text().strip()
        if not code or not name:
            QMessageBox.warning(self, "Validation Error", "Department Code and Name are required fields.")
            return
        self.accept()

    def get_data(self):
        return {
            "code": self.txt_code.text().strip().upper(),
            "name": self.txt_name.text().strip(),
            "hod_name": self.txt_hod.text().strip()
        }


class DepartmentWidget(QWidget):
    """Main department management view."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_departments()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title & Action bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 4)
        top_bar.setAlignment(Qt.AlignVCenter)

        lbl_title = QLabel("Academic Departments")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")

        btn_add = QPushButton("➕ Add Department")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedHeight(28)
        btn_add.clicked.connect(self.on_add_department)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setFixedHeight(28)
        btn_refresh.clicked.connect(self.load_departments)

        top_bar.addWidget(lbl_title)
        top_bar.addStretch()
        top_bar.addWidget(btn_refresh)
        top_bar.addWidget(btn_add)
        layout.addLayout(top_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "ID", "Dept Code", "Department Name", "Head of Dept (HOD)", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

    def load_departments(self):
        depts = self.db.get_departments()
        self.table.setRowCount(len(depts))
        for row, d in enumerate(depts):
            it0 = QTableWidgetItem(str(d["id"]))
            it0.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, it0)

            it1 = QTableWidgetItem(d["code"])
            it1.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, it1)

            it2 = QTableWidgetItem(d["name"])
            it2.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 2, it2)

            it3 = QTableWidgetItem(d.get("hod_name") or "-")
            it3.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
            self.table.setItem(row, 3, it3)

            # Action buttons
            actions_widget = QWidget()
            act_layout = QHBoxLayout(actions_widget)
            act_layout.setContentsMargins(6, 2, 6, 2)
            act_layout.setSpacing(6)
            act_layout.setAlignment(Qt.AlignCenter)

            btn_edit = QPushButton("Edit")
            btn_edit.setProperty("tableAction", "true")
            btn_edit.setFixedSize(54, 24)
            btn_edit.clicked.connect(lambda ch, dept=d: self.on_edit_department(dept))

            btn_del = QPushButton("Delete")
            btn_del.setProperty("tableDelete", "true")
            btn_del.setFixedSize(54, 24)
            btn_del.clicked.connect(lambda ch, dept_id=d["id"], name=d["name"]: self.on_delete_department(dept_id, name))

            act_layout.addWidget(btn_edit)
            act_layout.addWidget(btn_del)
            self.table.setCellWidget(row, 4, actions_widget)

    def on_add_department(self):
        dlg = DepartmentDialog(self)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.add_department(data["code"], data["name"], data["hod_name"])
                QMessageBox.information(self, "Success", f"Department '{data['code']}' added successfully.")
                self.load_departments()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not add department: {e}")

    def on_edit_department(self, dept_data):
        dlg = DepartmentDialog(self, dept_data)
        if dlg.exec():
            data = dlg.get_data()
            try:
                self.db.update_department(dept_data["id"], data["code"], data["name"], data["hod_name"])
                QMessageBox.information(self, "Success", f"Department '{data['code']}' updated.")
                self.load_departments()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update department: {e}")

    def on_delete_department(self, dept_id: int, name: str):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete department '{name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            success, msg = self.db.delete_department(dept_id)
            if success:
                QMessageBox.information(self, "Deleted", msg)
                self.load_departments()
            else:
                QMessageBox.warning(self, "Cannot Delete", msg)

