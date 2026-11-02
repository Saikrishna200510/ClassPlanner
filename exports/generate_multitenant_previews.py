"""
Generates visual preview snapshots of the Multi-Tenant ClassPlanner Desktop UI.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from classplanner.database import DatabaseManager, load_sample_college_data
from classplanner.auth import AuthService, UserRole
from classplanner.ui.styles import CLASSIC_DESKTOP_QSS
from classplanner.ui.dialogs.login_dialog import LoginDialog
from classplanner.ui.main_window import MainWindow

os.environ["QT_QPA_PLATFORM"] = "offscreen"

app = QApplication(sys.argv)
app.setStyleSheet(CLASSIC_DESKTOP_QSS)
db = DatabaseManager()
load_sample_college_data(db, force=True)
auth = AuthService(db)

# 1. Capture Login Dialog (College Login Tab)
login_dlg = LoginDialog(db)
login_dlg.show()
app.processEvents()
login_dlg.grab().save("exports/preview_login_college.png")

# Switch to Super Admin Tab
login_dlg.tabs.setCurrentIndex(1)
app.processEvents()
login_dlg.grab().save("exports/preview_login_superadmin.png")
login_dlg.close()

# 2. Capture Super Admin Console
ok, msg, sa_sess = auth.login("superadmin@classplanner.edu", "Admin@12345")
win_sa = MainWindow(db, session=sa_sess)
win_sa.resize(1180, 750)
win_sa.show()
app.processEvents()
win_sa.grab().save("exports/preview_super_admin_console.png")
win_sa.close()

# 3. Capture College Admin Console (GEC-01)
ok, msg, col_sess = auth.login("admin@gec.edu", "College@12345")
win_col = MainWindow(db, session=col_sess)
win_col.resize(1180, 750)
win_col.show()
app.processEvents()
win_col.grab().save("exports/preview_college_admin_console.png")

# Also capture Courses & Semesters view
win_col.navigate_to_key("courses_semesters")
app.processEvents()
win_col.grab().save("exports/preview_courses_semesters.png")

# Also capture Timetable Grid View (where user reported input size issue)
win_col.navigate_to_key("timetable_view")
app.processEvents()
win_col.grab().save("exports/preview_timetable_view.png")

# Also capture Timetable View Controls specifically
tt_widget = win_col.widget_timetable_view
tt_widget.top_group.grab().save("exports/preview_timetable_controls.png")

win_col.close()

print("Snapshots generated successfully in exports/")

