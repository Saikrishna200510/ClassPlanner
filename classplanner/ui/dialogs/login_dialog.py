"""
ClassPlanner - Multi-College Authentication Dialog
Provides dual login portals for:
1. College Login (College Administrators & Faculty)
2. Super Admin Login (Master Platform Administrator)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFormLayout, QFrame, QTabWidget,
    QWidget, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from classplanner.auth import AuthService, UserRole
from classplanner.database.db_manager import DatabaseManager


class LoginDialog(QDialog):
    """Multi-portal login window for ClassPlanner."""
    login_successful = Signal(object)

    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.auth = AuthService(db)
        self.session = None

        self.setWindowTitle("ClassPlanner — Multi-College Management Login")
        self.setFixedSize(480, 420)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        # ---------------- Brand Header ----------------
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #1A2B4C;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        h_lay = QVBoxLayout(header_frame)
        h_lay.setContentsMargins(10, 8, 10, 8)
        h_lay.setSpacing(3)

        lbl_title = QLabel("ClassPlanner Enterprise")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 13pt; font-weight: bold;")
        lbl_sub = QLabel("Automated Timetable & Multi-College Management System")
        lbl_sub.setStyleSheet("color: #C0D0E8; font-size: 8.5pt;")

        h_lay.addWidget(lbl_title)
        h_lay.addWidget(lbl_sub)
        main_layout.addWidget(header_frame)

        # ---------------- Tabbed Login Portals ----------------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #D0D0D0;
                background: #FFFFFF;
                top: -1px;
            }
            QTabBar::tab {
                background: #E8ECEF;
                border: 1px solid #C0C0C0;
                padding: 7px 18px;
                font-weight: bold;
                font-size: 9pt;
            }
            QTabBar::tab:selected {
                background: #FFFFFF;
                border-bottom: 1px solid #FFFFFF;
                color: #1A2B4C;
            }
        """)

        # Tab 1: College Admin / Faculty Login
        tab_college = QWidget()
        lay_col = QVBoxLayout(tab_college)
        lay_col.setContentsMargins(15, 15, 15, 15)
        lay_col.setSpacing(10)

        lbl_col_info = QLabel("Sign in to access your college timetable portal.")
        lbl_col_info.setStyleSheet("color: #555555; font-size: 8.5pt;")
        lay_col.addWidget(lbl_col_info)

        form_col = QFormLayout()
        form_col.setSpacing(8)

        self.txt_col_email = QLineEdit()
        self.txt_col_email.setPlaceholderText("e.g., admin@gec.edu")
        self.txt_col_email.setText("admin@gec.edu")  # Convenient default
        self.txt_col_email.returnPressed.connect(self.on_college_login)

        self.txt_col_pwd = QLineEdit()
        self.txt_col_pwd.setEchoMode(QLineEdit.Password)
        self.txt_col_pwd.setPlaceholderText("Enter college account password")
        self.txt_col_pwd.setText("College@12345")
        self.txt_col_pwd.returnPressed.connect(self.on_college_login)

        form_col.addRow("Email Address *:", self.txt_col_email)
        form_col.addRow("Password *:", self.txt_col_pwd)
        lay_col.addLayout(form_col)

        btn_col_login = QPushButton("🔑 Login to College Portal")
        btn_col_login.setObjectName("btn_primary")
        btn_col_login.setMinimumHeight(32)
        btn_col_login.setStyleSheet("""
            QPushButton#btn_primary {
                background-color: #004D99;
                color: white;
                font-weight: bold;
                font-size: 9.5pt;
                border-radius: 3px;
                border: 1px solid #003366;
            }
            QPushButton#btn_primary:hover {
                background-color: #003366;
            }
        """)
        btn_col_login.clicked.connect(self.on_college_login)
        lay_col.addWidget(btn_col_login)

        h_col_help = QHBoxLayout()
        btn_col_forgot = QPushButton("Forgot Password?")
        btn_col_forgot.setStyleSheet("border: none; color: #004D99; text-decoration: underline; background: transparent;")
        btn_col_forgot.clicked.connect(lambda: self.on_forgot_password(self.txt_col_email.text()))
        h_col_help.addWidget(btn_col_forgot)
        h_col_help.addStretch()
        lay_col.addLayout(h_col_help)
        lay_col.addStretch()

        self.tabs.addTab(tab_college, "🏫 College Login")

        # Tab 2: Super Admin Login
        tab_admin = QWidget()
        lay_adm = QVBoxLayout(tab_admin)
        lay_adm.setContentsMargins(15, 15, 15, 15)
        lay_adm.setSpacing(10)

        lbl_adm_info = QLabel("Platform Administrator login for multi-college management.")
        lbl_adm_info.setStyleSheet("color: #555555; font-size: 8.5pt;")
        lay_adm.addWidget(lbl_adm_info)

        form_adm = QFormLayout()
        form_adm.setSpacing(8)

        self.txt_adm_email = QLineEdit()
        self.txt_adm_email.setPlaceholderText("e.g., superadmin@classplanner.edu")
        self.txt_adm_email.setText("superadmin@classplanner.edu")
        self.txt_adm_email.returnPressed.connect(self.on_super_admin_login)

        self.txt_adm_pwd = QLineEdit()
        self.txt_adm_pwd.setEchoMode(QLineEdit.Password)
        self.txt_adm_pwd.setPlaceholderText("Enter super admin password")
        self.txt_adm_pwd.setText("Admin@12345")
        self.txt_adm_pwd.returnPressed.connect(self.on_super_admin_login)

        form_adm.addRow("Admin Email *:", self.txt_adm_email)
        form_adm.addRow("Master Password *:", self.txt_adm_pwd)
        lay_adm.addLayout(form_adm)

        btn_adm_login = QPushButton("🛡️ Login as Super Administrator")
        btn_adm_login.setObjectName("btn_primary")
        btn_adm_login.setMinimumHeight(32)
        btn_adm_login.setStyleSheet("""
            QPushButton#btn_primary {
                background-color: #1A2B4C;
                color: white;
                font-weight: bold;
                font-size: 9.5pt;
                border-radius: 3px;
                border: 1px solid #0E1726;
            }
            QPushButton#btn_primary:hover {
                background-color: #0E1726;
            }
        """)
        btn_adm_login.clicked.connect(self.on_super_admin_login)
        lay_adm.addWidget(btn_adm_login)

        h_adm_help = QHBoxLayout()
        btn_adm_forgot = QPushButton("Password Recovery")
        btn_adm_forgot.setStyleSheet("border: none; color: #004D99; text-decoration: underline; background: transparent;")
        btn_adm_forgot.clicked.connect(lambda: self.on_forgot_password(self.txt_adm_email.text()))
        h_adm_help.addWidget(btn_adm_forgot)
        h_adm_help.addStretch()
        lay_adm.addLayout(h_adm_help)
        lay_adm.addStretch()

        self.tabs.addTab(tab_admin, "🛡️ Super Admin")

        main_layout.addWidget(self.tabs)

        # ---------------- Footer Status & Exit ----------------
        btn_bar = QHBoxLayout()
        lbl_status = QLabel("🔒 Offline SQLite & Supabase PostgreSQL Ready")
        lbl_status.setStyleSheet("color: #666666; font-size: 8pt;")
        btn_exit = QPushButton("Exit")
        btn_exit.setFixedWidth(70)
        btn_exit.clicked.connect(self.reject)

        btn_bar.addWidget(lbl_status)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_exit)
        main_layout.addLayout(btn_bar)

    def on_college_login(self):
        email = self.txt_col_email.text().strip()
        pwd = self.txt_col_pwd.text().strip()

        ok, msg, sess = self.auth.login(email, pwd, expected_role=UserRole.COLLEGE_ADMIN)
        if ok:
            self.session = sess
            self.login_successful.emit(sess)
            self.accept()
        else:
            QMessageBox.critical(self, "College Login Failed", msg)

    def on_super_admin_login(self):
        email = self.txt_adm_email.text().strip()
        pwd = self.txt_adm_pwd.text().strip()

        ok, msg, sess = self.auth.login(email, pwd, expected_role=UserRole.SUPER_ADMIN)
        if ok:
            self.session = sess
            self.login_successful.emit(sess)
            self.accept()
        else:
            QMessageBox.critical(self, "Super Admin Login Failed", msg)

    def on_forgot_password(self, email: str):
        target_email = email.strip()
        if not target_email:
            QMessageBox.information(
                self,
                "Password Reset",
                "Please enter your registered email address in the email field first, then click 'Forgot Password?'."
            )
            return

        ok, msg = self.auth.request_password_reset(target_email)
        QMessageBox.information(self, "Password Reset Dispatched", msg)
