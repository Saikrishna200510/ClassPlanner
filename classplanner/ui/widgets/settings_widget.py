"""
ClassPlanner - Settings & Institution Profile Widget
Manages college institution details, admin password security, backups, and restores.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QLineEdit, QCheckBox, QMessageBox,
    QFileDialog
)
import hashlib
from classplanner.database.db_manager import DatabaseManager
from classplanner.database.backup import create_backup, restore_backup, reset_database
from classplanner.database.sample_data import load_sample_college_data


class SettingsWidget(QWidget):
    """Institutional configuration, security, and database maintenance."""
    def __init__(self, db: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        lbl_title = QLabel("Application & Institutional Settings")
        lbl_title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #1A2B4C;")
        main_layout.addWidget(lbl_title)

        # 1. Institution Details
        inst_group = QGroupBox("College / University Details")
        form_inst = QFormLayout(inst_group)

        self.txt_inst_name = QLineEdit()
        self.txt_inst_addr = QLineEdit()
        self.txt_acad_year = QLineEdit()
        self.txt_acad_term = QLineEdit()

        form_inst.addRow("Institution Name *:", self.txt_inst_name)
        form_inst.addRow("Institution Address *:", self.txt_inst_addr)
        form_inst.addRow("Active Academic Year *:", self.txt_acad_year)
        form_inst.addRow("Active Term / Semester *:", self.txt_acad_term)

        btn_save_inst = QPushButton("Save Institution Details")
        btn_save_inst.setObjectName("btn_primary")
        btn_save_inst.clicked.connect(self.save_institution_settings)
        form_inst.addRow("", btn_save_inst)

        main_layout.addWidget(inst_group)

        # 2. Administrator Access & Security
        sec_group = QGroupBox("Security & Access Protection")
        form_sec = QFormLayout(sec_group)

        self.chk_require_login = QCheckBox("Enable Administrator Login Protection")
        self.txt_admin_pwd = QLineEdit()
        self.txt_admin_pwd.setEchoMode(QLineEdit.Password)
        self.txt_admin_pwd.setPlaceholderText("Enter new administrator password (leave blank to keep current)")

        form_sec.addRow("", self.chk_require_login)
        form_sec.addRow("Admin Password:", self.txt_admin_pwd)

        btn_save_sec = QPushButton("Update Security Credentials")
        btn_save_sec.clicked.connect(self.save_security_settings)
        form_sec.addRow("", btn_save_sec)

        main_layout.addWidget(sec_group)

        # 3. Supabase Cloud PostgreSQL Integration
        cloud_group = QGroupBox("☁️ Supabase PostgreSQL Cloud Integration")
        form_cloud = QFormLayout(cloud_group)

        self.txt_cloud_host = QLineEdit("db.lmllravkxpdqigkfprgx.supabase.co")
        self.txt_cloud_port = QLineEdit("5432")
        self.txt_cloud_db = QLineEdit("postgres")
        self.txt_cloud_user = QLineEdit("postgres")
        self.txt_cloud_pwd = QLineEdit("Krishna@6301986030")
        self.txt_cloud_pwd.setEchoMode(QLineEdit.Password)

        self.txt_cloud_uri = QLineEdit("postgresql://postgres:Krishna%406301986030@db.lmllravkxpdqigkfprgx.supabase.co:5432/postgres")
        self.txt_cloud_uri.setReadOnly(True)

        form_cloud.addRow("Supabase Host:", self.txt_cloud_host)
        form_cloud.addRow("Port:", self.txt_cloud_port)
        form_cloud.addRow("Database:", self.txt_cloud_db)
        form_cloud.addRow("Username:", self.txt_cloud_user)
        form_cloud.addRow("Password:", self.txt_cloud_pwd)
        form_cloud.addRow("Percent-Encoded URI:", self.txt_cloud_uri)

        cloud_btn_bar = QHBoxLayout()
        btn_test_cloud = QPushButton("🔌 Test Supabase Connection")
        btn_test_cloud.clicked.connect(self.on_test_supabase)

        btn_push_cloud = QPushButton("☁️ Push Local Data to Supabase")
        btn_push_cloud.setObjectName("btn_primary")
        btn_push_cloud.clicked.connect(self.on_push_supabase)

        cloud_btn_bar.addWidget(btn_test_cloud)
        cloud_btn_bar.addWidget(btn_push_cloud)
        cloud_btn_bar.addStretch()
        form_cloud.addRow("", cloud_btn_bar)

        main_layout.addWidget(cloud_group)

        # 4. Database Maintenance (Backup, Restore, Reset)
        db_group = QGroupBox("Database Maintenance & Local Backup")
        h_db = QHBoxLayout(db_group)
        h_db.setSpacing(10)

        btn_backup = QPushButton("💾 Backup Database")
        btn_backup.clicked.connect(self.on_backup_db)

        btn_restore = QPushButton("📂 Restore Database")
        btn_restore.clicked.connect(self.on_restore_db)

        btn_sample = QPushButton("📥 Load Sample College Data")
        btn_sample.clicked.connect(self.on_load_sample)

        btn_reset = QPushButton("⚠️ Reset / Wipe All Data")
        btn_reset.setStyleSheet("color: #C00000;")
        btn_reset.clicked.connect(self.on_reset_db)

        h_db.addWidget(btn_backup)
        h_db.addWidget(btn_restore)
        h_db.addWidget(btn_sample)
        h_db.addWidget(btn_reset)

        main_layout.addWidget(db_group)
        main_layout.addStretch()

    def load_settings(self):
        self.txt_inst_name.setText(self.db.get_setting("institution_name", "Government Engineering College"))
        self.txt_inst_addr.setText(self.db.get_setting("institution_address", "College Campus, University Road"))
        self.txt_acad_year.setText(self.db.get_setting("academic_year", "2026-2027"))
        self.txt_acad_term.setText(self.db.get_setting("academic_term", "Even Semester (II, IV, VI, VIII)"))
        self.chk_require_login.setChecked(self.db.get_setting("require_login", "0") == "1")

    def save_institution_settings(self):
        name = self.txt_inst_name.text().strip()
        addr = self.txt_inst_addr.text().strip()
        year = self.txt_acad_year.text().strip()
        term = self.txt_acad_term.text().strip()

        if not name or not addr:
            QMessageBox.warning(self, "Validation Error", "Institution Name and Address are required.")
            return

        self.db.set_setting("institution_name", name)
        self.db.set_setting("institution_address", addr)
        self.db.set_setting("academic_year", year)
        self.db.set_setting("academic_term", term)

        QMessageBox.information(self, "Saved", "Institution details updated successfully.")

    def save_security_settings(self):
        req = "1" if self.chk_require_login.isChecked() else "0"
        self.db.set_setting("require_login", req)

        pwd = self.txt_admin_pwd.text().strip()
        if pwd:
            pwd_hash = hashlib.sha256(pwd.encode()).hexdigest()
            self.db.set_setting("admin_password_hash", pwd_hash)
            self.txt_admin_pwd.clear()
            QMessageBox.information(self, "Saved", "Administrator password and security settings updated.")
        else:
            QMessageBox.information(self, "Saved", "Security policy updated.")

    def on_backup_db(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Database Backup",
            "classplanner_backup.db",
            "SQLite Database Files (*.db)"
        )
        if not file_path:
            return

        try:
            saved_path = create_backup(file_path)
            QMessageBox.information(self, "Backup Complete", f"Database successfully backed up to:\n{saved_path}")
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", f"Could not create database backup: {e}")

    def on_restore_db(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database Backup to Restore",
            "",
            "SQLite Database Files (*.db)"
        )
        if not file_path:
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Database Restore",
            "Restoring a database will overwrite all existing current records.\n"
            "Are you sure you want to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                restore_backup(file_path)
                QMessageBox.information(self, "Restore Complete", "Database restored successfully. Reloading settings.")
                self.load_settings()
            except Exception as e:
                QMessageBox.critical(self, "Restore Failed", f"Could not restore database: {e}")

    def on_load_sample(self):
        reply = QMessageBox.question(
            self,
            "Load Sample Data",
            "Load complete college sample dataset (CSE, ECE, MECH departments with subjects and faculty)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            success, msg = load_sample_college_data(self.db, force=True)
            if success:
                QMessageBox.information(self, "Success", msg)
            else:
                QMessageBox.warning(self, "Notice", msg)

    def on_reset_db(self):
        reply = QMessageBox.critical(
            self,
            "DANGER: Reset Database",
            "This action will permanently delete all departments, faculty, subjects, classrooms, "
            "and generated timetables!\n\nAre you absolutely sure you want to wipe the database?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # Second confirmation to prevent accidental loss
            confirm2 = QMessageBox.question(
                self,
                "Final Confirmation",
                "Please confirm a second time: Wipe all institutional data?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm2 == QMessageBox.Yes:
                reset_database()
                QMessageBox.information(self, "Reset Complete", "Database has been reset to fresh initial state.")
                self.load_settings()

    def on_test_supabase(self):
        from classplanner.database.supabase_sync import SupabaseManager
        host = self.txt_cloud_host.text().strip()
        try:
            port = int(self.txt_cloud_port.text().strip() or 5432)
        except ValueError:
            port = 5432
        dbname = self.txt_cloud_db.text().strip()
        user = self.txt_cloud_user.text().strip()
        pwd = self.txt_cloud_pwd.text().strip()

        sm = SupabaseManager(host=host, port=port, dbname=dbname, user=user, password=pwd)
        self.txt_cloud_uri.setText(sm.get_connection_string())

        ok, msg = sm.test_connection()
        if ok:
            QMessageBox.information(self, "Supabase Connection Success", f"Connected to Supabase PostgreSQL successfully!\n\n{msg}")
        else:
            QMessageBox.critical(self, "Supabase Connection Failed", f"Could not connect to Supabase PostgreSQL:\n\n{msg}")

    def on_push_supabase(self):
        from classplanner.database.supabase_sync import SupabaseManager
        reply = QMessageBox.question(
            self,
            "Confirm Supabase Sync",
            "This will upload and synchronize all local college data (departments, faculty, subjects, classrooms, "
            "sections, time slots, and timetables) to your remote Supabase PostgreSQL instance.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return

        host = self.txt_cloud_host.text().strip()
        try:
            port = int(self.txt_cloud_port.text().strip() or 5432)
        except ValueError:
            port = 5432
        dbname = self.txt_cloud_db.text().strip()
        user = self.txt_cloud_user.text().strip()
        pwd = self.txt_cloud_pwd.text().strip()

        sm = SupabaseManager(host=host, port=port, dbname=dbname, user=user, password=pwd)
        ok, msg = sm.push_local_data_to_supabase(self.db)
        if ok:
            QMessageBox.information(self, "Cloud Sync Succeeded", msg)
        else:
            QMessageBox.critical(self, "Cloud Sync Failed", msg)

