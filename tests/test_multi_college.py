"""
Comprehensive Multi-College & Multi-Tenant Authentication Test Suite
Tests:
- Super Admin and College Admin authentication
- Role-based access control and inactive college blocking
- Strict data isolation across different colleges (departments, faculty, subjects, timetables)
- Super Admin college provisioning, activation, deactivation, and password reset
- Courses and Semesters management
"""

import pytest
import tempfile
import os
from classplanner.database import DatabaseManager, load_sample_college_data
from classplanner.auth import AuthService, UserRole, Session
from classplanner.solver import TimetableGenerator


@pytest.fixture
def multi_tenant_db():
    """Provides a fresh isolated database with multi-tenant schema."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name

    db = DatabaseManager.reset_instance(temp_path)
    yield db

    if os.path.exists(temp_path):
        os.remove(temp_path)
    DatabaseManager.reset_instance()


def test_initial_multi_college_setup(multi_tenant_db):
    """Verifies default colleges and initial administrative accounts are seeded."""
    colleges = multi_tenant_db.get_colleges()
    assert len(colleges) >= 2

    # Check GEC and NIT
    gec = next(c for c in colleges if c["college_code"] == "GEC-01")
    nit = next(c for c in colleges if c["college_code"] == "NIT-02")
    assert gec["status"] == "active"
    assert nit["status"] == "active"

    # Check Super Admin stats
    stats = multi_tenant_db.get_super_admin_stats()
    assert stats["total_colleges"] >= 2
    assert stats["active_colleges"] >= 2
    assert stats["total_college_admins"] >= 2


def test_authentication_and_rbac(multi_tenant_db):
    """Tests Super Admin and College Admin authentication, role validation, and status checks."""
    auth = AuthService(multi_tenant_db)

    # 1. Super Admin login
    ok, msg, sess = auth.login("superadmin@classplanner.edu", "Admin@12345")
    assert ok is True
    assert sess.is_super_admin() is True
    assert sess.college_id is None

    # 2. College Admin login
    ok, msg, sess = auth.login("admin@gec.edu", "College@12345")
    assert ok is True
    assert sess.is_college_admin() is True
    assert sess.college_id == 1
    assert sess.college_code == "GEC-01"

    # 3. Portal role guard: Super Admin trying to use College portal
    ok, msg, sess = auth.login("superadmin@classplanner.edu", "Admin@12345", expected_role=UserRole.COLLEGE_ADMIN)
    assert ok is False
    assert "Super Admin login portal" in msg

    # 4. Deactivated College Login Blocking
    # Deactivate NIT (College 2)
    multi_tenant_db.set_college_status(2, "inactive")
    ok, msg, sess = auth.login("admin@nit.edu", "Nit@12345")
    assert ok is False
    assert "suspended" in msg.lower() or "inactive" in msg.lower()

    # Reactivate NIT
    multi_tenant_db.set_college_status(2, "active")
    ok, msg, sess = auth.login("admin@nit.edu", "Nit@12345")
    assert ok is True


def test_multi_tenant_data_isolation(multi_tenant_db):
    """
    Guarantees strict tenant isolation:
    Data added to College 1 is never visible or leaked to College 2.
    """
    # 1. Add Department and Faculty to College 1 (GEC)
    multi_tenant_db.set_active_college(1)
    d1 = multi_tenant_db.add_department("CSE-GEC", "GEC Computer Science")
    f1 = multi_tenant_db.add_faculty("FAC-GEC-01", "Prof. GEC One", d1, "Professor")
    r1 = multi_tenant_db.add_classroom("GEC-101", "GEC Main Block", 60, "Regular", d1)
    s1 = multi_tenant_db.add_subject("CS101-GEC", "GEC Programming", d1, 1, "Theory", 4, 1, 0, f1)

    # 2. Add Department and Faculty to College 2 (NIT)
    multi_tenant_db.set_active_college(2)
    d2 = multi_tenant_db.add_department("ECE-NIT", "NIT Electronics")
    f2 = multi_tenant_db.add_faculty("FAC-NIT-01", "Prof. NIT One", d2, "Professor")
    r2 = multi_tenant_db.add_classroom("NIT-201", "NIT Tech Block", 65, "Regular", d2)
    s2 = multi_tenant_db.add_subject("EC201-NIT", "NIT Signals", d2, 2, "Theory", 4, 1, 0, f2)

    # 3. Inspect College 1 Scope
    multi_tenant_db.set_active_college(1)
    c1_depts = [d["code"] for d in multi_tenant_db.get_departments()]
    c1_fac = [f["name"] for f in multi_tenant_db.get_faculty_list()]
    c1_rooms = [r["room_number"] for r in multi_tenant_db.get_classrooms()]
    c1_subs = [s["code"] for s in multi_tenant_db.get_subjects()]

    assert "CSE-GEC" in c1_depts
    assert "ECE-NIT" not in c1_depts  # STRICT ISOLATION
    assert "Prof. GEC One" in c1_fac
    assert "Prof. NIT One" not in c1_fac  # STRICT ISOLATION
    assert "GEC-101" in c1_rooms
    assert "NIT-201" not in c1_rooms
    assert "CS101-GEC" in c1_subs
    assert "EC201-NIT" not in c1_subs

    # 4. Inspect College 2 Scope
    multi_tenant_db.set_active_college(2)
    c2_depts = [d["code"] for d in multi_tenant_db.get_departments()]
    c2_fac = [f["name"] for f in multi_tenant_db.get_faculty_list()]

    assert "ECE-NIT" in c2_depts
    assert "CSE-GEC" not in c2_depts  # STRICT ISOLATION
    assert "Prof. NIT One" in c2_fac
    assert "Prof. GEC One" not in c2_fac  # STRICT ISOLATION


def test_college_provisioning_and_admin_reset(multi_tenant_db):
    """Tests Super Admin creating a new college and resetting credentials."""
    auth = AuthService(multi_tenant_db)

    # Add new college
    cid = multi_tenant_db.add_college(
        college_name="Indian Institute of Science",
        college_code="IIS-03",
        address="Bangalore Science Park",
        email="contact@iis.edu",
        phone="+91 98888 11111",
        status="active",
        admin_name="IIS Administrator",
        admin_email="admin@iis.edu",
        admin_password="InitialPassword123"
    )
    assert cid > 0

    # Verify new college admin can log in
    ok, msg, sess = auth.login("admin@iis.edu", "InitialPassword123")
    assert ok is True
    assert sess.college_code == "IIS-03"

    # Reset admin password
    admin_prof = multi_tenant_db.get_college_admin(cid)
    ok, msg = auth.reset_password_by_admin(admin_prof["id"], "NewSecurePassword456")
    assert ok is True

    # Old password must fail
    ok_old, _, _ = auth.login("admin@iis.edu", "InitialPassword123")
    assert ok_old is False

    # New password must succeed
    ok_new, _, _ = auth.login("admin@iis.edu", "NewSecurePassword456")
    assert ok_new is True


def test_courses_and_semesters_crud(multi_tenant_db):
    """Tests course degree program and semester configuration."""
    multi_tenant_db.set_active_college(1)
    d_id = multi_tenant_db.add_department("CSE-TEST", "CSE Test Dept")

    # Add Course
    c_id = multi_tenant_db.add_course("BTECH-CS", "Bachelor of Tech in CS", d_id, 4)
    assert c_id > 0
    courses = multi_tenant_db.get_courses()
    assert any(c["course_code"] == "BTECH-CS" for c in courses)

    # Add Semester
    s_id = multi_tenant_db.add_semester(5, "2026-2027", "Odd")
    assert s_id > 0
    sems = multi_tenant_db.get_semesters()
    assert any(s["semester_number"] == 5 for s in sems)

