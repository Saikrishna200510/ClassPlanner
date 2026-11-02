"""
ClassPlanner - Supabase PostgreSQL Cloud Integration & Multi-Tenant Synchronization
Connects to Supabase PostgreSQL for cloud sync, multi-college governance,
and Row Level Security (RLS) enforcement.
"""

import os
import sys
from typing import Dict, Any, Tuple, Optional
from urllib.parse import quote_plus
import psycopg2
from psycopg2.extras import RealDictCursor
from classplanner.database.db_manager import DatabaseManager
from classplanner.config import (
    SUPABASE_HOST, SUPABASE_PORT, SUPABASE_DBNAME,
    SUPABASE_USER, SUPABASE_DEFAULT_PASSWORD
)

if getattr(sys, "frozen", False):
    SQL_FILE_PATH = os.path.join(getattr(sys, "_MEIPASS", ""), "classplanner", "database", "supabase_multitenant.sql")
else:
    SQL_FILE_PATH = os.path.join(os.path.dirname(__file__), "supabase_multitenant.sql")


class SupabaseManager:
    """Manages connections and multi-tenant synchronization with Supabase PostgreSQL."""

    def __init__(self, host: str = SUPABASE_HOST,
                 port: int = SUPABASE_PORT,
                 dbname: str = SUPABASE_DBNAME,
                 user: str = SUPABASE_USER,
                 password: str = SUPABASE_DEFAULT_PASSWORD):
        self.host = host.strip()
        self.port = int(port)
        self.dbname = dbname.strip()
        self.user = user.strip()
        cleaned_pwd = password.strip()
        if cleaned_pwd.startswith("[") and cleaned_pwd.endswith("]"):
            cleaned_pwd = cleaned_pwd[1:-1]
        self.password = cleaned_pwd

    def get_connection_string(self) -> str:
        """Returns the standardized, properly percent-encoded PostgreSQL URI."""
        enc_pwd = quote_plus(self.password)
        return f"postgresql://{self.user}:{enc_pwd}@{self.host}:{self.port}/{self.dbname}"

    def get_connection(self):
        """Connects directly to the Supabase PostgreSQL database."""
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password,
            connect_timeout=10
        )

    def test_connection(self) -> Tuple[bool, str]:
        """Tests network connectivity and credentials with Supabase."""
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            cur.close()
            conn.close()
            return True, f"Connected successfully!\n{ver.split(',')[0]}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def init_supabase_schema(self) -> Tuple[bool, str]:
        """Creates the full multi-tenant schema and RLS policies on Supabase PostgreSQL."""
        try:
            if not os.path.exists(SQL_FILE_PATH):
                return False, f"SQL migration file not found: {SQL_FILE_PATH}"

            with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
                schema_sql = f.read()

            conn = self.get_connection()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            conn.close()
            return True, "Supabase Multi-Tenant PostgreSQL schema and RLS policies initialized successfully."
        except Exception as e:
            return False, f"Failed to initialize schema: {str(e)}"

    def push_local_data_to_supabase(self, local_db: Optional[DatabaseManager] = None) -> Tuple[bool, str]:
        """
        Synchronizes all local SQLite records across all colleges into Supabase PostgreSQL.
        """
        db = local_db or DatabaseManager()
        ok, init_msg = self.init_supabase_schema()
        if not ok:
            return False, f"Schema initialization error: {init_msg}"

        try:
            pg_conn = self.get_connection()
            with pg_conn:
                with pg_conn.cursor() as pg_cur:
                    # Disable triggers/RLS temporarily for admin sync
                    pg_cur.execute("SET session_replication_role = 'replica';")

                    # Truncate existing cloud tables in reverse dependency order
                    pg_cur.execute("""
                        TRUNCATE TABLE 
                            public.timetable_entries,
                            public.timetables,
                            public.time_slots,
                            public.working_days,
                            public.sections,
                            public.subject_faculty,
                            public.subjects,
                            public.classrooms,
                            public.faculty_availability,
                            public.faculty,
                            public.semesters,
                            public.courses,
                            public.departments,
                            public.profiles,
                            public.colleges,
                            public.app_settings
                        CASCADE;
                    """)

                    sqlite_conn = db.get_connection()
                    sq_cur = sqlite_conn.cursor()

                    # 1. Colleges
                    sq_cur.execute("SELECT id, college_name, college_code, address, email, phone, status FROM colleges ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.colleges (id, college_name, college_code, address, email, phone, status) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_name"], r["college_code"], r["address"], r["email"], r["phone"], r["status"])
                        )

                    # 2. Profiles (Users)
                    sq_cur.execute("SELECT id, full_name, email, password_hash, role, college_id, phone, is_active FROM profiles ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.profiles (id, full_name, email, password_hash, role, college_id, phone, is_active) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["full_name"], r["email"], r["password_hash"], r["role"], r["college_id"], r["phone"], r["is_active"])
                        )

                    # 3. Departments
                    sq_cur.execute("SELECT id, college_id, code, name, hod_name FROM departments ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.departments (id, college_id, code, name, hod_name) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["code"], r["name"], r["hod_name"])
                        )

                    # 4. Courses
                    sq_cur.execute("SELECT id, college_id, course_code, course_name, department_id, duration_years FROM courses ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.courses (id, college_id, course_code, course_name, department_id, duration_years) "
                            "VALUES (%s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["course_code"], r["course_name"], r["department_id"], r["duration_years"])
                        )

                    # 5. Semesters
                    sq_cur.execute("SELECT id, college_id, semester_number, academic_year, term_type, is_active FROM semesters ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.semesters (id, college_id, semester_number, academic_year, term_type, is_active) "
                            "VALUES (%s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["semester_number"], r["academic_year"], r["term_type"], r["is_active"])
                        )

                    # 6. Faculty
                    sq_cur.execute("SELECT id, college_id, faculty_id, name, department_id, designation, email, phone, max_hours_per_day, max_hours_per_week, is_active FROM faculty ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.faculty (id, college_id, faculty_id, name, department_id, designation, email, phone, max_hours_per_day, max_hours_per_week, is_active) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["faculty_id"], r["name"], r["department_id"], r["designation"], r["email"], r["phone"], r["max_hours_per_day"], r["max_hours_per_week"], r["is_active"])
                        )

                    # 7. Faculty Availability
                    sq_cur.execute("SELECT college_id, faculty_id, day_name, slot_number, is_available FROM faculty_availability")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.faculty_availability (college_id, faculty_id, day_name, slot_number, is_available) "
                            "VALUES (%s, %s, %s, %s, %s)",
                            (r["college_id"], r["faculty_id"], r["day_name"], r["slot_number"], r["is_available"])
                        )

                    # 8. Classrooms
                    sq_cur.execute("SELECT id, college_id, room_number, building_name, capacity, room_type, department_id, is_available FROM classrooms ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.classrooms (id, college_id, room_number, building_name, capacity, room_type, department_id, is_available) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["room_number"], r["building_name"], r["capacity"], r["room_type"], r["department_id"], r["is_available"])
                        )

                    # 9. Subjects
                    sq_cur.execute("SELECT id, college_id, code, name, department_id, semester, subject_type, weekly_hours, consecutive_periods, requires_lab, default_faculty_id FROM subjects ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.subjects (id, college_id, code, name, department_id, semester, subject_type, weekly_hours, consecutive_periods, requires_lab, default_faculty_id) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["code"], r["name"], r["department_id"], r["semester"], r["subject_type"], r["weekly_hours"], r["consecutive_periods"], r["requires_lab"], r["default_faculty_id"])
                        )

                    # 10. Subject-Faculty
                    sq_cur.execute("SELECT college_id, subject_id, faculty_id, is_primary FROM subject_faculty")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.subject_faculty (college_id, subject_id, faculty_id, is_primary) "
                            "VALUES (%s, %s, %s, %s)",
                            (r["college_id"], r["subject_id"], r["faculty_id"], r["is_primary"])
                        )

                    # 11. Sections
                    sq_cur.execute("SELECT id, college_id, department_id, academic_year, semester, section_name, student_count, assigned_classroom_id FROM sections ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.sections (id, college_id, department_id, academic_year, semester, section_name, student_count, assigned_classroom_id) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["department_id"], r["academic_year"], r["semester"], r["section_name"], r["student_count"], r["assigned_classroom_id"])
                        )

                    # 12. Working Days
                    sq_cur.execute("SELECT college_id, day_name, is_working, display_order FROM working_days")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.working_days (college_id, day_name, is_working, display_order) "
                            "VALUES (%s, %s, %s, %s)",
                            (r["college_id"], r["day_name"], r["is_working"], r["display_order"])
                        )

                    # 13. Time Slots
                    sq_cur.execute("SELECT college_id, slot_number, slot_name, start_time, end_time, is_break, break_type, display_order FROM time_slots")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.time_slots (college_id, slot_number, slot_name, start_time, end_time, is_break, break_type, display_order) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["college_id"], r["slot_number"], r["slot_name"], r["start_time"], r["end_time"], r["is_break"], r["break_type"], r["display_order"])
                        )

                    # 14. Timetables & Entries
                    sq_cur.execute("SELECT id, college_id, name, academic_year, semester_type, is_active, generation_fitness, notes FROM timetables ORDER BY id")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.timetables (id, college_id, name, academic_year, semester_type, is_active, generation_fitness, notes) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["name"], r["academic_year"], r["semester_type"], r["is_active"], r["generation_fitness"], r["notes"])
                        )

                    sq_cur.execute("SELECT id, college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked FROM timetable_entries")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.timetable_entries (id, college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (r["id"], r["college_id"], r["timetable_id"], r["section_id"], r["day_name"], r["slot_number"], r["subject_id"], r["faculty_id"], r["classroom_id"], r["is_locked"])
                        )

                    # 15. Settings
                    sq_cur.execute("SELECT key, value, college_id FROM app_settings")
                    for r in sq_cur.fetchall():
                        pg_cur.execute(
                            "INSERT INTO public.app_settings (key, value, college_id) VALUES (%s, %s, %s) "
                            "ON CONFLICT(key, college_id) DO UPDATE SET value = EXCLUDED.value",
                            (r["key"], r["value"], r["college_id"] or 1)
                        )

                    # Update PostgreSQL sequences
                    seq_tables = ['colleges', 'profiles', 'departments', 'courses', 'semesters', 'faculty', 'classrooms', 'subjects', 'sections', 'timetables', 'timetable_entries']
                    for t in seq_tables:
                        pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('public.{t}', 'id'), COALESCE(MAX(id), 1)) FROM public.{t};")

                    # Re-enable standard session replication role
                    pg_cur.execute("SET session_replication_role = 'origin';")
                    sqlite_conn.close()

            pg_conn.close()
            return True, "Successfully synced all multi-college institutional data to Supabase PostgreSQL!"
        except Exception as e:
            return False, f"Sync to Supabase failed: {str(e)}"
