"""
ClassPlanner - About Dialog
Classic system information dialog.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt
from classplanner.config import APP_NAME, APP_VERSION


class AboutDialog(QDialog):
    """About dialog with system version, institutional license, and offline guarantee."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(460, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0; padding: 12px;")
        f_lay = QVBoxLayout(info_frame)
        f_lay.setSpacing(6)

        lbl_title = QLabel(f"<b>{APP_NAME}</b>")
        lbl_title.setStyleSheet("font-size: 14pt; color: #1A2B4C;")

        lbl_desc = QLabel("Automated College Timetable Generator & Management Desktop Software")
        lbl_desc.setStyleSheet("font-size: 9.5pt; font-weight: bold; color: #333333;")

        lbl_body = QLabel(
            f"Version {APP_VERSION}<br/><br/>"
            "This software is an offline college administration tool designed exclusively for "
            "higher education institutions, engineering colleges, and universities.<br/><br/>"
            "<b>Key Features:</b><br/>"
            "• Constraint-Based & Genetic Algorithm Automatic Scheduling<br/>"
            "• Zero Double-Booking Guarantee (Faculty, Rooms, Sections)<br/>"
            "• Consecutive Laboratory Period Blocks & Break Preservation<br/>"
            "• Native SQLite Database with Instant Backup & Restore<br/>"
            "• ReportLab PDF & OpenPyXL Excel Exports<br/>"
            "• 100% Offline Standalone Operation"
        )
        lbl_body.setWordWrap(True)
        lbl_body.setStyleSheet("font-size: 8.5pt; color: #444444;")

        f_lay.addWidget(lbl_title)
        f_lay.addWidget(lbl_desc)
        f_lay.addWidget(lbl_body)
        layout.addWidget(info_frame)

        btn_bar = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.setFixedWidth(80)
        btn_ok.clicked.connect(self.accept)
        btn_bar.addStretch()
        btn_bar.addWidget(btn_ok)
        layout.addLayout(btn_bar)

