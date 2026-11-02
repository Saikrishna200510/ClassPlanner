"""
UI Tests for ClassPlanner
Verifies that all widgets, tables, dialogs, and navigation operate cleanly.
"""

import sys
import pytest
from PySide6.QtWidgets import QApplication
from classplanner.database import DatabaseManager, load_sample_college_data
from classplanner.ui.main_window import MainWindow
from classplanner.ui.widgets import (
    DashboardWidget, DepartmentWidget, FacultyWidget,
    SubjectWidget, ClassroomWidget, SectionWidget,
    WorkingHoursWidget, GeneratorWidget, TimetableGridWidget,
    ReportsWidget, SettingsWidget
)
from classplanner.ui.dialogs import AboutDialog, EditCellDialog


@pytest.fixture(scope="session")
def qapp():
    """Initializes QApplication once for session."""
    import gc
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    gc.collect()


@pytest.fixture
def test_db():
    db = DatabaseManager()
    load_sample_college_data(db, force=True)
    return db


def test_main_window_and_navigation(qapp, test_db):
    win = MainWindow(test_db)
    assert win.windowTitle().startswith("ClassPlanner")

    # Test navigation to each module
    keys = [
        "dashboard", "departments", "faculty", "subjects",
        "classrooms", "sections", "working_hours", "generator",
        "timetable_view", "reports", "settings"
    ]
    for k in keys:
        win.navigate_to_key(k)
        assert win.stack.currentIndex() >= 0
    win.deleteLater()


def test_individual_widgets(qapp, test_db):
    dash = DashboardWidget(test_db)
    dash.refresh_stats()
    assert int(dash.card_depts.lbl_val.text()) >= 3

    dept_w = DepartmentWidget(test_db)
    assert dept_w.table.rowCount() >= 3

    fac_w = FacultyWidget(test_db)
    assert fac_w.table.rowCount() >= 10

    sub_w = SubjectWidget(test_db)
    assert sub_w.table.rowCount() >= 15

    room_w = ClassroomWidget(test_db)
    assert room_w.table.rowCount() >= 8

    sec_w = SectionWidget(test_db)
    assert sec_w.table.rowCount() >= 4

    hrs_w = WorkingHoursWidget(test_db)
    assert hrs_w.table.rowCount() >= 7

    gen_w = GeneratorWidget(test_db)
    assert gen_w.btn_generate.isEnabled()

    # Generate a timetable so timetable grid and reports have active data
    from classplanner.solver import TimetableGenerator
    gen = TimetableGenerator(test_db)
    res = gen.generate("Test UI Timetable", "2026-2027", "Even")
    assert res.success is True

    tt_w = TimetableGridWidget(test_db)
    assert tt_w.table.rowCount() >= 7
    assert tt_w.cmb_view_mode.minimumWidth() >= 160
    assert tt_w.cmb_timetables.minimumWidth() >= 240
    assert tt_w.cmb_target.minimumWidth() >= 240

    rep_w = ReportsWidget(test_db)
    assert rep_w.tbl_workload.rowCount() >= 10

    set_w = SettingsWidget(test_db)
    assert len(set_w.txt_inst_name.text()) > 0

    from classplanner.ui.widgets import SuperAdminWidget, CourseSemesterWidget
    sa_w = SuperAdminWidget(test_db)
    assert sa_w.table.rowCount() >= 2

    cs_w = CourseSemesterWidget(test_db)
    assert cs_w.tbl_courses is not None


def test_about_dialog(qapp):
    dlg = AboutDialog()
    assert "ClassPlanner" in dlg.windowTitle()
