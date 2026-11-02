"""
ClassPlanner - Super Administrator Dashboard & College Management Widget
Enables platform-wide monitoring, college provisioning, status management,
and credential governance across all colleges.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit,
    QComboBox, QDialog, QFormLayout, QMessageBox, QFrame,
    QSplitter, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from typing import Optional, Dict, Any
from classplanner.database.db_manager import DatabaseManager


class AddCollegeDialog(QDialog):
    """Dialog for registering a new college with initial College Admin credentials."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Register New College Account")
        self.setFixedSize(480, 420)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_hdr = QLabel("<b>Institution Information & Administrator Setup</b>")
        lbl_hdr.setStyleSheet("font-size: 10pt; color: #1A2B4C;")
        layout.addWidget(lbl_hdr)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_name = QLineEdit()
        self.txt_name.setPlaceholderText("e.g. Oxford Institute of Technology")

        self.txt_code = QLineEdit()
        self.txt_code.setPlaceholderText("e.g. OIT-05")

        self.txt_addr = QLineEdit()
        self.txt_addr.setPlaceholderText("e.g. Campus Drive, West Wing")

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("e.g. contact@oit.edu")

        self.txt_phone = QLineEdit()
        self.txt_phone.setPlaceholderText("e.g. +91 98765 00000")

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["active", "inactive"])

        self.txt_admin_name = QLineEdit()
        self.txt_admin_name.setPlaceholderText("e.g. Prof. R. K. Sharma")

        self.txt_admin_email = QLineEdit()
        self.txt_admin_email.setPlaceholderText("e.g. admin@oit.edu")

        self.txt_admin_pwd = QLineEdit()
        self.txt_admin_pwd.setEchoMode(QLineEdit.Password)
        self.txt_admin_pwd.setPlaceholderText("Minimum 6 characters")

        form.addRow("College Name *:", self.txt_name)
        form.addRow("College Code *:", self.txt_code)
        form.addRow("Campus Address:", self.txt_addr)
        form.addRow("Official Email:", self.txt_email)
        form.addRow("Phone Number:", self.txt_phone)
        form.addRow("Account Status *:", self.cmb_status)
        form.addRow("Admin Full Name *:", self.txt_admin_name)
        form.addRow("Admin Email *:", self.txt_admin_email)
        form.addRow("Admin Password *:", self.txt_admin_pwd)

        layout.addLayout(form)

        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save & Register College")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        name = self.txt_name.text().strip()
        code = self.txt_code.text().strip()
        admin_email = self.txt_admin_email.text().strip()
        admin_pwd = self.txt_admin_pwd.text().strip()

        if not name or not code:
            QMessageBox.warning(self, "Validation Error", "College Name and College Code are required.")
            return

        if not admin_email or not admin_pwd:
            QMessageBox.warning(self, "Validation Error", "College Administrator Email and Password are required.")
            return

        if len(admin_pwd) < 6:
            QMessageBox.warning(self, "Validation Error", "Administrator Password must be at least 6 characters.")
            return

        self.accept()

    def get_data(self) -> Dict[str, Any]:
        return {
            "college_name": self.txt_name.text().strip(),
            "college_code": self.txt_code.text().strip().upper(),
            "address": self.txt_addr.text().strip(),
            "email": self.txt_email.text().strip(),
            "phone": self.txt_phone.text().strip(),
            "status": self.cmb_status.currentText(),
            "admin_name": self.txt_admin_name.text().strip(),
            "admin_email": self.txt_admin_email.text().strip().lower(),
            "admin_password": self.txt_admin_pwd.text().strip()
        }


class EditCollegeDialog(QDialog):
    """Dialog for editing an existing college profile."""
    def __init__(self, college_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.data = college_data
        self.setWindowTitle(f"Edit College — {college_data.get('college_name')}")
        self.setFixedSize(450, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        form = QFormLayout()
        form.setSpacing(8)

        self.txt_name = QLineEdit(self.data.get("college_name", ""))
        self.txt_code = QLineEdit(self.data.get("college_code", ""))
        self.txt_addr = QLineEdit(self.data.get("address", ""))
        self.txt_email = QLineEdit(self.data.get("email", ""))
        self.txt_phone = QLineEdit(self.data.get("phone", ""))
        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["active", "inactive"])
        self.cmb_status.setCurrentText(self.data.get("status", "active"))

        form.addRow("College Name *:", self.txt_name)
        form.addRow("College Code *:", self.txt_code)
        form.addRow("Campus Address:", self.txt_addr)
        form.addRow("Official Email:", self.txt_email)
        form.addRow("Phone Number:", self.txt_phone)
        form.addRow("Account Status *:", self.cmb_status)

        layout.addLayout(form)

        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Update College")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.accept)

        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def get_data(self) -> Dict[str, Any]:
        return {
            "college_name": self.txt_name.text().strip(),
            "college_code": self.txt_code.text().strip().upper(),
            "address": self.txt_addr.text().strip(),
            "email": self.txt_email.text().strip(),
            "phone": self.txt_phone.text().strip(),
            "status": self.cmb_status.currentText()
        }


class ResetPasswordDialog(QDialog):
    """Dialog to reset College Admin password."""
    def __init__(self, college_name: str, admin_email: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reset College Admin Password")
        self.setFixedSize(380, 200)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl_info = QLabel(f"Resetting credentials for: <b>{college_name}</b><br>User: <i>{admin_email}</i>")
        lbl_info.setStyleSheet("color: #333333;")
        layout.addWidget(lbl_info)

        form = QFormLayout()
        self.txt_pwd = QLineEdit()
        self.txt_pwd.setEchoMode(QLineEdit.Password)
        self.txt_pwd.setPlaceholderText("Minimum 6 characters")
        form.addRow("New Password *:", self.txt_pwd)
        layout.addLayout(form)

        btn_bar = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Confirm Password Reset")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self.on_save)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_cancel)
        btn_bar.addWidget(btn_save)
        layout.addLayout(btn_bar)

    def on_save(self):
        if len(self.txt_pwd.text().strip()) < 6:
            QMessageBox.warning(self, "Invalid Password", "Password must be at least 6 characters long.")
            return
        self.accept()

    def get_password(self) -> str:
        return self.txt_pwd.text().strip()


class SuperAdminWidget(QWidget):
    """Central Super Admin Monitoring & College Governance Dashboard."""
    college_switched = Signal(int)

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(14)

        # ---------------- Title & Quick Actions ----------------
        h_title = QHBoxLayout()
        lbl_title = QLabel("🛡️ Super Administrator Console — Multi-College Governance")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")
        h_title.addWidget(lbl_title)
        h_title.addStretch()

        btn_refresh = QPushButton("🔄 Refresh Platform Data")
        btn_refresh.clicked.connect(self.refresh_data)
        h_title.addWidget(btn_refresh)
        main_layout.addLayout(h_title)

        # ---------------- KPI Summary Cards ----------------
        kpi_frame = QFrame()
        kpi_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #D0D0D0; border-radius: 4px; padding: 6px;")
        kpi_layout = QHBoxLayout(kpi_frame)
        kpi_layout.setSpacing(10)

        self.card_total = self._create_kpi_card("Total Registered Colleges", "0", "#004D99")
        self.card_active = self._create_kpi_card("Active Colleges", "0", "#008000")
        self.card_inactive = self._create_kpi_card("Inactive Colleges", "0", "#C00000")
        self.card_admins = self._create_kpi_card("Total College Admins", "0", "#663399")
        self.card_faculty = self._create_kpi_card("Total Faculty", "0", "#D97706")
        self.card_timetables = self._create_kpi_card("Generated Timetables", "0", "#0D9488")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_active)
        kpi_layout.addWidget(self.card_inactive)
        kpi_layout.addWidget(self.card_admins)
        kpi_layout.addWidget(self.card_faculty)
        kpi_layout.addWidget(self.card_timetables)
        main_layout.addWidget(kpi_frame)

        # ---------------- College Directory & Management ----------------
        sec_group = QGroupBox("Registered Colleges Directory && Tenancy Control")
        sec_layout = QVBoxLayout(sec_group)
        sec_layout.setSpacing(10)

        # Toolbar
        tb_layout = QHBoxLayout()
        tb_layout.addWidget(QLabel("Search Colleges:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by college name, code, or admin email...")
        self.txt_search.setFixedHeight(28)
        self.txt_search.textChanged.connect(self.refresh_colleges_table)
        tb_layout.addWidget(self.txt_search, 1)

        tb_layout.addWidget(QLabel("Status Filter:"))
        self.cmb_status_filter = QComboBox()
        self.cmb_status_filter.addItems(["All", "Active", "Inactive"])
        self.cmb_status_filter.setMinimumWidth(120)
        self.cmb_status_filter.setFixedHeight(28)
        self.cmb_status_filter.currentTextChanged.connect(self.refresh_colleges_table)
        tb_layout.addWidget(self.cmb_status_filter)

        btn_add_college = QPushButton("+ Add New College")
        btn_add_college.setObjectName("btn_primary")
        btn_add_college.setStyleSheet("""
            QPushButton#btn_primary {
                background-color: #004D99;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 3px;
            }
        """)
        btn_add_college.clicked.connect(self.on_add_college)
        tb_layout.addWidget(btn_add_college)

        sec_layout.addLayout(tb_layout)

        # Colleges Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Code", "College Name", "Campus Location",
            "College Admin", "Status", "Depts", "Faculty", "Actions"
        ])
        self.table.setColumnWidth(0, 28)
        self.table.setColumnWidth(1, 60)
        self.table.setColumnWidth(2, 180)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setColumnWidth(3, 140)
        self.table.setColumnWidth(4, 150)
        self.table.setColumnWidth(5, 65)
        self.table.setColumnWidth(6, 45)
        self.table.setColumnWidth(7, 45)
        self.table.setColumnWidth(8, 245)
        self.table.verticalHeader().setDefaultSectionSize(36)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        sec_layout.addWidget(self.table)

        main_layout.addWidget(sec_group, 1)

    def _create_kpi_card(self, title: str, val: str, color_hex: str) -> QFrame:
        card = QFrame()
        card.setMinimumWidth(110)
        card.setStyleSheet(f"border-left: 4px solid {color_hex}; padding: 4px 6px; background: #FAFAFA;")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(6, 4, 6, 4)
        c_lay.setSpacing(2)

        lbl_v = QLabel(val)
        lbl_v.setStyleSheet(f"font-size: 15pt; font-weight: bold; color: {color_hex};")
        lbl_t = QLabel(title)
        lbl_t.setWordWrap(True)
        lbl_t.setStyleSheet("font-size: 7.5pt; color: #555555; font-weight: bold;")

        c_lay.addWidget(lbl_v)
        c_lay.addWidget(lbl_t)
        card.lbl_v = lbl_v
        return card

    def refresh_data(self):
        """Loads platform statistics and re-populates the directory table."""
        stats = self.db.get_super_admin_stats()
        self.card_total.lbl_v.setText(str(stats["total_colleges"]))
        self.card_active.lbl_v.setText(str(stats["active_colleges"]))
        self.card_inactive.lbl_v.setText(str(stats["inactive_colleges"]))
        self.card_admins.lbl_v.setText(str(stats["total_college_admins"]))
        self.card_faculty.lbl_v.setText(str(stats["total_faculty"]))
        self.card_timetables.lbl_v.setText(str(stats["total_timetables"]))

        self.refresh_colleges_table()

    def refresh_colleges_table(self):
        status_filter = self.cmb_status_filter.currentText()
        search_query = self.txt_search.text().strip()

        colleges = self.db.get_colleges(status_filter=status_filter, search_query=search_query)
        self.table.setRowCount(len(colleges))

        for row, c in enumerate(colleges):
            cid = c["id"]

            it_id = QTableWidgetItem(str(cid))
            it_id.setTextAlignment(Qt.AlignCenter)

            it_code = QTableWidgetItem(c.get("college_code", ""))
            it_code.setTextAlignment(Qt.AlignCenter)
            it_code.setFont(QFont("Segoe UI", 9, QFont.Bold))

            it_name = QTableWidgetItem(c.get("college_name", ""))

            it_addr = QTableWidgetItem(c.get("address", "") or "—")

            admin_str = f"{c.get('admin_name') or 'No Admin'}\n<{c.get('admin_email') or '—'}>"
            it_admin = QTableWidgetItem(admin_str)

            status = c.get("status", "active")
            it_status = QTableWidgetItem(status.upper())
            it_status.setTextAlignment(Qt.AlignCenter)
            if status == "active":
                it_status.setForeground(QColor("#008000"))
            else:
                it_status.setForeground(QColor("#C00000"))
            it_status.setFont(QFont("Segoe UI", 9, QFont.Bold))

            it_depts = QTableWidgetItem(str(c.get("dept_count", 0)))
            it_depts.setTextAlignment(Qt.AlignCenter)

            it_fac = QTableWidgetItem(str(c.get("faculty_count", 0)))
            it_fac.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, it_id)
            self.table.setItem(row, 1, it_code)
            self.table.setItem(row, 2, it_name)
            self.table.setItem(row, 3, it_addr)
            self.table.setItem(row, 4, it_admin)
            self.table.setItem(row, 5, it_status)
            self.table.setItem(row, 6, it_depts)
            self.table.setItem(row, 7, it_fac)

            # Action Buttons: [Edit] [Status Toggle] [Reset Pwd] [Manage / View]
            cell_widget = QWidget()
            h_act = QHBoxLayout(cell_widget)
            h_act.setContentsMargins(4, 2, 4, 2)
            h_act.setSpacing(4)
            h_act.setAlignment(Qt.AlignCenter)

            btn_manage = QPushButton("Manage")
            btn_manage.setFixedWidth(52)
            btn_manage.setToolTip("Switch active college context to view and generate its timetables")
            btn_manage.setStyleSheet("background-color: #004D99; color: white; font-size: 8pt; font-weight: bold; padding: 2px;")
            btn_manage.clicked.connect(lambda _, x=cid: self.on_switch_college(x))

            btn_edit = QPushButton("Edit")
            btn_edit.setFixedWidth(36)
            btn_edit.setStyleSheet("font-size: 8pt; padding: 2px;")
            btn_edit.clicked.connect(lambda _, x=c: self.on_edit_college(x))

            status_btn_txt = "Deactivate" if status == "active" else "Activate"
            btn_status = QPushButton(status_btn_txt)
            btn_status.setFixedWidth(66)
            btn_status.setStyleSheet("font-size: 8pt; padding: 2px;")
            btn_status.clicked.connect(lambda _, x=cid, s=status: self.on_toggle_status(x, s))

            btn_reset = QPushButton("Reset Pwd")
            btn_reset.setFixedWidth(64)
            btn_reset.setStyleSheet("font-size: 8pt; padding: 2px;")
            btn_reset.clicked.connect(lambda _, x=c: self.on_reset_admin_password(x))

            h_act.addWidget(btn_manage)
            h_act.addWidget(btn_edit)
            h_act.addWidget(btn_status)
            h_act.addWidget(btn_reset)

            self.table.setCellWidget(row, 8, cell_widget)

    def on_add_college(self):
        dlg = AddCollegeDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            try:
                new_id = self.db.add_college(
                    college_name=d["college_name"],
                    college_code=d["college_code"],
                    address=d["address"],
                    email=d["email"],
                    phone=d["phone"],
                    status=d["status"],
                    admin_name=d["admin_name"],
                    admin_email=d["admin_email"],
                    admin_password=d["admin_password"]
                )
                QMessageBox.information(
                    self,
                    "College Registered",
                    f"College '{d['college_name']}' [{d['college_code']}] successfully registered!\n"
                    f"Administrator account '{d['admin_email']}' created."
                )
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Registration Error", f"Could not register college: {e}")

    def on_edit_college(self, college_data: Dict[str, Any]):
        dlg = EditCollegeDialog(college_data, self)
        if dlg.exec():
            d = dlg.get_data()
            try:
                self.db.update_college(
                    college_id=college_data["id"],
                    college_name=d["college_name"],
                    college_code=d["college_code"],
                    address=d["address"],
                    email=d["email"],
                    phone=d["phone"],
                    status=d["status"]
                )
                QMessageBox.information(self, "Updated", "College details updated successfully.")
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Update Error", f"Could not update college: {e}")

    def on_toggle_status(self, college_id: int, current_status: str):
        new_status = "inactive" if current_status == "active" else "active"
        prompt = f"Are you sure you want to {new_status.upper()} this college account?\n"
        if new_status == "inactive":
            prompt += "Administrators and faculty belonging to this college will not be able to log in."

        reply = QMessageBox.question(self, "Confirm Status Change", prompt, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.set_college_status(college_id, new_status)
            self.refresh_data()

    def on_reset_admin_password(self, college_data: Dict[str, Any]):
        cid = college_data["id"]
        admin_prof = self.db.get_college_admin(cid)
        if not admin_prof:
            QMessageBox.warning(self, "No Admin Found", "No College Admin account currently assigned to this college.")
            return

        dlg = ResetPasswordDialog(college_data["college_name"], admin_prof["email"], self)
        if dlg.exec():
            from classplanner.auth import AuthService
            auth = AuthService(self.db)
            new_pwd = dlg.get_password()
            ok, msg = auth.reset_password_by_admin(admin_prof["id"], new_pwd)
            if ok:
                QMessageBox.information(self, "Password Reset", f"Administrator password for {admin_prof['email']} reset successfully.")
            else:
                QMessageBox.critical(self, "Reset Error", msg)

    def on_switch_college(self, college_id: int):
        """Notifies main window to switch scoped timetable management to this college."""
        self.college_switched.emit(college_id)
