#!/usr/bin/env python3
"""
ClassPlanner - Automated College Timetable Generator & Multi-College Management System
Main Application Entry Point.
"""

import sys
import os

# Ensure package is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon

from classplanner.config import APP_NAME, APP_ORGANIZATION
from classplanner.database.db_manager import DatabaseManager
from classplanner.ui.styles import CLASSIC_DESKTOP_QSS, RESOURCES_DIR
from classplanner.ui.main_window import MainWindow
from classplanner.ui.dialogs.login_dialog import LoginDialog


def main():
    # Set high DPI attributes
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setStyleSheet(CLASSIC_DESKTOP_QSS)

    # Set application icon
    icon_path = os.path.join(RESOURCES_DIR, "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # Set default standard font
    default_font = QFont("Segoe UI", 9)
    app.setFont(default_font)

    # Initialize Database (multi-tenant schema)
    db = DatabaseManager()

    # Application session loop (allows clean re-login after logout)
    while True:
        login_dlg = LoginDialog(db)
        if not login_dlg.exec() or not login_dlg.session:
            break

        window = MainWindow(db, session=login_dlg.session)
        logged_out = False

        def handle_logout():
            nonlocal logged_out
            logged_out = True

        window.logout_requested.connect(handle_logout)
        window.show()

        app.exec()

        if not logged_out:
            break

    sys.exit(0)


if __name__ == "__main__":
    main()
