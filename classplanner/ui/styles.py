"""
ClassPlanner - Traditional Desktop Software Stylesheet & Palette
Emulates classic Windows / Qt desktop software appearance.
"""

import os
import sys
import base64

if getattr(sys, "frozen", False):
    RESOURCES_DIR = os.path.join(getattr(sys, "_MEIPASS", ""), "classplanner", "resources")
else:
    RESOURCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources"))

ARROW_ICON_PATH = os.path.join(RESOURCES_DIR, "down_arrow.png").replace("\\", "/")

# Ensure down_arrow.png exists on disk
if not os.path.exists(ARROW_ICON_PATH):
    try:
        os.makedirs(RESOURCES_DIR, exist_ok=True)
        with open(ARROW_ICON_PATH, "wb") as f:
            f.write(base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAACXBIWXMAAAsTAAALEwEAmpwY"
                "AAAASklEQVQokWNgGPqAEcYwMTFp+P//fz1WRYyMjWfOnGlgYGBgYIYJPnv27IC0tDQjAwOD"
                "Ay7FKBqwaUJXjBOYmJg0mJiYEFY4RAEAgCkZGDwuAqcAAAAASUVORK5CYII="
            ))
    except Exception:
        pass


_RAW_QSS = """
/* Base Window and Dialogs */
QWidget {
    background-color: #F0F0F0;
    color: #000000;
    font-family: -apple-system, "Segoe UI", "Arial", sans-serif;
    font-size: 9pt;
}

/* Ensure QLabels do not inherit borders from parent containers */
QLabel {
    background: transparent;
    border: none;
    padding: 0px;
}

/* Main Window Content Panels */
QMainWindow {
    background-color: #F0F0F0;
}

QStackedWidget#central_stack {
    background-color: #FFFFFF;
    border: 1px solid #A0A0A0;
}

QFrame#banner_frame {
    background-color: #FFFFFF;
    border: 1px solid #A0A0A0;
}

/* Classic Menu Bar */
QMenuBar {
    background-color: #F0F0F0;
    border-bottom: 1px solid #C0C0C0;
    padding: 2px;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 10px;
    margin: 1px;
}

QMenuBar::item:selected {
    background-color: #CCE4F7;
    border: 1px solid #0078D7;
}

QMenu {
    background-color: #FFFFFF;
    border: 1px solid #999999;
    padding: 2px;
}

QMenu::item {
    padding: 5px 25px 5px 20px;
}

QMenu::item:selected {
    background-color: #E5F1FB;
    color: #000000;
}

QMenu::separator {
    height: 1px;
    background-color: #D0D0D0;
    margin: 3px 5px;
}

/* ToolBar & Status Bar */
QToolBar {
    background-color: #F0F0F0;
    border-bottom: 1px solid #C0C0C0;
    spacing: 4px;
    padding: 3px;
}

QStatusBar {
    background-color: #F0F0F0;
    border-top: 1px solid #C0C0C0;
    color: #333333;
}

/* Left Navigation Tree / List */
QTreeWidget#nav_tree, QListWidget#nav_list {
    background-color: #FFFFFF;
    border: 1px solid #A0A0A0;
    font-size: 9.5pt;
    padding: 2px;
}

QTreeWidget#nav_tree::item {
    padding: 6px 4px;
    border-bottom: 1px solid #F5F5F5;
}

QTreeWidget#nav_tree::item:selected {
    background-color: #CCE4F7;
    color: #000000;
    border: 1px solid #99D1FF;
}

QTreeWidget#nav_tree::item:hover {
    background-color: #E5F1FB;
}

/* Standard Rectangular Buttons */
QPushButton {
    background-color: #E1E1E1;
    border: 1px solid #ADADAD;
    border-radius: 2px;
    padding: 4px 14px;
    min-height: 22px;
    font-size: 9pt;
    text-align: center;
}

QPushButton:hover {
    background-color: #E5F1FB;
    border: 1px solid #0078D7;
}

QPushButton:pressed {
    background-color: #CCE4F7;
    border: 1px solid #005499;
}

QPushButton:disabled {
    background-color: #F4F4F4;
    border: 1px solid #D6D6D6;
    color: #888888;
}

/* Primary Action Button (Generate Timetable / Save) */
QPushButton#btn_primary {
    background-color: #DCE8F5;
    border: 1px solid #0078D7;
    font-weight: bold;
    color: #004080;
}

QPushButton#btn_primary:hover {
    background-color: #CCE4F7;
    border: 1px solid #005499;
}

/* Action buttons inside Table Cells */
QPushButton[tableAction="true"] {
    background-color: #F2F2F2;
    border: 1px solid #ADADAD;
    border-radius: 2px;
    padding: 2px 6px;
    min-height: 22px;
    max-height: 24px;
    font-size: 8.5pt;
    text-align: center;
}

QPushButton[tableAction="true"]:hover {
    background-color: #CCE4F7;
    border: 1px solid #0078D7;
    color: #004080;
}

QPushButton[tableDelete="true"] {
    background-color: #F2F2F2;
    border: 1px solid #ADADAD;
    border-radius: 2px;
    padding: 2px 6px;
    min-height: 22px;
    max-height: 24px;
    font-size: 8.5pt;
    text-align: center;
}

QPushButton[tableDelete="true"]:hover {
    background-color: #FDE7E9;
    border: 1px solid #D83B01;
    color: #A80000;
}

/* Data Tables */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    border: 1px solid #A0A0A0;
    gridline-color: #DCDCDC;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
    alternate-background-color: #F9FBFD;
    outline: none;
}

QTableWidget::item {
    padding-left: 6px;
    padding-right: 6px;
}

QHeaderView::section {
    background-color: #EAEAEA;
    color: #000000;
    padding: 6px 8px;
    border: 1px solid #C0C0C0;
    border-top: none;
    border-left: none;
    font-weight: bold;
    font-size: 8.5pt;
}

/* Input Controls */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #7A7A7A;
    border-radius: 2px;
    padding: 4px 8px;
    min-height: 26px;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
}

QLineEdit:focus {
    border: 1px solid #0078D7;
}

QLineEdit:disabled {
    background-color: #F4F4F4;
    color: #888888;
    border: 1px solid #D6D6D6;
}

QComboBox {
    background-color: #FFFFFF;
    border: 1px solid #7A7A7A;
    border-radius: 2px;
    padding: 4px 26px 4px 8px;
    min-height: 26px;
    min-width: 130px;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
}

QComboBox:hover {
    border: 1px solid #0078D7;
}

QComboBox:focus {
    border: 1px solid #0078D7;
}

QComboBox:disabled {
    background-color: #F4F4F4;
    color: #888888;
    border: 1px solid #D6D6D6;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #ADADAD;
    background-color: #E1E1E1;
    border-top-right-radius: 2px;
    border-bottom-right-radius: 2px;
}

QComboBox::drop-down:hover {
    background-color: #CCE4F7;
}

QComboBox::down-arrow {
    image: url("__ARROW_ICON_PATH__");
    width: 8px;
    height: 8px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #7A7A7A;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
    padding: 2px;
    outline: none;
    min-width: 140px;
}

QComboBox QAbstractItemView::item {
    min-height: 24px;
    padding: 3px 8px;
}

QSpinBox, QTimeEdit, QDateEdit, QDateTimeEdit {
    background-color: #FFFFFF;
    border: 1px solid #7A7A7A;
    border-radius: 2px;
    padding: 4px 6px;
    min-height: 26px;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
}

QSpinBox:focus, QTimeEdit:focus, QDateEdit:focus, QDateTimeEdit:focus {
    border: 1px solid #0078D7;
}

QSpinBox:disabled, QTimeEdit:disabled, QDateEdit:disabled {
    background-color: #F4F4F4;
    color: #888888;
    border: 1px solid #D6D6D6;
}

QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 1px solid #7A7A7A;
    border-radius: 2px;
    padding: 6px 8px;
    selection-background-color: #CCE4F7;
    selection-color: #000000;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #0078D7;
}

/* Group Boxes & Frames */
QGroupBox {
    border: 1px solid #C0C0C0;
    margin-top: 8px;
    padding-top: 10px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 8px;
    padding: 0 4px;
    background-color: #F0F0F0;
}

/* Tab Widgets */
QTabWidget::pane {
    border: 1px solid #A0A0A0;
    background-color: #FFFFFF;
}

QTabBar::tab {
    background-color: #E1E1E1;
    border: 1px solid #A0A0A0;
    border-bottom: none;
    padding: 6px 14px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    border-top: 2px solid #0078D7;
}

QTabBar::tab:hover:!selected {
    background-color: #EBF3FC;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: 1px solid #C0C0C0;
    background: #F0F0F0;
    width: 14px;
}

QScrollBar::handle:vertical {
    background: #CDCDCD;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #A6A6A6;
}

QScrollBar:horizontal {
    border: 1px solid #C0C0C0;
    background: #F0F0F0;
    height: 14px;
}

QScrollBar::handle:horizontal {
    background: #CDCDCD;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #A6A6A6;
}
"""

CLASSIC_DESKTOP_QSS = _RAW_QSS.replace("__ARROW_ICON_PATH__", ARROW_ICON_PATH)

