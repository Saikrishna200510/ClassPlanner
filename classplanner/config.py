"""
ClassPlanner - Application Configuration and Constants
Traditional Desktop College Timetable Management System
"""

import os
import sys

APP_NAME = "ClassPlanner"
APP_VERSION = "1.0.0"
APP_ORGANIZATION = "SL IT Solutions"

# Application Base Directory
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data and Database Directory
custom_data_dir = os.environ.get("CLASSPLANNER_DATA_DIR")
if custom_data_dir:
    DATA_DIR = custom_data_dir
elif getattr(sys, "frozen", False):
    # Standalone packaged application: write to OS-standard user appdata folder
    if sys.platform == "win32":
        base_user_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        DATA_DIR = os.path.join(base_user_dir, "ClassPlanner", "data")
    elif sys.platform == "darwin":
        DATA_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "ClassPlanner", "data")
    else:
        base_user_dir = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
        DATA_DIR = os.path.join(base_user_dir, "classplanner", "data")
else:
    # Development mode: prefer local workspace data/ directory if present
    project_data_dir = os.path.join(os.path.dirname(BASE_DIR), "data")
    if os.path.exists(project_data_dir):
        DATA_DIR = project_data_dir
    else:
        DATA_DIR = os.path.join(os.path.expanduser("~"), ".classplanner", "data")

os.makedirs(DATA_DIR, exist_ok=True)

DEFAULT_DB_PATH = os.path.join(DATA_DIR, "classplanner.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Production Backend & Cloud Synchronization Settings
# Reads from environment variables if configured, with secure fallback
PRODUCTION_API_URL = os.environ.get("CLASSPLANNER_API_URL", "https://api.classplanner.slit.edu")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lmllravkxpdqigkfprgx.supabase.co")
SUPABASE_HOST = os.environ.get("SUPABASE_HOST", "db.lmllravkxpdqigkfprgx.supabase.co")
SUPABASE_PORT = int(os.environ.get("SUPABASE_PORT", "5432"))
SUPABASE_DBNAME = os.environ.get("SUPABASE_DBNAME", "postgres")
SUPABASE_USER = os.environ.get("SUPABASE_USER", "postgres")
SUPABASE_DEFAULT_PASSWORD = os.environ.get("SUPABASE_PASSWORD", "Krishna@6301986030")

# Standard Days of Week
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Classroom Types
ROOM_TYPE_REGULAR = "Regular Classroom"
ROOM_TYPE_LAB = "Laboratory / Computer Lab"
ROOM_TYPE_SEMINAR = "Seminar Hall / Auditorium"
ROOM_TYPES = [ROOM_TYPE_REGULAR, ROOM_TYPE_LAB, ROOM_TYPE_SEMINAR]

# Subject Types
SUBJECT_TYPE_THEORY = "Theory"
SUBJECT_TYPE_PRACTICAL = "Practical / Laboratory"
SUBJECT_TYPES = [SUBJECT_TYPE_THEORY, SUBJECT_TYPE_PRACTICAL]

# Faculty Designations
FACULTY_DESIGNATIONS = [
    "Professor & Head of Department",
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Senior Lecturer",
    "Lecturer",
    "Adjunct Faculty",
    "Lab Assistant / Instructor"
]

# Default Institution Settings
DEFAULT_SETTINGS = {
    "institution_name": "Government Engineering College",
    "institution_address": "College Campus, University Road, City - 500001",
    "academic_year": "2026-2027",
    "academic_term": "Even Semester (II, IV, VI, VIII)",
    "admin_password_hash": "",  # Empty = No password required by default
    "require_login": "0",
    "college_start_time": "09:00",
    "college_end_time": "16:30",
    "period_duration_minutes": "50",
    "lunch_start_time": "12:20",
    "lunch_duration_minutes": "50",
    "tea_break_enabled": "1",
    "tea_break_start_time": "11:20",
    "tea_break_duration_minutes": "10",
    "periods_per_day": "7",
}
