"""
ClassPlanner - Database Backup and Restore Utilities
Supports full SQLite database backups, restores, and data resets.
"""

import os
import shutil
import sqlite3
import datetime
from classplanner.config import BACKUP_DIR, DEFAULT_DB_PATH
from classplanner.database.db_manager import DatabaseManager


def create_backup(custom_dest_path: str = None) -> str:
    """
    Creates a timestamped snapshot of the current SQLite database.
    Returns the file path of the backup.
    """
    db = DatabaseManager()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not custom_dest_path:
        dest_filename = f"classplanner_backup_{timestamp}.db"
        dest_path = os.path.join(BACKUP_DIR, dest_filename)
    else:
        dest_path = custom_dest_path

    # SQLite backup API produces consistent atomic snapshots
    src_conn = db.get_connection()
    dst_conn = sqlite3.connect(dest_path)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    return dest_path


def restore_backup(source_backup_path: str) -> bool:
    """
    Restores the application database from a backup file.
    """
    if not os.path.exists(source_backup_path):
        raise FileNotFoundError(f"Backup file not found: {source_backup_path}")

    # Validate that it is a valid SQLite database with expected tables
    test_conn = sqlite3.connect(source_backup_path)
    try:
        cur = test_conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='departments'")
        if not cur.fetchone():
            raise ValueError("The selected file is not a valid ClassPlanner database.")
    finally:
        test_conn.close()

    db = DatabaseManager()
    # Perform online restore
    target_conn = db.get_connection()
    src_conn = sqlite3.connect(source_backup_path)
    with target_conn:
        src_conn.backup(target_conn)
    src_conn.close()
    target_conn.close()

    # Re-initialize to verify
    db.init_database()
    return True


def reset_database(target_db: Optional[DatabaseManager] = None) -> bool:
    """
    Wipes existing database and re-initializes a fresh empty schema.
    """
    db = target_db or DatabaseManager()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DROP VIEW IF EXISTS timetable_slots;")
        # Drop all tables in reverse order of dependencies
        tables = [
            "timetable_entries", "timetables", "time_slots", "working_days",
            "sections", "subject_faculty", "subjects", "classrooms",
            "faculty_availability", "faculty", "semesters", "courses",
            "departments", "profiles", "app_settings", "colleges"
        ]
        for t in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {t}")
        try:
            cursor.execute("DELETE FROM sqlite_sequence;")
        except Exception:
            pass
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = ON;")

    db.init_database()
    return True

