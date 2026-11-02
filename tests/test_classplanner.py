"""
Comprehensive Test Suite for ClassPlanner Desktop Application
Tests database, CRUD, constraint solver, validator, PDF & Excel exporters, and UI instantiations.
"""

import os
import pytest
import tempfile
import sqlite3
from classplanner.database import DatabaseManager, load_sample_college_data, create_backup, restore_backup
from classplanner.solver import TimetableGenerator, ConflictValidator
from classplanner.exporters import PDFExporter, ExcelExporter
from classplanner.config import (
    SUBJECT_TYPE_THEORY, SUBJECT_TYPE_PRACTICAL,
    ROOM_TYPE_REGULAR, ROOM_TYPE_LAB
)


@pytest.fixture
def temp_db():
    """Provides a fresh isolated database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_path = tf.name

    db = DatabaseManager.reset_instance(temp_path)
    yield db

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
    DatabaseManager.reset_instance()


def test_database_initialization(temp_db):
    """Verifies all tables and default configurations are created."""
    stats = temp_db.get_dashboard_stats()
    assert stats["total_departments"] == 0
    assert stats["total_faculty"] == 0

    # Verify default slots are present
    slots = temp_db.get_all_time_slots()
    assert len(slots) >= 7

    # Verify working days
    days = temp_db.get_active_working_days()
    assert "Monday" in days
    assert "Friday" in days


def test_crud_operations(temp_db):
    """Tests CRUD for Department, Faculty, Classroom, Subject, and Section."""
    # 1. Department
    d_id = temp_db.add_department("CIVIL", "Civil Engineering", "Dr. K. Patel")
    assert d_id > 0
    dept = temp_db.get_department(d_id)
    assert dept["code"] == "CIVIL"

    temp_db.update_department(d_id, "CIVIL", "Civil & Structural Engg", "Dr. K. Patel")
    assert temp_db.get_department(d_id)["name"] == "Civil & Structural Engg"

    # 2. Faculty
    f_id = temp_db.add_faculty("FAC-CIV-01", "Dr. A. Verma", d_id, "Professor", "verma@civil.edu", "9998887770", 4, 16)
    assert f_id > 0
    fac = temp_db.get_faculty(f_id)
    assert fac["name"] == "Dr. A. Verma"

    # 3. Classroom
    r_id = temp_db.add_classroom("CE-101", "Civil Block", 60, ROOM_TYPE_REGULAR, d_id)
    assert r_id > 0
    room = temp_db.get_classroom(r_id)
    assert room["room_number"] == "CE-101"

    # 4. Subject
    s_id = temp_db.add_subject("CE301", "Surveying & Geomatics", d_id, 3, SUBJECT_TYPE_THEORY, 4, 1, 0, f_id)
    assert s_id > 0
    sub = temp_db.get_subject(s_id)
    assert sub["code"] == "CE301"

    # 5. Section
    sec_id = temp_db.add_section(d_id, "2026-2027", 3, "CIVIL-3A", 50, r_id)
    assert sec_id > 0
    sec = temp_db.get_section(sec_id)
    assert sec["section_name"] == "CIVIL-3A"


def test_sample_college_data_and_solver(temp_db):
    """Loads sample college dataset and verifies automated generation satisfies all hard constraints."""
    loaded, msg = load_sample_college_data(temp_db, force=True)
    assert loaded is True

    stats = temp_db.get_dashboard_stats()
    assert stats["total_departments"] == 3
    assert stats["total_faculty"] >= 10
    assert stats["total_subjects"] >= 15
    assert stats["total_classrooms"] >= 8
    assert stats["total_sections"] >= 4

    # Run Solver
    generator = TimetableGenerator(temp_db)
    result = generator.generate("Master Benchmark Timetable", "2026-2027", "Even", random_seed=42)

    assert result.success is True
    assert result.total_scheduled_periods == result.total_required_periods
    assert len(result.unscheduled_items) == 0

    # Verify no double-booking in database
    tt_id = result.timetable_id
    entries = temp_db.get_timetable_entries(tt_id)

    # 1. No Faculty double booking
    fac_slots = set()
    for e in entries:
        key = (e["faculty_id"], e["day_name"], e["slot_number"])
        assert key not in fac_slots, f"Faculty double booking detected: {key}"
        fac_slots.add(key)

    # 2. No Classroom double booking
    room_slots = set()
    for e in entries:
        key = (e["classroom_id"], e["day_name"], e["slot_number"])
        assert key not in room_slots, f"Classroom double booking detected: {key}"
        room_slots.add(key)

    # 3. No Section double booking
    sec_slots = set()
    for e in entries:
        key = (e["section_id"], e["day_name"], e["slot_number"])
        assert key not in sec_slots, f"Section double booking detected: {key}"
        sec_slots.add(key)

    # 4. No entry scheduled during break slots
    break_slots = {s["slot_number"] for s in temp_db.get_all_time_slots() if s["is_break"]}
    for e in entries:
        assert e["slot_number"] not in break_slots, f"Entry scheduled during break slot: {e['slot_number']}"


def test_conflict_validator(temp_db):
    """Tests ConflictValidator for blocking collisions and capacity issues."""
    load_sample_college_data(temp_db, force=True)
    gen = TimetableGenerator(temp_db)
    res = gen.generate("Test TT", "2026-2027", "Even", random_seed=123)

    all_entries = temp_db.get_timetable_entries(res.timetable_id)
    entry = all_entries[0]

    # Propose placing another section with same faculty at same day & slot
    other_section = next(s for s in temp_db.get_sections() if s["id"] != entry["section_id"])
    fac_info = temp_db.get_faculty(entry["faculty_id"])
    room_info = temp_db.get_classroom(entry["classroom_id"])
    sub_info = temp_db.get_subject(entry["subject_id"])
    fac_avail = temp_db.get_faculty_availability(entry["faculty_id"])

    is_valid, hard, warn = ConflictValidator.validate_assignment(
        timetable_id=res.timetable_id,
        section_id=other_section["id"],
        day_name=entry["day_name"],
        slot_number=entry["slot_number"],
        subject_id=entry["subject_id"],
        faculty_id=entry["faculty_id"],
        classroom_id=entry["classroom_id"],
        existing_entries=all_entries,
        section_info=other_section,
        faculty_info=fac_info,
        classroom_info=room_info,
        subject_info=sub_info,
        faculty_availability=fac_avail
    )

    # Must detect hard conflict for faculty double booking
    assert is_valid is False
    assert any("already teaching" in h for h in hard)


def test_backup_and_restore(temp_db):
    """Verifies SQLite atomic backup and restore."""
    load_sample_college_data(temp_db, force=True)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as bf:
        backup_path = bf.name

    try:
        saved_path = create_backup(backup_path)
        assert os.path.exists(saved_path)

        # Mutate current DB
        temp_db.add_department("MUTATED", "Mutated Department")
        assert any(d["code"] == "MUTATED" for d in temp_db.get_departments())

        # Restore from backup
        restore_backup(saved_path)
        # Verify MUTATED is gone
        assert not any(d["code"] == "MUTATED" for d in temp_db.get_departments())
    finally:
        if os.path.exists(backup_path):
            os.remove(backup_path)


def test_pdf_and_excel_exports(temp_db, tmp_path):
    """Verifies PDF and Excel export files are created and valid."""
    load_sample_college_data(temp_db, force=True)
    gen = TimetableGenerator(temp_db)
    res = gen.generate("Export Test TT", "2026-2027", "Even", random_seed=99)

    entries = temp_db.get_timetable_entries(res.timetable_id, section_id=1)
    days = temp_db.get_active_working_days()
    slots = temp_db.get_all_time_slots()
    grid_data = {(e["day_name"], e["slot_number"]): e for e in entries}

    pdf_out = str(tmp_path / "test_timetable.pdf")
    pdf_exporter = PDFExporter()
    pdf_exporter.export_timetable_grid(pdf_out, "CLASS TIMETABLE", "CSE-4A", days, slots, grid_data)
    assert os.path.exists(pdf_out)
    assert os.path.getsize(pdf_out) > 1000

    xlsx_out = str(tmp_path / "test_timetable.xlsx")
    excel_exporter = ExcelExporter()
    excel_exporter.export_timetable_grid(xlsx_out, "CLASS TIMETABLE", "CSE-4A", days, slots, grid_data)
    assert os.path.exists(xlsx_out)
    assert os.path.getsize(xlsx_out) > 1000


def test_supabase_url_encoding():
    """Verifies PostgreSQL URI generation, percent-encoding of @ symbol, and bracket stripping."""
    from classplanner.database.supabase_sync import SupabaseManager

    # Case 1: Standard password with @ symbol
    sm1 = SupabaseManager(password="Krishna@6301986030")
    uri1 = sm1.get_connection_string()
    assert "Krishna%406301986030" in uri1
    assert uri1 == "postgresql://postgres:Krishna%406301986030@db.lmllravkxpdqigkfprgx.supabase.co:5432/postgres"

    # Case 2: Bracketed password placeholder provided
    sm2 = SupabaseManager(password="[Krishna@6301986030]")
    uri2 = sm2.get_connection_string()
    assert "Krishna%406301986030" in uri2
    assert "[" not in uri2 and "]" not in uri2
    assert uri2 == "postgresql://postgres:Krishna%406301986030@db.lmllravkxpdqigkfprgx.supabase.co:5432/postgres"

