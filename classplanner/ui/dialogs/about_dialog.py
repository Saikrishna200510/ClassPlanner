"""
ClassPlanner - About Dialog
Classic system information dialog.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
import os
from classplanner.config import APP_NAME, APP_VERSION, APP_ORGANIZATION
from classplanner.ui.styles import RESOURCES_DIR


class AboutDialog(QDialog):
    """About dialog with system version, developer attribution, and system features."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(480, 370)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0; padding: 12px;")
        f_lay = QVBoxLayout(info_frame)
        f_lay.setSpacing(8)

        # Header with Logo and Title
        h_head = QHBoxLayout()
        logo_path = os.path.join(RESOURCES_DIR, "icon.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(RESOURCES_DIR, "slit_logo.png")

        if os.path.exists(logo_path):
            lbl_logo = QLabel()
            pix = QPixmap(logo_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            h_head.addWidget(lbl_logo)
            h_head.addSpacing(10)

        v_titles = QVBoxLayout()
        lbl_title = QLabel(f"<b>{APP_NAME}</b>")
        lbl_title.setStyleSheet("font-size: 15pt; color: #1A2B4C;")
        lbl_desc = QLabel("Multi-College Automated Timetable Management System")
        lbl_desc.setStyleSheet("font-size: 9pt; font-weight: bold; color: #333333;")
        lbl_ver = QLabel(f"Version: <b>v{APP_VERSION}</b> | Developer: <b>{APP_ORGANIZATION}</b>")
        lbl_ver.setStyleSheet("font-size: 8.5pt; color: #004D99;")
        v_titles.addWidget(lbl_title)
        v_titles.addWidget(lbl_desc)
        v_titles.addWidget(lbl_ver)
        h_head.addLayout(v_titles)
        h_head.addStretch()
        f_lay.addLayout(h_head)

        lbl_body = QLabel(
            "ClassPlanner is a standalone desktop application engineered to simplify "
            "college timetable management and automate conflict-free weekly schedules.<br/><br/>"
            "<b>Key Capabilities:</b><br/>"
            "• Multi-College Management with Super Admin and College Portals<br/>"
            "• Constraint-Based Automated Scheduling (OR-Tools / Heuristic Backtracking)<br/>"
            "• Zero Double-Booking Collision Guarantees (Faculty, Rooms, Sections)<br/>"
            "• Consecutive Laboratory Blocks & Daily Break Protection<br/>"
            "• Multi-Perspective Timetables (Section, Faculty, Room, Department)<br/>"
            "• ReportLab PDF & OpenPyXL Excel Institutional Exports<br/>"
            "• Offline SQLite with Cloud Sync to Supabase PostgreSQL (Row Level Security)"
        )
        lbl_body.setWordWrap(True)
        lbl_body.setStyleSheet("font-size: 8.5pt; color: #444444; line-height: 1.3;")
        f_lay.addWidget(lbl_body)
        layout.addWidget(info_frame)

        btn_bar = QHBoxLayout()
        lbl_status = QLabel("Project Status: Under Development")
        lbl_status.setStyleSheet("color: #777777; font-size: 8pt; font-style: italic;")
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(self.accept)
        btn_bar.addWidget(lbl_status)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_ok)
        layout.addLayout(btn_bar)

