"""
ClassPlanner - SQLite Multi-Tenant Database Schema Definitions
Supports multiple colleges with isolated departments, faculty, subjects,
classrooms, courses, semesters, sections, and timetables.
"""

SCHEMA_SQL = """
-- 1. Colleges Table (Central Multi-Tenant Registry)
CREATE TABLE IF NOT EXISTS colleges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_name TEXT NOT NULL,
    college_code TEXT UNIQUE NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT,
    status TEXT DEFAULT 'active', -- 'active' or 'inactive'
    logo_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. User Profiles Table (Authentication & RBAC)
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('super_admin', 'college_admin', 'faculty')),
    college_id INTEGER REFERENCES colleges(id) ON DELETE CASCADE,
    phone TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    hod_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, code)
);

-- 4. Courses / Academic Programs Table
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    duration_years INTEGER DEFAULT 4,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, course_code)
);

-- 5. Semesters Table
CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    semester_number INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    term_type TEXT NOT NULL DEFAULT 'Even', -- 'Odd' or 'Even'
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, academic_year, semester_number)
);

-- 6. Faculty Table
CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    faculty_id TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    designation TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    max_hours_per_day INTEGER DEFAULT 4,
    max_hours_per_week INTEGER DEFAULT 18,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, faculty_id)
);

-- 7. Faculty Availability Table
CREATE TABLE IF NOT EXISTS faculty_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    is_available INTEGER DEFAULT 1,
    UNIQUE(college_id, faculty_id, day_name, slot_number)
);

-- 8. Classrooms Table
CREATE TABLE IF NOT EXISTS classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    room_number TEXT NOT NULL,
    building_name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    is_available INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, room_number)
);

-- 9. Subjects Curriculum Table
CREATE TABLE IF NOT EXISTS subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    semester INTEGER NOT NULL,
    subject_type TEXT NOT NULL,
    weekly_hours INTEGER NOT NULL DEFAULT 4,
    consecutive_periods INTEGER NOT NULL DEFAULT 1,
    requires_lab INTEGER NOT NULL DEFAULT 0,
    default_faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, code)
);

-- 10. Subject-Faculty Mapping Table
CREATE TABLE IF NOT EXISTS subject_faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    is_primary INTEGER DEFAULT 1,
    UNIQUE(college_id, subject_id, faculty_id)
);

-- 11. Student Sections Table
CREATE TABLE IF NOT EXISTS sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section_name TEXT NOT NULL,
    student_count INTEGER NOT NULL DEFAULT 60,
    assigned_classroom_id INTEGER REFERENCES classrooms(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, department_id, semester, section_name)
);

-- 12. Working Days Table
CREATE TABLE IF NOT EXISTS working_days (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    is_working INTEGER DEFAULT 1,
    display_order INTEGER NOT NULL,
    UNIQUE(college_id, day_name)
);

-- 13. Time Slots Table
CREATE TABLE IF NOT EXISTS time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    slot_number INTEGER NOT NULL,
    slot_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_break INTEGER DEFAULT 0,
    break_type TEXT DEFAULT '',
    display_order INTEGER NOT NULL,
    UNIQUE(college_id, slot_number)
);

-- 14. Master Timetables Table
CREATE TABLE IF NOT EXISTS timetables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester_type TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    generation_fitness REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 15. Timetable Entries Table
CREATE TABLE IF NOT EXISTS timetable_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    college_id INTEGER NOT NULL DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    timetable_id INTEGER NOT NULL REFERENCES timetables(id) ON DELETE CASCADE,
    section_id INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES faculty(id) ON DELETE CASCADE,
    classroom_id INTEGER NOT NULL REFERENCES classrooms(id) ON DELETE CASCADE,
    is_locked INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, timetable_id, section_id, day_name, slot_number)
);

-- 16. Timetable Slots View (Multi-Tenant Alias)
CREATE VIEW IF NOT EXISTS timetable_slots AS 
SELECT id, college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked, created_at 
FROM timetable_entries;

-- 17. Application & College Settings Table
CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    college_id INTEGER DEFAULT 1 REFERENCES colleges(id) ON DELETE CASCADE,
    PRIMARY KEY(key, college_id)
);

-- Multi-Tenant Indexes
CREATE INDEX IF NOT EXISTS idx_colleges_code ON colleges(college_code);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_college ON profiles(college_id);
CREATE INDEX IF NOT EXISTS idx_dept_college ON departments(college_id);
CREATE INDEX IF NOT EXISTS idx_fac_college ON faculty(college_id);
CREATE INDEX IF NOT EXISTS idx_rooms_college ON classrooms(college_id);
CREATE INDEX IF NOT EXISTS idx_subj_college ON subjects(college_id);
CREATE INDEX IF NOT EXISTS idx_sec_college ON sections(college_id);
CREATE INDEX IF NOT EXISTS idx_tt_college ON timetables(college_id);
CREATE INDEX IF NOT EXISTS idx_entries_tt ON timetable_entries(timetable_id);
CREATE INDEX IF NOT EXISTS idx_entries_college ON timetable_entries(college_id);
CREATE INDEX IF NOT EXISTS idx_entries_fac ON timetable_entries(college_id, timetable_id, faculty_id, day_name, slot_number);
CREATE INDEX IF NOT EXISTS idx_entries_room ON timetable_entries(college_id, timetable_id, classroom_id, day_name, slot_number);
CREATE INDEX IF NOT EXISTS idx_entries_sec ON timetable_entries(college_id, timetable_id, section_id, day_name, slot_number);
"""
