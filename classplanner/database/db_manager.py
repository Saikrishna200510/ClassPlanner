"""
ClassPlanner - Multi-Tenant Database Manager
Handles SQLite connection, transactions, multi-college tenancy scoping,
and CRUD operations for all platform entities.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional, Tuple
from classplanner.config import DEFAULT_DB_PATH, DEFAULT_SETTINGS, DAYS_OF_WEEK
from classplanner.database.schema import SCHEMA_SQL


class DatabaseManager:
    """Singleton Database Manager for ClassPlanner SQLite database with multi-college tenancy."""
    _instance = None

    def __new__(cls, db_path: str = None):
        target_path = db_path or DEFAULT_DB_PATH
        if cls._instance is None or (db_path is not None and cls._instance.db_path != db_path):
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.db_path = target_path
            cls._instance.current_college_id = 1  # Default to College 1 for backward compatibility
            cls._instance.init_database()
        elif not os.path.exists(cls._instance.db_path):
            cls._instance.db_path = target_path
            cls._instance.current_college_id = 1
            cls._instance.init_database()
        return cls._instance

    @classmethod
    def reset_instance(cls, db_path: str = None):
        """Reset singleton with new path (used for restore/testing)."""
        cls._instance = None
        return cls(db_path)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory configured."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_database(self):
        """Initialize tables, apply multi-tenant schema migrations, and load default colleges/profiles."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Migrate existing tables to include college_id if they were created by older schema
            # Run this BEFORE executescript(SCHEMA_SQL) so views and indexes can reference college_id
            tables_to_check = [
                "departments", "faculty", "faculty_availability", "classrooms",
                "subjects", "subject_faculty", "sections", "working_days",
                "time_slots", "timetables", "timetable_entries", "app_settings"
            ]
            for t in tables_to_check:
                try:
                    cursor.execute(f"PRAGMA table_info({t});")
                    cols = [c[1] for c in cursor.fetchall()]
                    if cols and "college_id" not in cols:
                        cursor.execute(f"ALTER TABLE {t} ADD COLUMN college_id INTEGER DEFAULT 1;")
                except Exception:
                    pass
            conn.commit()

            cursor.executescript(SCHEMA_SQL)
            conn.commit()

            # Ensure default colleges exist
            cursor.execute("SELECT id FROM colleges WHERE id = 1")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT OR REPLACE INTO colleges (id, college_name, college_code, address, email, phone, status)
                    VALUES 
                    (1, 'Government Engineering College', 'GEC-01', 'University Road, North Campus', 'contact@gec.edu', '+91 98765 43210', 'active'),
                    (2, 'National Institute of Technology', 'NIT-02', 'Tech Park Boulevard, South Zone', 'admin@nit.edu', '+91 98765 88990', 'active');
                """)
                conn.commit()

            # Ensure initial profiles exist (Super Admin & College Admins)
            cursor.execute("SELECT COUNT(*) FROM profiles")
            if cursor.fetchone()[0] == 0:
                from classplanner.auth.auth_service import hash_password
                cursor.execute("""
                    INSERT INTO profiles (full_name, email, password_hash, role, college_id, phone, is_active)
                    VALUES
                    (?, ?, ?, 'super_admin', NULL, '+91 90000 00001', 1),
                    (?, ?, ?, 'college_admin', 1, '+91 98765 43211', 1),
                    (?, ?, ?, 'college_admin', 2, '+91 98765 88991', 1);
                """, (
                    "ClassPlanner Super Administrator", "superadmin@classplanner.edu", hash_password("Admin@12345"),
                    "GEC College Administrator", "admin@gec.edu", hash_password("College@12345"),
                    "NIT College Administrator", "admin@nit.edu", hash_password("Nit@12345")
                ))
                conn.commit()

            # Ensure default working days and slots exist for college 1 and 2
            for cid in [1, 2]:
                cursor.execute("SELECT COUNT(*) FROM working_days WHERE college_id = ?", (cid,))
                if cursor.fetchone()[0] == 0:
                    for i, day in enumerate(DAYS_OF_WEEK):
                        cursor.execute(
                            "INSERT OR IGNORE INTO working_days (college_id, day_name, is_working, display_order) VALUES (?, ?, 1, ?)",
                            (cid, day, i + 1)
                        )
                cursor.execute("SELECT COUNT(*) FROM time_slots WHERE college_id = ?", (cid,))
                if cursor.fetchone()[0] == 0:
                    self._generate_default_time_slots(cursor, cid)

            # Initialize Default Settings for active colleges
            for key, val in DEFAULT_SETTINGS.items():
                cursor.execute(
                    "INSERT OR IGNORE INTO app_settings (key, value, college_id) VALUES (?, ?, 1)",
                    (key, str(val))
                )

            conn.commit()

    def _generate_default_time_slots(self, cursor: sqlite3.Cursor, college_id: int = 1):
        """Populate initial 7 teaching periods with a Tea Break and Lunch Break for a college."""
        slots = [
            (1, "Period 1", "09:00", "09:50", 0, "", 1),
            (2, "Period 2", "09:50", "10:40", 0, "", 2),
            (3, "Period 3", "10:40", "11:30", 0, "", 3),
            (4, "Tea Break", "11:30", "11:45", 1, "Tea", 4),
            (5, "Period 4", "11:45", "12:35", 0, "", 5),
            (6, "Lunch Break", "12:35", "13:25", 1, "Lunch", 6),
            (7, "Period 5", "13:25", "14:15", 0, "", 7),
            (8, "Period 6", "14:15", "15:05", 0, "", 8),
            (9, "Period 7", "15:05", "15:55", 0, "", 9),
        ]
        for slot in slots:
            cursor.execute(
                """INSERT OR IGNORE INTO time_slots 
                   (college_id, slot_number, slot_name, start_time, end_time, is_break, break_type, display_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (college_id, slot[0], slot[1], slot[2], slot[3], slot[4], slot[5], slot[6])
            )

    def get_or_create_default_college_id(self) -> int:
        """Returns active college id or creates/fetches default college 1."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.current_college_id:
                cursor.execute("SELECT id FROM colleges WHERE id = ?", (self.current_college_id,))
                row = cursor.fetchone()
                if row:
                    return row[0]
            cursor.execute("SELECT id FROM colleges ORDER BY id ASC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row[0]
            cursor.execute("""
                INSERT OR REPLACE INTO colleges (id, college_name, college_code, status)
                VALUES (1, 'Government Engineering College', 'GEC-01', 'active')
            """)
            conn.commit()
            return 1

    # -------------------------------------------------------------
    # Multi-Tenant Context Helpers
    # -------------------------------------------------------------
    def set_active_college(self, college_id: Optional[int]):
        """Sets the active college tenant for scoped operations."""
        self.current_college_id = college_id

    def get_active_college(self) -> Optional[Dict[str, Any]]:
        """Retrieves details of currently active college."""
        if not self.current_college_id:
            return None
        return self.get_college(self.current_college_id)

    # -------------------------------------------------------------
    # Super Admin & College Management Operations
    # -------------------------------------------------------------
    def get_super_admin_stats(self) -> Dict[str, Any]:
        """Calculates global platform KPIs across all colleges for Super Admin."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM colleges")
            total_colleges = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM colleges WHERE status = 'active'")
            active_colleges = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM colleges WHERE status != 'active'")
            inactive_colleges = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM profiles WHERE role = 'college_admin'")
            total_admins = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM faculty WHERE is_active = 1")
            total_faculty = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM timetables")
            total_timetables = cursor.fetchone()[0]

            cursor.execute("""
                SELECT c.id, c.college_name, c.college_code, c.status, c.created_at,
                       p.full_name as admin_name, p.email as admin_email
                FROM colleges c
                LEFT JOIN profiles p ON p.college_id = c.id AND p.role = 'college_admin'
                ORDER BY c.created_at DESC LIMIT 10
            """)
            recent_colleges = [dict(r) for r in cursor.fetchall()]

            return {
                "total_colleges": total_colleges,
                "active_colleges": active_colleges,
                "inactive_colleges": inactive_colleges,
                "total_college_admins": total_admins,
                "total_faculty": total_faculty,
                "total_timetables": total_timetables,
                "recent_colleges": recent_colleges
            }

    def get_colleges(self, status_filter: Optional[str] = None, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetches list of registered colleges with statistics and admin info."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.*, 
                       p.full_name as admin_name, p.email as admin_email,
                       (SELECT COUNT(*) FROM departments WHERE college_id = c.id) as dept_count,
                       (SELECT COUNT(*) FROM faculty WHERE college_id = c.id) as faculty_count,
                       (SELECT COUNT(*) FROM timetables WHERE college_id = c.id) as timetable_count
                FROM colleges c
                LEFT JOIN profiles p ON p.college_id = c.id AND p.role = 'college_admin'
                WHERE 1=1
            """
            params = []
            if status_filter and status_filter.lower() != "all":
                query += " AND c.status = ?"
                params.append(status_filter.lower())
            if search_query:
                query += " AND (c.college_name LIKE ? OR c.college_code LIKE ? OR c.email LIKE ?)"
                like_term = f"%{search_query.strip()}%"
                params.extend([like_term, like_term, like_term])
            query += " ORDER BY c.id ASC"
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]

    def get_college(self, college_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, p.full_name as admin_name, p.email as admin_email
                FROM colleges c
                LEFT JOIN profiles p ON p.college_id = c.id AND p.role = 'college_admin'
                WHERE c.id = ?
            """, (college_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_college(self, college_name: str, college_code: str, address: str = "",
                    email: str = "", phone: str = "", status: str = "active",
                    admin_name: str = "", admin_email: str = "", admin_password: str = "") -> int:
        """Registers a new college and optionally provisions its College Admin account."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO colleges (college_name, college_code, address, email, phone, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (college_name.strip(), college_code.strip().upper(), address.strip(),
                  email.strip(), phone.strip(), status.strip()))
            college_id = cursor.lastrowid

            # Initialize working days & time slots for new college
            for i, day in enumerate(DAYS_OF_WEEK):
                cursor.execute(
                    "INSERT OR IGNORE INTO working_days (college_id, day_name, is_working, display_order) VALUES (?, ?, 1, ?)",
                    (college_id, day, i + 1)
                )
            self._generate_default_time_slots(cursor, college_id)

            # Create initial College Admin if provided
            if admin_email and admin_password:
                from classplanner.auth.auth_service import hash_password
                cursor.execute("""
                    INSERT INTO profiles (full_name, email, password_hash, role, college_id, phone, is_active)
                    VALUES (?, ?, ?, 'college_admin', ?, ?, 1)
                """, (
                    admin_name.strip() or f"{college_code} Administrator",
                    admin_email.strip().lower(),
                    hash_password(admin_password),
                    college_id,
                    phone.strip()
                ))
            conn.commit()
            return college_id

    def update_college(self, college_id: int, college_name: str, college_code: str,
                       address: str = "", email: str = "", phone: str = "", status: str = "active") -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE colleges 
                SET college_name = ?, college_code = ?, address = ?, email = ?, phone = ?, status = ?
                WHERE id = ?
            """, (college_name.strip(), college_code.strip().upper(), address.strip(),
                  email.strip(), phone.strip(), status.strip(), college_id))
            conn.commit()
            return True

    def set_college_status(self, college_id: int, status: str) -> bool:
        with self.get_connection() as conn:
            conn.execute("UPDATE colleges SET status = ? WHERE id = ?", (status, college_id))
            conn.commit()
            return True

    def delete_college(self, college_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT college_name FROM colleges WHERE id = ?", (college_id,))
            row = cursor.fetchone()
            if not row:
                return False, "College not found."
            name = row["college_name"]
            cursor.execute("DELETE FROM colleges WHERE id = ?", (college_id,))
            conn.commit()
            return True, f"College '{name}' and all associated records deleted."

    # -------------------------------------------------------------
    # User Profile Operations (Supabase Authentication & RBAC)
    # -------------------------------------------------------------
    def get_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE email = ?", (email.strip().lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_profile(self, email: str, full_name: str, password_hash: str, role: str,
                    college_id: Optional[int] = None, phone: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (full_name, email, password_hash, role, college_id, phone, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (full_name.strip(), email.strip().lower(), password_hash, role, college_id, phone.strip()))
            conn.commit()
            return cursor.lastrowid

    def update_user_password(self, user_id: int, password_hash: str) -> bool:
        with self.get_connection() as conn:
            conn.execute("UPDATE profiles SET password_hash = ? WHERE id = ?", (password_hash, user_id))
            conn.commit()
            return True

    def get_college_admin(self, college_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM profiles WHERE college_id = ? AND role = 'college_admin' LIMIT 1", (college_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_profiles(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if college_id is not None:
                cursor.execute("SELECT * FROM profiles WHERE college_id = ? ORDER BY id ASC", (college_id,))
            else:
                cursor.execute("SELECT * FROM profiles ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    # -------------------------------------------------------------
    # Settings Operations
    # -------------------------------------------------------------
    def get_setting(self, key: str, default: str = "", college_id: Optional[int] = None) -> str:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_settings WHERE key = ? AND college_id = ?", (key, cid))
            row = cursor.fetchone()
            if row:
                return row["value"]
            # Fallback to key without college_id check
            cursor.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row2 = cursor.fetchone()
            return row2["value"] if row2 else default

    def set_setting(self, key: str, value: str, college_id: Optional[int] = None):
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO app_settings (key, value, college_id) VALUES (?, ?, ?) "
                "ON CONFLICT(key, college_id) DO UPDATE SET value = excluded.value",
                (key, str(value), cid)
            )
            conn.commit()

    def get_all_settings(self, college_id: Optional[int] = None) -> Dict[str, str]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM app_settings WHERE college_id = ?", (cid,))
            return {row["key"]: row["value"] for row in cursor.fetchall()}

    # -------------------------------------------------------------
    # Department Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_departments(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cid is not None:
                cursor.execute("SELECT * FROM departments WHERE college_id = ? ORDER BY code ASC", (cid,))
            else:
                cursor.execute("SELECT * FROM departments ORDER BY code ASC")
            return [dict(row) for row in cursor.fetchall()]

    def get_department(self, dept_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM departments WHERE id = ?", (dept_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_department(self, code: str, name: str, hod_name: str = "", college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else self.get_or_create_default_college_id()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO departments (college_id, code, name, hod_name) VALUES (?, ?, ?, ?)",
                (cid, code.strip().upper(), name.strip(), hod_name.strip())
            )
            conn.commit()
            return cursor.lastrowid

    def update_department(self, dept_id: int, code: str, name: str, hod_name: str = "") -> bool:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE departments SET code = ?, name = ?, hod_name = ? WHERE id = ?",
                (code.strip().upper(), name.strip(), hod_name.strip(), dept_id)
            )
            conn.commit()
            return True

    def delete_department(self, dept_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM faculty WHERE department_id = ?", (dept_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete department: Faculty members are assigned to it."
            cursor.execute("SELECT COUNT(*) FROM subjects WHERE department_id = ?", (dept_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete department: Subjects are assigned to it."
            cursor.execute("SELECT COUNT(*) FROM sections WHERE department_id = ?", (dept_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete department: Student sections are linked to it."

            conn.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
            conn.commit()
            return True, "Department deleted successfully."

    # -------------------------------------------------------------
    # Courses & Semesters Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_courses(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cid is not None:
                cursor.execute("""
                    SELECT c.*, d.name as department_name, d.code as department_code 
                    FROM courses c
                    LEFT JOIN departments d ON d.id = c.department_id
                    WHERE c.college_id = ?
                    ORDER BY c.course_code ASC
                """, (cid,))
            else:
                cursor.execute("""
                    SELECT c.*, d.name as department_name, d.code as department_code 
                    FROM courses c
                    LEFT JOIN departments d ON d.id = c.department_id
                    ORDER BY c.course_code ASC
                """)
            return [dict(r) for r in cursor.fetchall()]

    def add_course(self, course_code: str, course_name: str, department_id: Optional[int] = None,
                   duration_years: int = 4, college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO courses (college_id, course_code, course_name, department_id, duration_years)
                VALUES (?, ?, ?, ?, ?)
            """, (cid, course_code.strip().upper(), course_name.strip(), department_id, duration_years))
            conn.commit()
            return cursor.lastrowid

    def delete_course(self, course_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            return True

    def get_semesters(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cid is not None:
                cursor.execute("SELECT * FROM semesters WHERE college_id = ? ORDER BY academic_year DESC, semester_number ASC", (cid,))
            else:
                cursor.execute("SELECT * FROM semesters ORDER BY academic_year DESC, semester_number ASC")
            return [dict(r) for r in cursor.fetchall()]

    def add_semester(self, semester_number: int, academic_year: str, term_type: str = "Even",
                     college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO semesters (college_id, semester_number, academic_year, term_type, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (cid, semester_number, academic_year.strip(), term_type.strip()))
            conn.commit()
            return cursor.lastrowid

    def delete_semester(self, semester_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM semesters WHERE id = ?", (semester_id,))
            conn.commit()
            return True

    # -------------------------------------------------------------
    # Faculty Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_faculty_list(self, department_id: Optional[int] = None, active_only: bool = False,
                         college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT f.*, 
                       d.name as department_name, d.code as department_code,
                       d.name as dept_name, d.code as dept_code
                FROM faculty f
                JOIN departments d ON f.department_id = d.id
                WHERE 1=1
            """
            params = []
            if cid is not None:
                query += " AND f.college_id = ?"
                params.append(cid)
            if department_id:
                query += " AND f.department_id = ?"
                params.append(department_id)
            if active_only:
                query += " AND f.is_active = 1"
            query += " ORDER BY f.name ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_faculty(self, faculty_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, d.name as department_name, d.code as department_code 
                FROM faculty f
                JOIN departments d ON f.department_id = d.id
                WHERE f.id = ?
            """, (faculty_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_faculty(self, faculty_id_code: str, name: str, department_id: int, designation: str,
                    email: str = "", phone: str = "", max_hours_per_day: int = 4,
                    max_hours_per_week: int = 18, is_active: int = 1, college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else self.get_or_create_default_college_id()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO faculty 
                (college_id, faculty_id, name, department_id, designation, email, phone, max_hours_per_day, max_hours_per_week, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, faculty_id_code.strip().upper(), name.strip(), department_id,
                  designation.strip(), email.strip(), phone.strip(),
                  max_hours_per_day, max_hours_per_week, is_active))
            new_id = cursor.lastrowid

            # Initialize full availability for all working days & teaching slots
            cursor.execute("SELECT day_name FROM working_days WHERE college_id = ? AND is_working = 1", (cid,))
            working_days = [r[0] for r in cursor.fetchall()]
            cursor.execute("SELECT slot_number FROM time_slots WHERE college_id = ? AND is_break = 0", (cid,))
            slots = [r[0] for r in cursor.fetchall()]

            for d in working_days:
                for s in slots:
                    cursor.execute("""
                        INSERT OR IGNORE INTO faculty_availability (college_id, faculty_id, day_name, slot_number, is_available)
                        VALUES (?, ?, ?, ?, 1)
                    """, (cid, new_id, d, s))

            conn.commit()
            return new_id

    def update_faculty(self, f_id: int, faculty_id_code: str, name: str, department_id: int,
                       designation: str, email: str = "", phone: str = "",
                       max_hours_per_day: int = 4, max_hours_per_week: int = 18, is_active: int = 1) -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE faculty 
                SET faculty_id = ?, name = ?, department_id = ?, designation = ?, email = ?,
                    phone = ?, max_hours_per_day = ?, max_hours_per_week = ?, is_active = ?
                WHERE id = ?
            """, (faculty_id_code.strip().upper(), name.strip(), department_id,
                  designation.strip(), email.strip(), phone.strip(),
                  max_hours_per_day, max_hours_per_week, is_active, f_id))
            conn.commit()
            return True

    def delete_faculty(self, f_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subjects WHERE default_faculty_id = ?", (f_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete faculty: Designated as primary faculty for curriculum subjects."

            conn.execute("DELETE FROM faculty WHERE id = ?", (f_id,))
            conn.commit()
            return True, "Faculty member removed successfully."

    # -------------------------------------------------------------
    # Faculty Availability Operations
    # -------------------------------------------------------------
    def get_faculty_availability(self, faculty_id: int) -> Dict[Tuple[str, int], bool]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT day_name, slot_number, is_available FROM faculty_availability WHERE faculty_id = ?",
                (faculty_id,)
            )
            return {(row["day_name"], row["slot_number"]): bool(row["is_available"]) for row in cursor.fetchall()}

    def set_faculty_slot_availability(self, faculty_id: int, day_name: str, slot_number: int, is_available: int, college_id: Optional[int] = None):
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO faculty_availability (college_id, faculty_id, day_name, slot_number, is_available)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(college_id, faculty_id, day_name, slot_number) DO UPDATE SET is_available = excluded.is_available
            """, (cid, faculty_id, day_name, slot_number, is_available))
            conn.commit()

    # -------------------------------------------------------------
    # Classroom Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_classrooms(self, room_type: Optional[str] = None, available_only: bool = False,
                       college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT c.*, d.name as department_name, d.code as department_code 
                FROM classrooms c
                LEFT JOIN departments d ON c.department_id = d.id
                WHERE 1=1
            """
            params = []
            if cid is not None:
                query += " AND c.college_id = ?"
                params.append(cid)
            if room_type:
                query += " AND c.room_type = ?"
                params.append(room_type)
            if available_only:
                query += " AND c.is_available = 1"
            query += " ORDER BY c.room_number ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_classroom(self, room_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM classrooms WHERE id = ?", (room_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_classroom(self, room_number: str, building_name: str, capacity: int, room_type: str,
                      department_id: Optional[int] = None, is_available: int = 1, college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else self.get_or_create_default_college_id()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO classrooms (college_id, room_number, building_name, capacity, room_type, department_id, is_available)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cid, room_number.strip().upper(), building_name.strip(), capacity, room_type, department_id, is_available))
            conn.commit()
            return cursor.lastrowid

    def update_classroom(self, room_id: int, room_number: str, building_name: str, capacity: int,
                         room_type: str, department_id: Optional[int] = None, is_available: int = 1) -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE classrooms 
                SET room_number = ?, building_name = ?, capacity = ?, room_type = ?, department_id = ?, is_available = ?
                WHERE id = ?
            """, (room_number.strip().upper(), building_name.strip(), capacity, room_type, department_id, is_available, room_id))
            conn.commit()
            return True

    def delete_classroom(self, room_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sections WHERE assigned_classroom_id = ?", (room_id,))
            if cursor.fetchone()[0] > 0:
                return False, "Cannot delete room: Assigned as base room to active student sections."

            conn.execute("DELETE FROM classrooms WHERE id = ?", (room_id,))
            conn.commit()
            return True, "Classroom removed successfully."

    # -------------------------------------------------------------
    # Subject Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_subjects(self, department_id: Optional[int] = None, semester: Optional[int] = None,
                     college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT s.*, 
                       d.name as department_name, d.code as department_code,
                       d.name as dept_name, d.code as dept_code,
                       f.name as faculty_name, f.faculty_id as faculty_code
                FROM subjects s
                JOIN departments d ON s.department_id = d.id
                LEFT JOIN faculty f ON s.default_faculty_id = f.id
                WHERE 1=1
            """
            params = []
            if cid is not None:
                query += " AND s.college_id = ?"
                params.append(cid)
            if department_id:
                query += " AND s.department_id = ?"
                params.append(department_id)
            if semester:
                query += " AND s.semester = ?"
                params.append(semester)
            query += " ORDER BY s.semester ASC, s.code ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_subject(self, sub_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.*, d.name as department_name, d.code as department_code,
                       f.name as faculty_name
                FROM subjects s
                JOIN departments d ON s.department_id = d.id
                LEFT JOIN faculty f ON s.default_faculty_id = f.id
                WHERE s.id = ?
            """, (sub_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_subject(self, code: str, name: str, department_id: int, semester: int,
                    subject_type: str, weekly_hours: int = 4, consecutive_periods: int = 1,
                    requires_lab: int = 0, default_faculty_id: Optional[int] = None,
                    college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else self.get_or_create_default_college_id()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO subjects 
                (college_id, code, name, department_id, semester, subject_type, weekly_hours, consecutive_periods, requires_lab, default_faculty_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, code.strip().upper(), name.strip(), department_id, semester,
                  subject_type, weekly_hours, consecutive_periods, requires_lab, default_faculty_id))
            sub_id = cursor.lastrowid

            if default_faculty_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO subject_faculty (college_id, subject_id, faculty_id, is_primary)
                    VALUES (?, ?, ?, 1)
                """, (cid, sub_id, default_faculty_id))

            conn.commit()
            return sub_id

    def update_subject(self, sub_id: int, code: str, name: str, department_id: int, semester: int,
                       subject_type: str, weekly_hours: int = 4, consecutive_periods: int = 1,
                       requires_lab: int = 0, default_faculty_id: Optional[int] = None) -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE subjects 
                SET code = ?, name = ?, department_id = ?, semester = ?, subject_type = ?,
                    weekly_hours = ?, consecutive_periods = ?, requires_lab = ?, default_faculty_id = ?
                WHERE id = ?
            """, (code.strip().upper(), name.strip(), department_id, semester,
                  subject_type, weekly_hours, consecutive_periods, requires_lab, default_faculty_id, sub_id))

            if default_faculty_id:
                cursor = conn.cursor()
                cursor.execute("SELECT college_id FROM subjects WHERE id = ?", (sub_id,))
                cid = cursor.fetchone()[0]
                conn.execute("""
                    INSERT INTO subject_faculty (college_id, subject_id, faculty_id, is_primary)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(college_id, subject_id, faculty_id) DO UPDATE SET is_primary = 1
                """, (cid, sub_id, default_faculty_id))

            conn.commit()
            return True

    def delete_subject(self, sub_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM subjects WHERE id = ?", (sub_id,))
            conn.commit()
            return True, "Subject deleted successfully."

    # -------------------------------------------------------------
    # Student Section Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_sections(self, department_id: Optional[int] = None, semester: Optional[int] = None,
                     college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT sec.*, 
                       d.code as dept_code, d.name as dept_name,
                       d.code as department_code, d.name as department_name,
                       c.room_number, c.building_name, c.capacity as room_capacity
                FROM sections sec
                JOIN departments d ON sec.department_id = d.id
                LEFT JOIN classrooms c ON sec.assigned_classroom_id = c.id
                WHERE 1=1
            """
            params = []
            if cid is not None:
                query += " AND sec.college_id = ?"
                params.append(cid)
            if department_id:
                query += " AND sec.department_id = ?"
                params.append(department_id)
            if semester:
                query += " AND sec.semester = ?"
                params.append(semester)
            query += " ORDER BY d.code ASC, sec.semester ASC, sec.section_name ASC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_section(self, sec_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT sec.*, d.name as department_name, d.code as department_code,
                       c.room_number, c.building_name, c.capacity as room_capacity
                FROM sections sec
                JOIN departments d ON sec.department_id = d.id
                LEFT JOIN classrooms c ON sec.assigned_classroom_id = c.id
                WHERE sec.id = ?
            """, (sec_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_section(self, department_id: int, academic_year: str, semester: int,
                    section_name: str, student_count: int = 60,
                    assigned_classroom_id: Optional[int] = None, college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else self.get_or_create_default_college_id()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sections 
                (college_id, department_id, academic_year, semester, section_name, student_count, assigned_classroom_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cid, department_id, academic_year.strip(), semester,
                  section_name.strip().upper(), student_count, assigned_classroom_id))
            conn.commit()
            return cursor.lastrowid

    def update_section(self, sec_id: int, department_id: int, academic_year: str, semester: int,
                       section_name: str, student_count: int = 60,
                       assigned_classroom_id: Optional[int] = None) -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE sections 
                SET department_id = ?, academic_year = ?, semester = ?, section_name = ?,
                    student_count = ?, assigned_classroom_id = ?
                WHERE id = ?
            """, (department_id, academic_year.strip(), semester,
                  section_name.strip().upper(), student_count, assigned_classroom_id, sec_id))
            conn.commit()
            return True

    def delete_section(self, sec_id: int) -> Tuple[bool, str]:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM sections WHERE id = ?", (sec_id,))
            conn.commit()
            return True, "Section deleted successfully."

    # -------------------------------------------------------------
    # Working Days & Time Slots Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_active_working_days(self, college_id: Optional[int] = None) -> List[str]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT day_name FROM working_days WHERE college_id = ? AND is_working = 1 ORDER BY display_order ASC",
                (cid,)
            )
            return [r[0] for r in cursor.fetchall()]

    def get_all_working_days(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM working_days WHERE college_id = ? ORDER BY display_order ASC", (cid,))
            return [dict(r) for r in cursor.fetchall()]

    def get_working_days(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Alias for get_all_working_days."""
        return self.get_all_working_days(college_id)

    def set_working_days(self, days_list: List[Tuple[str, int]], college_id: Optional[int] = None):
        """Update multiple working days is_working flags."""
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            for day_name, is_working in days_list:
                conn.execute(
                    "UPDATE working_days SET is_working = ? WHERE college_id = ? AND day_name = ?",
                    (is_working, cid, day_name)
                )
            conn.commit()

    def set_time_slots(self, slots: List[Tuple[int, str, str, str, int, str, int]], college_id: Optional[int] = None):
        """Replaces time slots for a college."""
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM time_slots WHERE college_id = ?", (cid,))
            for s in slots:
                conn.execute("""
                    INSERT INTO time_slots 
                    (college_id, slot_number, slot_name, start_time, end_time, is_break, break_type, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (cid, s[0], s[1], s[2], s[3], s[4], s[5], s[6]))
            conn.commit()

    def get_teaching_slots(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Alias for get_teaching_time_slots."""
        return self.get_teaching_time_slots(college_id)

    def get_subject_faculties(self, subject_id: int) -> List[Dict[str, Any]]:
        """Returns list of faculty assigned to this subject (from subject_faculty or default_faculty_id)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, sf.is_primary 
                FROM subject_faculty sf
                JOIN faculty f ON sf.faculty_id = f.id
                WHERE sf.subject_id = ?
            """, (subject_id,))
            rows = [dict(r) for r in cursor.fetchall()]
            if not rows:
                cursor.execute("""
                    SELECT f.*, 1 as is_primary
                    FROM subjects s
                    JOIN faculty f ON s.default_faculty_id = f.id
                    WHERE s.id = ?
                """, (subject_id,))
                rows = [dict(r) for r in cursor.fetchall()]
            return rows

    def set_faculty_availability(self, faculty_id: int, avail_map: Dict[Tuple[str, int], int], college_id: Optional[int] = None):
        """Sets bulk availability for a faculty member."""
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            for (day, slot), is_avail in avail_map.items():
                conn.execute("""
                    INSERT INTO faculty_availability (college_id, faculty_id, day_name, slot_number, is_available)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(college_id, faculty_id, day_name, slot_number) DO UPDATE SET is_available = excluded.is_available
                """, (cid, faculty_id, day, slot, is_avail))
            conn.commit()

    def create_timetable(self, name: str, academic_year: str, semester_type: str = "Even",
                         fitness: float = 0.0, notes: str = "", college_id: Optional[int] = None) -> int:
        """Alias for add_timetable."""
        return self.add_timetable(name, academic_year, semester_type, fitness, notes, college_id)

    def save_timetable_entries(self, timetable_id: int, entries: List[Dict[str, Any]], college_id: Optional[int] = None):
        """Bulk inserts scheduled entries for a timetable."""
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            for e in entries:
                conn.execute("""
                    INSERT INTO timetable_entries 
                    (college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cid, timetable_id, e["section_id"], e["day_name"], e["slot_number"],
                      e["subject_id"], e["faculty_id"], e["classroom_id"], e.get("is_locked", 0)))
            conn.commit()

    def set_working_day_status(self, day_name: str, is_working: int, college_id: Optional[int] = None):
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            conn.execute("UPDATE working_days SET is_working = ? WHERE college_id = ? AND day_name = ?",
                         (is_working, cid, day_name))
            conn.commit()

    def get_all_time_slots(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM time_slots WHERE college_id = ? ORDER BY slot_number ASC", (cid,))
            return [dict(r) for r in cursor.fetchall()]

    def get_teaching_time_slots(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM time_slots WHERE college_id = ? AND is_break = 0 ORDER BY slot_number ASC", (cid,))
            return [dict(r) for r in cursor.fetchall()]

    def update_time_slot(self, slot_id: int, slot_name: str, start_time: str, end_time: str,
                         is_break: int, break_type: str = "") -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE time_slots 
                SET slot_name = ?, start_time = ?, end_time = ?, is_break = ?, break_type = ?
                WHERE id = ?
            """, (slot_name.strip(), start_time.strip(), end_time.strip(), is_break, break_type.strip(), slot_id))
            conn.commit()
            return True

    # -------------------------------------------------------------
    # Timetables & Entries Operations (Tenant Scoped)
    # -------------------------------------------------------------
    def get_timetables(self, college_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cid is not None:
                cursor.execute("SELECT * FROM timetables WHERE college_id = ? ORDER BY created_at DESC", (cid,))
            else:
                cursor.execute("SELECT * FROM timetables ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_timetable(self, timetable_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM timetables WHERE id = ?", (timetable_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_active_timetable(self, college_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM timetables WHERE college_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1", (cid,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_timetable(self, name: str, academic_year: str, semester_type: str = "Even",
                      fitness: float = 0.0, notes: str = "", college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Mark previous timetables for this college as inactive
            cursor.execute("UPDATE timetables SET is_active = 0 WHERE college_id = ?", (cid,))
            cursor.execute("""
                INSERT INTO timetables (college_id, name, academic_year, semester_type, is_active, generation_fitness, notes)
                VALUES (?, ?, ?, ?, 1, ?, ?)
            """, (cid, name.strip(), academic_year.strip(), semester_type.strip(), fitness, notes.strip()))
            conn.commit()
            return cursor.lastrowid

    def set_active_timetable(self, timetable_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT college_id FROM timetables WHERE id = ?", (timetable_id,))
            row = cursor.fetchone()
            if not row:
                return False
            cid = row[0]
            cursor.execute("UPDATE timetables SET is_active = 0 WHERE college_id = ?", (cid,))
            cursor.execute("UPDATE timetables SET is_active = 1 WHERE id = ?", (timetable_id,))
            conn.commit()
            return True

    def delete_timetable(self, timetable_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM timetables WHERE id = ?", (timetable_id,))
            conn.commit()
            return True

    def add_timetable_entry(self, timetable_id: int, section_id: int, day_name: str,
                            slot_number: int, subject_id: int, faculty_id: int,
                            classroom_id: int, is_locked: int = 0, college_id: Optional[int] = None) -> int:
        cid = college_id if college_id is not None else (self.current_college_id or 1)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO timetable_entries 
                (college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cid, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked))
            conn.commit()
            return cursor.lastrowid

    def get_timetable_entries(self, timetable_id: int,
                              section_id: Optional[int] = None,
                              faculty_id: Optional[int] = None,
                              classroom_id: Optional[int] = None,
                              department_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch joined timetable entries with detailed labels for grid rendering."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT e.*, 
                       sec.section_name, sec.semester AS section_semester, sec.student_count,
                       d.code AS dept_code, d.name AS dept_name,
                       sub.code AS subject_code, sub.name AS subject_name, sub.subject_type, sub.requires_lab,
                       f.name AS faculty_name, f.faculty_id AS faculty_code,
                       c.room_number, c.building_name, c.room_type
                FROM timetable_entries e
                JOIN sections sec ON e.section_id = sec.id
                JOIN departments d ON sec.department_id = d.id
                JOIN subjects sub ON e.subject_id = sub.id
                JOIN faculty f ON e.faculty_id = f.id
                JOIN classrooms c ON e.classroom_id = c.id
                WHERE e.timetable_id = ?
            """
            params = [timetable_id]
            if section_id:
                sql += " AND e.section_id = ?"
                params.append(section_id)
            if faculty_id:
                sql += " AND e.faculty_id = ?"
                params.append(faculty_id)
            if classroom_id:
                sql += " AND e.classroom_id = ?"
                params.append(classroom_id)
            if department_id:
                sql += " AND sec.department_id = ?"
                params.append(department_id)

            sql += " ORDER BY e.day_name, e.slot_number"
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_timetable_entry(self, entry_id: int, subject_id: int, faculty_id: int, classroom_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE timetable_entries 
                SET subject_id = ?, faculty_id = ?, classroom_id = ?
                WHERE id = ?
            """, (subject_id, faculty_id, classroom_id, entry_id))
            conn.commit()
            return True

    def delete_timetable_entry(self, entry_id: int) -> bool:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM timetable_entries WHERE id = ?", (entry_id,))
            conn.commit()
            return True

    def insert_single_entry(self, timetable_id: int, section_id: int, day_name: str,
                            slot_number: int, subject_id: int, faculty_id: int, classroom_id: int) -> int:
        cid = self.current_college_id or 1
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO timetable_entries 
                (college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(college_id, timetable_id, section_id, day_name, slot_number) DO UPDATE SET
                    subject_id = excluded.subject_id,
                    faculty_id = excluded.faculty_id,
                    classroom_id = excluded.classroom_id,
                    is_locked = 1
            """, (cid, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id))
            conn.commit()
            return cursor.lastrowid

    # -------------------------------------------------------------
    # Dashboard Statistics (College Scoped)
    # -------------------------------------------------------------
    def get_dashboard_stats(self, college_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculates dashboard metrics for the active college."""
        cid = college_id if college_id is not None else self.current_college_id
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if cid is not None:
                cursor.execute("SELECT COUNT(*) FROM departments WHERE college_id = ?", (cid,))
                total_departments = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM faculty WHERE college_id = ? AND is_active = 1", (cid,))
                total_faculty = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM subjects WHERE college_id = ?", (cid,))
                total_subjects = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM classrooms WHERE college_id = ? AND is_available = 1", (cid,))
                total_classrooms = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM sections WHERE college_id = ?", (cid,))
                total_sections = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM timetables WHERE college_id = ?", (cid,))
                total_timetables = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT COUNT(*) FROM departments")
                total_departments = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM faculty WHERE is_active = 1")
                total_faculty = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM subjects")
                total_subjects = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM classrooms WHERE is_available = 1")
                total_classrooms = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM sections")
                total_sections = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM timetables")
                total_timetables = cursor.fetchone()[0]

            active_tt = self.get_active_timetable(cid)
            total_scheduled_entries = 0
            if active_tt:
                cursor.execute("SELECT COUNT(*) FROM timetable_entries WHERE timetable_id = ?", (active_tt["id"],))
                total_scheduled_entries = cursor.fetchone()[0]

            return {
                "total_departments": total_departments,
                "total_faculty": total_faculty,
                "total_subjects": total_subjects,
                "total_classrooms": total_classrooms,
                "total_sections": total_sections,
                "total_timetables": total_timetables,
                "active_timetable": active_tt,
                "total_scheduled_entries": total_scheduled_entries
            }
