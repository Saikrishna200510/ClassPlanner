"""
ClassPlanner Widgets Package
"""

from classplanner.ui.widgets.dashboard_widget import DashboardWidget
from classplanner.ui.widgets.department_widget import DepartmentWidget
from classplanner.ui.widgets.faculty_widget import FacultyWidget
from classplanner.ui.widgets.subject_widget import SubjectWidget
from classplanner.ui.widgets.classroom_widget import ClassroomWidget
from classplanner.ui.widgets.section_widget import SectionWidget
from classplanner.ui.widgets.working_hours_widget import WorkingHoursWidget
from classplanner.ui.widgets.generator_widget import GeneratorWidget
from classplanner.ui.widgets.timetable_view_widget import TimetableGridWidget
from classplanner.ui.widgets.reports_widget import ReportsWidget
from classplanner.ui.widgets.settings_widget import SettingsWidget
from classplanner.ui.widgets.super_admin_widget import SuperAdminWidget
from classplanner.ui.widgets.course_semester_widget import CourseSemesterWidget

__all__ = [
    "DashboardWidget", "DepartmentWidget", "FacultyWidget",
    "SubjectWidget", "ClassroomWidget", "SectionWidget",
    "WorkingHoursWidget", "GeneratorWidget", "TimetableGridWidget",
    "ReportsWidget", "SettingsWidget", "SuperAdminWidget", "CourseSemesterWidget"
]
