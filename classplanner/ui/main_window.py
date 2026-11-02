"""
ClassPlanner - Main Application Window
Traditional desktop software interface with classic Menu Bar, Left Navigation Tree,
Central Stacked Workspace, and Multi-College Tenancy & Role-Based Access Control.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QMenuBar, QMenu, QStatusBar, QMessageBox, QSplitter,
    QLabel, QFrame, QFileDialog, QPushButton, QComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QFont, QIcon, QColor

from classplanner.config import APP_NAME, APP_VERSION
from classplanner.auth import Session, UserRole, AuthService
from classplanner.database.db_manager import DatabaseManager
from classplanner.database.backup import create_backup, restore_backup
from classplanner.database.sample_data import load_sample_college_data

from classplanner.ui.styles import CLASSIC_DESKTOP_QSS
from classplanner.ui.widgets import (
    DashboardWidget, DepartmentWidget, FacultyWidget,
    SubjectWidget, ClassroomWidget, SectionWidget,
    WorkingHoursWidget, GeneratorWidget, TimetableGridWidget,
    ReportsWidget, SettingsWidget, SuperAdminWidget, CourseSemesterWidget
)
from classplanner.ui.dialogs import AboutDialog


class MainWindow(QMainWindow):
    """Main Application Window for ClassPlanner with Multi-Tenant Governance."""
    logout_requested = Signal()

    def __init__(self, db: DatabaseManager, session: Optional[Session] = None):
        super().__init__()
        self.db = db
        self.session = session or AuthService.get_current_session() or Session(
            user_id=1, email="admin@gec.edu", full_name="College Administrator",
            role=UserRole.COLLEGE_ADMIN, college_id=1, college_name="Government Engineering College",
            college_code="GEC-01", is_authenticated=True
        )

        # Set tenant scope on DatabaseManager
        if self.session.is_super_admin():
            if self.db.current_college_id is None:
                self.db.set_active_college(1)
        else:
            self.db.set_active_college(self.session.college_id)

        self.setWindowTitle(f"{APP_NAME} Enterprise v{APP_VERSION} — Multi-College Timetable Platform")
        self.setMinimumSize(1180, 750)
        self.setStyleSheet(CLASSIC_DESKTOP_QSS)

        self.init_ui()
        self.create_menu_bar()
        self.create_status_bar()

    def init_ui(self):
        # Central Splitter: Left Nav Tree + Right Content Stack
        main_splitter = QSplitter(Qt.Horizontal)

        # ---------------- Left Navigation Panel ----------------
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(6)

        # Brand & Active Tenant Banner
        banner_frame = QFrame()
        banner_frame.setObjectName("banner_frame")
        b_lay = QVBoxLayout(banner_frame)
        b_lay.setContentsMargins(8, 8, 8, 8)
        b_lay.setSpacing(3)

        lbl_brand = QLabel(f"<b>{APP_NAME} Enterprise</b>")
        lbl_brand.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl_brand.setStyleSheet("color: #1A2B4C;")

        self.lbl_tenant_info = QLabel()
        self._update_tenant_banner_text()
        self.lbl_tenant_info.setStyleSheet("font-size: 8pt; color: #444444;")

        b_lay.addWidget(lbl_brand)
        b_lay.addWidget(self.lbl_tenant_info)

        # Super Admin College Switcher in navigation header if Super Admin
        if self.session.is_super_admin():
            h_switch = QHBoxLayout()
            h_switch.setContentsMargins(0, 4, 0, 0)
            lbl_sw = QLabel("College:")
            lbl_sw.setStyleSheet("font-size: 8.5pt; font-weight: bold; color: #004D99;")
            self.cmb_col_switch = QComboBox()
            self.cmb_col_switch.setMinimumWidth(140)
            self.cmb_col_switch.setFixedHeight(26)
            self.cmb_col_switch.setStyleSheet("font-size: 8.5pt; padding: 2px 22px 2px 6px;")
            self._populate_college_switcher()
            self.cmb_col_switch.currentIndexChanged.connect(self.on_switch_college_dropdown)
            h_switch.addWidget(lbl_sw)
            h_switch.addWidget(self.cmb_col_switch, 1)
            b_lay.addLayout(h_switch)

        nav_layout.addWidget(banner_frame)

        # Tree Widget for Navigation
        self.nav_tree = QTreeWidget()
        self.nav_tree.setObjectName("nav_tree")
        self.nav_tree.setHeaderHidden(True)
        self.nav_tree.setColumnCount(1)
        self.nav_tree.setMinimumWidth(215)
        self.nav_tree.setMaximumWidth(270)

        # Build Navigation Items based on Role
        self._build_nav_tree()
        self.nav_tree.itemClicked.connect(self.on_nav_item_clicked)
        nav_layout.addWidget(self.nav_tree)

        # Logout & Session button at bottom of nav tree
        nav_foot = QFrame()
        nav_foot.setStyleSheet("background: #EAEAEA; border: 1px solid #C0C0C0; padding: 4px; border-radius: 3px;")
        f_lay = QVBoxLayout(nav_foot)
        f_lay.setContentsMargins(4, 4, 4, 4)
        f_lay.setSpacing(4)

        lbl_user = QLabel(f"👤 {self.session.full_name}\n<{self.session.get_role_badge()}>")
        lbl_user.setStyleSheet("font-size: 7.8pt; color: #333333;")
        btn_logout = QPushButton("🚪 Logout")
        btn_logout.setStyleSheet("background-color: #FFFFFF; font-size: 8.5pt; border: 1px solid #A0A0A0; padding: 3px;")
        btn_logout.clicked.connect(self.on_logout)

        f_lay.addWidget(lbl_user)
        f_lay.addWidget(btn_logout)
        nav_layout.addWidget(nav_foot)

        main_splitter.addWidget(nav_container)

        # ---------------- Right Workspace Stack ----------------
        self.stack = QStackedWidget()
        self.stack.setObjectName("central_stack")

        # Instantiate Sub-Widgets
        if self.session.is_super_admin():
            self.widget_super_admin = SuperAdminWidget(self.db, self)
            self.widget_super_admin.college_switched.connect(self.switch_to_college)
        else:
            self.widget_super_admin = None

        self.widget_dashboard = DashboardWidget(self.db, self)
        self.widget_dashboard.navigate_requested.connect(self.navigate_to_key)

        self.widget_departments = DepartmentWidget(self.db, self)
        self.widget_courses_semesters = CourseSemesterWidget(self.db, self)
        self.widget_faculty = FacultyWidget(self.db, self)
        self.widget_subjects = SubjectWidget(self.db, self)
        self.widget_classrooms = ClassroomWidget(self.db, self)
        self.widget_sections = SectionWidget(self.db, self)
        self.widget_working_hours = WorkingHoursWidget(self.db, self)

        self.widget_generator = GeneratorWidget(self.db, self)
        self.widget_generator.view_timetable_requested.connect(lambda: self.navigate_to_key("timetable_view"))

        self.widget_timetable_view = TimetableGridWidget(self.db, self)
        self.widget_reports = ReportsWidget(self.db, self)
        self.widget_settings = SettingsWidget(self.db, self)

        # Add to stack in index order
        idx_tt_view = self.stack.addWidget(self.widget_timetable_view)
        self.nav_mapping = {
            "dashboard": self.stack.addWidget(self.widget_dashboard),
            "departments": self.stack.addWidget(self.widget_departments),
            "courses_semesters": self.stack.addWidget(self.widget_courses_semesters),
            "faculty": self.stack.addWidget(self.widget_faculty),
            "subjects": self.stack.addWidget(self.widget_subjects),
            "classrooms": self.stack.addWidget(self.widget_classrooms),
            "sections": self.stack.addWidget(self.widget_sections),
            "working_hours": self.stack.addWidget(self.widget_working_hours),
            "generator": self.stack.addWidget(self.widget_generator),
            "timetable_view": idx_tt_view,
            "timetable_edit": idx_tt_view,
            "reports": self.stack.addWidget(self.widget_reports),
            "settings": self.stack.addWidget(self.widget_settings),
        }

        if self.widget_super_admin:
            idx_sa = self.stack.addWidget(self.widget_super_admin)
            self.nav_mapping["super_admin"] = idx_sa
            # Default Super Admin landing view
            self.stack.setCurrentIndex(idx_sa)
        else:
            self.stack.setCurrentIndex(self.nav_mapping["dashboard"])

        main_splitter.addWidget(self.stack)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(main_splitter)

    def _update_tenant_banner_text(self):
        """Updates top navigation banner to reflect active tenant college."""
        if self.session.is_super_admin():
            active_col = self.db.get_active_college()
            col_label = f"[{active_col['college_code']}] {active_col['college_name']}" if active_col else "All Colleges"
            self.lbl_tenant_info.setText(f"🛡️ <b>Super Admin Console</b><br>Active: <i>{col_label}</i>")
        else:
            col_name = self.session.college_name or "College Portal"
            col_code = self.session.college_code or ""
            code_str = f" [{col_code}]" if col_code else ""
            self.lbl_tenant_info.setText(f"🏫 <b>{col_name}{code_str}</b><br>College Admin Portal")

    def _populate_college_switcher(self):
        """Populates the Super Admin college context switcher dropdown."""
        self.cmb_col_switch.blockSignals(True)
        self.cmb_col_switch.clear()
        colleges = self.db.get_colleges()
        cur_id = self.db.current_college_id or 1
        cur_idx = 0

        for i, c in enumerate(colleges):
            self.cmb_col_switch.addItem(f"{c['college_code']} — {c['college_name']}", c["id"])
            if c["id"] == cur_id:
                cur_idx = i

        self.cmb_col_switch.setCurrentIndex(cur_idx)
        self.cmb_col_switch.blockSignals(False)

    def _build_nav_tree(self):
        """Constructs role-aware hierarchical navigation tree."""
        self.nav_tree.clear()

        # ---------------- SUPER ADMIN SECTION ----------------
        if self.session.is_super_admin():
            group_sa = QTreeWidgetItem(self.nav_tree, ["🛡️ Super Admin"])
            group_sa.setExpanded(True)

            i_sa_dash = QTreeWidgetItem(group_sa, ["Colleges & Governance"])
            i_sa_dash.setData(0, Qt.UserRole, "super_admin")
            self.nav_tree.setCurrentItem(i_sa_dash)

        # ---------------- COLLEGE OPERATIONS SECTION ----------------
        header_text = "🏫 Managed College Operations" if self.session.is_super_admin() else "🏫 College Management"
        group_college = QTreeWidgetItem(self.nav_tree, [header_text])
        group_college.setExpanded(True)

        item_dash = QTreeWidgetItem(group_college, ["📊 Dashboard Overview"])
        item_dash.setData(0, Qt.UserRole, "dashboard")

        if not self.session.is_super_admin():
            self.nav_tree.setCurrentItem(item_dash)

        # Master Data
        group_master = QTreeWidgetItem(group_college, ["🏢 Master Data"])
        group_master.setExpanded(True)

        i_depts = QTreeWidgetItem(group_master, ["Academic Departments"])
        i_depts.setData(0, Qt.UserRole, "departments")

        i_prog = QTreeWidgetItem(group_master, ["Courses & Semesters"])
        i_prog.setData(0, Qt.UserRole, "courses_semesters")

        i_fac = QTreeWidgetItem(group_master, ["Faculty Members"])
        i_fac.setData(0, Qt.UserRole, "faculty")

        i_sub = QTreeWidgetItem(group_master, ["Subject Curriculum"])
        i_sub.setData(0, Qt.UserRole, "subjects")

        i_rooms = QTreeWidgetItem(group_master, ["Classrooms & Labs"])
        i_rooms.setData(0, Qt.UserRole, "classrooms")

        i_sec = QTreeWidgetItem(group_master, ["Student Sections"])
        i_sec.setData(0, Qt.UserRole, "sections")

        i_hours = QTreeWidgetItem(group_master, ["Working Hours & Slots"])
        i_hours.setData(0, Qt.UserRole, "working_hours")

        # Timetable Operations
        group_tt = QTreeWidgetItem(group_college, ["📅 Timetable Operations"])
        group_tt.setExpanded(True)

        i_gen = QTreeWidgetItem(group_tt, ["Generate Timetable"])
        i_gen.setData(0, Qt.UserRole, "generator")

        i_view = QTreeWidgetItem(group_tt, ["View Timetables (Grid)"])
        i_view.setData(0, Qt.UserRole, "timetable_view")

        i_edit = QTreeWidgetItem(group_tt, ["Manual Timetable Editor"])
        i_edit.setData(0, Qt.UserRole, "timetable_edit")

        # Reports & Exports
        item_reports = QTreeWidgetItem(group_college, ["📈 Reports & Exports"])
        item_reports.setData(0, Qt.UserRole, "reports")

        # Settings & Cloud Sync
        settings_label = "⚙️ Platform Settings & Cloud" if self.session.is_super_admin() else "⚙️ College Profile & Cloud"
        item_settings = QTreeWidgetItem(self.nav_tree, [settings_label])
        item_settings.setData(0, Qt.UserRole, "settings")

    def on_nav_item_clicked(self, item: QTreeWidgetItem, column: int):
        key = item.data(0, Qt.UserRole)
        if key and key in self.nav_mapping:
            idx = self.nav_mapping[key]
            self.stack.setCurrentIndex(idx)
            self._refresh_widget(key)

    def navigate_to_key(self, key: str):
        """Programmatically switch view from buttons or menu."""
        if key in self.nav_mapping:
            idx = self.nav_mapping[key]
            self.stack.setCurrentIndex(idx)
            self._select_nav_tree_item(key)
            self._refresh_widget(key)

    def _select_nav_tree_item(self, key: str):
        def search_item(parent_item):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if child.data(0, Qt.UserRole) == key:
                    self.nav_tree.setCurrentItem(child)
                    return True
                if search_item(child):
                    return True
            return False

        for i in range(self.nav_tree.topLevelItemCount()):
            top = self.nav_tree.topLevelItem(i)
            if top.data(0, Qt.UserRole) == key:
                self.nav_tree.setCurrentItem(top)
                return
            if search_item(top):
                return

    def _refresh_widget(self, key: str):
        """Triggers data reloads when switching to a view."""
        if key == "super_admin" and self.widget_super_admin:
            self.widget_super_admin.refresh_data()
        elif key == "dashboard":
            self.widget_dashboard.refresh_stats()
        elif key == "departments":
            self.widget_departments.load_departments()
        elif key == "courses_semesters":
            self.widget_courses_semesters.refresh_all()
        elif key == "faculty":
            self.widget_faculty.load_faculty()
        elif key == "subjects":
            self.widget_subjects.load_subjects()
        elif key == "classrooms":
            self.widget_classrooms.load_classrooms()
        elif key == "sections":
            self.widget_sections.load_sections()
        elif key == "working_hours":
            self.widget_working_hours.load_current_settings()
        elif key in ("timetable_view", "timetable_edit"):
            self.widget_timetable_view.load_timetables_dropdown()
        elif key == "reports":
            self.widget_reports.load_reports()
        elif key == "settings":
            self.widget_settings.load_settings()

    def on_switch_college_dropdown(self, index: int):
        cid = self.cmb_col_switch.currentData()
        if cid:
            self.switch_to_college(cid)

    def switch_to_college(self, college_id: int):
        """Switches active college context for Super Admin."""
        self.db.set_active_college(college_id)
        self._update_tenant_banner_text()
        if hasattr(self, "cmb_col_switch"):
            for i in range(self.cmb_col_switch.count()):
                if self.cmb_col_switch.itemData(i) == college_id:
                    self.cmb_col_switch.blockSignals(True)
                    self.cmb_col_switch.setCurrentIndex(i)
                    self.cmb_col_switch.blockSignals(False)
                    break

        col = self.db.get_college(college_id)
        col_name = col["college_name"] if col else "Selected College"
        self.lbl_status_inst.setText(f"🏫 Active College: {col_name}")

        # Navigate to Dashboard and refresh stats
        self.navigate_to_key("dashboard")

    def on_logout(self):
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to log out of ClassPlanner?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            AuthService.logout()
            self.logout_requested.emit()
            self.close()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # 1. FILE MENU
        menu_file = menubar.addMenu("&File")

        act_load_sample = QAction("Load Sample College Dataset", self)
        act_load_sample.triggered.connect(self.on_menu_load_sample)
        menu_file.addAction(act_load_sample)

        menu_file.addSeparator()

        act_backup = QAction("Backup Database...", self)
        act_backup.triggered.connect(self.on_menu_backup)
        menu_file.addAction(act_backup)

        act_restore = QAction("Restore Database...", self)
        act_restore.triggered.connect(self.on_menu_restore)
        menu_file.addAction(act_restore)

        menu_file.addSeparator()

        act_logout = QAction("Log &Out", self)
        act_logout.triggered.connect(self.on_logout)
        menu_file.addAction(act_logout)

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut("Alt+F4")
        act_exit.triggered.connect(self.close)
        menu_file.addAction(act_exit)

        # 2. MASTER DATA MENU
        menu_master = menubar.addMenu("&Master Data")

        act_m_depts = QAction("&Departments", self)
        act_m_depts.triggered.connect(lambda: self.navigate_to_key("departments"))
        menu_master.addAction(act_m_depts)

        act_m_prog = QAction("&Courses & Semesters", self)
        act_m_prog.triggered.connect(lambda: self.navigate_to_key("courses_semesters"))
        menu_master.addAction(act_m_prog)

        act_m_fac = QAction("&Faculty Members", self)
        act_m_fac.triggered.connect(lambda: self.navigate_to_key("faculty"))
        menu_master.addAction(act_m_fac)

        act_m_sub = QAction("&Subjects Curriculum", self)
        act_m_sub.triggered.connect(lambda: self.navigate_to_key("subjects"))
        menu_master.addAction(act_m_sub)

        act_m_room = QAction("&Classrooms & Labs", self)
        act_m_room.triggered.connect(lambda: self.navigate_to_key("classrooms"))
        menu_master.addAction(act_m_room)

        act_m_sec = QAction("Student &Sections", self)
        act_m_sec.triggered.connect(lambda: self.navigate_to_key("sections"))
        menu_master.addAction(act_m_sec)

        menu_master.addSeparator()

        act_m_hours = QAction("&Working Hours & Time Slots", self)
        act_m_hours.triggered.connect(lambda: self.navigate_to_key("working_hours"))
        menu_master.addAction(act_m_hours)

        # 3. TIMETABLE MENU
        menu_tt = menubar.addMenu("&Timetable")

        act_t_gen = QAction("&Generate Timetable...", self)
        act_t_gen.triggered.connect(lambda: self.navigate_to_key("generator"))
        menu_tt.addAction(act_t_gen)

        act_t_view = QAction("&View Timetable Grid", self)
        act_t_view.triggered.connect(lambda: self.navigate_to_key("timetable_view"))
        menu_tt.addAction(act_t_view)

        act_t_edit = QAction("&Manual Timetable Editor", self)
        act_t_edit.triggered.connect(lambda: self.navigate_to_key("timetable_edit"))
        menu_tt.addAction(act_t_edit)

        # 4. REPORTS MENU
        menu_rep = menubar.addMenu("&Reports")

        act_r_workload = QAction("Faculty &Workload Report", self)
        act_r_workload.triggered.connect(lambda: self.navigate_to_key("reports"))
        menu_rep.addAction(act_r_workload)

        act_r_util = QAction("Classroom &Utilization Report", self)
        act_r_util.triggered.connect(lambda: self.navigate_to_key("reports"))
        menu_rep.addAction(act_r_util)

        # 5. SETTINGS MENU
        menu_set = menubar.addMenu("&Settings")

        act_s_inst = QAction("&Institution & Term Configuration", self)
        act_s_inst.triggered.connect(lambda: self.navigate_to_key("settings"))
        menu_set.addAction(act_s_inst)

        # 6. HELP MENU
        menu_help = menubar.addMenu("&Help")

        act_guide = QAction("Quick User &Guide", self)
        act_guide.triggered.connect(self.on_show_guide)
        menu_help.addAction(act_guide)

        menu_help.addSeparator()

        act_about = QAction(f"&About {APP_NAME}...", self)
        act_about.triggered.connect(self.on_show_about)
        menu_help.addAction(act_about)

    def create_status_bar(self):
        status = self.statusBar()
        col = self.db.get_active_college()
        col_name = col["college_name"] if col else "Multi-College System"
        acad_year = self.db.get_setting("academic_year", "2026-2027")

        self.lbl_status_inst = QLabel(f"🏫 {col_name} ({acad_year})")
        self.lbl_status_role = QLabel(f"👤 {self.session.get_role_badge()}")
        self.lbl_status_role.setStyleSheet("color: #004D99; font-weight: bold; padding: 0 10px;")

        self.lbl_status_offline = QLabel("🔒 Offline SQLite & Supabase Sync Ready")
        self.lbl_status_offline.setStyleSheet("color: #006600; font-weight: bold; padding-right: 15px;")

        status.addWidget(self.lbl_status_inst, 1)
        status.addPermanentWidget(self.lbl_status_role)
        status.addPermanentWidget(self.lbl_status_offline)

    def on_menu_load_sample(self):
        reply = QMessageBox.question(
            self,
            "Load Sample College Dataset",
            "Are you sure you want to load sample college data?\n"
            "This will populate CSE, ECE, and MECH departments with subjects, faculty, and classrooms.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            success, msg = load_sample_college_data(self.db, force=True)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.widget_dashboard.refresh_stats()
            else:
                QMessageBox.warning(self, "Notice", msg)

    def on_menu_backup(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Backup Database", "classplanner_backup.db", "SQLite Database (*.db)"
        )
        if file_path:
            try:
                create_backup(file_path)
                QMessageBox.information(self, "Success", f"Database backed up to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create backup: {e}")

    def on_menu_restore(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Restore Database", "", "SQLite Database (*.db)"
        )
        if file_path:
            reply = QMessageBox.warning(
                self, "Confirm Restore", "Restoring will replace the current database. Proceed?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    restore_backup(file_path)
                    QMessageBox.information(self, "Success", "Database restored successfully.")
                    self.widget_dashboard.refresh_stats()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Could not restore database: {e}")

    def on_show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def on_show_guide(self):
        QMessageBox.information(
            self,
            "ClassPlanner - Quick Guide",
            "1. Master Data: Configure Departments, Courses, Faculty, Subjects, and Classrooms.\n"
            "2. Working Hours: Set working days and daily period start/end times.\n"
            "3. Generate Timetable: Click 'Generate Timetable' to run the constraint scheduler.\n"
            "4. Views & Editing: Review the grid in Section/Faculty/Room view. Double-click any cell to manually edit.\n"
            "5. Reports: Export final timetables and workload statistics to PDF or Excel.\n"
            "6. Multi-College: Super Admin can register new colleges, manage access, and switch contexts."
        )
