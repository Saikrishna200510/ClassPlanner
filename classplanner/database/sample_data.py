"""
ClassPlanner - Sample College Dataset Generator
Creates a realistic, complete engineering college dataset for immediate testing.
"""

from classplanner.database.db_manager import DatabaseManager
from classplanner.config import (
    ROOM_TYPE_REGULAR, ROOM_TYPE_LAB,
    SUBJECT_TYPE_THEORY, SUBJECT_TYPE_PRACTICAL
)


def load_sample_college_data(db: DatabaseManager, force: bool = False):
    """
    Populates sample departments, faculty members, subjects, classrooms,
    and sections into the database.
    """
    if force:
        from classplanner.database.backup import reset_database
        reset_database(target_db=db)
        db.set_active_college(1)
    else:
        stats = db.get_dashboard_stats()
        if stats["total_departments"] > 0:
            return False, "Database already contains existing college records."

    # 1. Departments
    dept_cse_id = db.add_department("CSE", "Computer Science & Engineering", "Dr. Arvind Sharma")
    dept_ece_id = db.add_department("ECE", "Electronics & Communication Engg.", "Dr. Meenakshi Sundaram")
    dept_mech_id = db.add_department("MECH", "Mechanical Engineering", "Dr. Rajeshwar Rao")

    # 2. Faculty
    # CSE Faculty
    f_sharma = db.add_faculty("FAC-CSE-01", "Dr. Arvind Sharma", dept_cse_id, "Professor & HOD", "arvind.sharma@college.edu", "9876543210", 4, 16)
    f_priya = db.add_faculty("FAC-CSE-02", "Dr. Priya Nair", dept_cse_id, "Associate Professor", "priya.nair@college.edu", "9876543211", 4, 18)
    f_vikram = db.add_faculty("FAC-CSE-03", "Dr. Vikram Roy", dept_cse_id, "Assistant Professor", "vikram.roy@college.edu", "9876543212", 4, 18)
    f_sneha = db.add_faculty("FAC-CSE-04", "Prof. Sneha Patel", dept_cse_id, "Assistant Professor", "sneha.patel@college.edu", "9876543213", 4, 18)
    f_verma = db.add_faculty("FAC-CSE-05", "Er. Rahul Verma", dept_cse_id, "Lecturer", "rahul.verma@college.edu", "9876543214", 4, 18)

    # ECE Faculty
    f_meenakshi = db.add_faculty("FAC-ECE-01", "Dr. Meenakshi Sundaram", dept_ece_id, "Professor & HOD", "meenakshi.s@college.edu", "9876543220", 4, 16)
    f_ananya = db.add_faculty("FAC-ECE-02", "Dr. Ananya Iyer", dept_ece_id, "Associate Professor", "ananya.iyer@college.edu", "9876543221", 4, 18)
    f_raman = db.add_faculty("FAC-ECE-03", "Prof. K. Ramanathan", dept_ece_id, "Assistant Professor", "ramanathan@college.edu", "9876543222", 4, 18)
    f_sunita = db.add_faculty("FAC-ECE-04", "Er. Sunita Deshmukh", dept_ece_id, "Assistant Professor", "sunita.d@college.edu", "9876543223", 4, 18)

    # MECH Faculty
    f_rao = db.add_faculty("FAC-MECH-01", "Dr. Rajeshwar Rao", dept_mech_id, "Professor & HOD", "rajeshwar.rao@college.edu", "9876543230", 4, 16)
    f_sanjay = db.add_faculty("FAC-MECH-02", "Dr. Sanjay Kulkarni", dept_mech_id, "Associate Professor", "sanjay.k@college.edu", "9876543231", 4, 18)
    f_amit = db.add_faculty("FAC-MECH-03", "Prof. Amit Bhatt", dept_mech_id, "Assistant Professor", "amit.bhatt@college.edu", "9876543232", 4, 18)

    # 3. Classrooms
    # Regular Lecture Halls
    r_lh101 = db.add_classroom("LH-101", "Main Academic Block (Floor 1)", 70, ROOM_TYPE_REGULAR, dept_cse_id)
    r_lh102 = db.add_classroom("LH-102", "Main Academic Block (Floor 1)", 70, ROOM_TYPE_REGULAR, dept_cse_id)
    r_lh201 = db.add_classroom("LH-201", "Technology Wing (Floor 2)", 65, ROOM_TYPE_REGULAR, dept_ece_id)
    r_lh301 = db.add_classroom("LH-301", "Mechanical Block (Floor 3)", 65, ROOM_TYPE_REGULAR, dept_mech_id)

    # Specialized Labs
    r_cslab1 = db.add_classroom("CS-LAB-1", "Computing Center (Ground Floor)", 45, ROOM_TYPE_LAB, dept_cse_id)
    r_cslab2 = db.add_classroom("CS-LAB-2", "Computing Center (Floor 1)", 45, ROOM_TYPE_LAB, dept_cse_id)
    r_eclab1 = db.add_classroom("EC-LAB-1", "Technology Wing (Floor 1)", 40, ROOM_TYPE_LAB, dept_ece_id)
    r_melab1 = db.add_classroom("ME-LAB-1", "Central Mechanical Workshop", 45, ROOM_TYPE_LAB, dept_mech_id)

    # 4. Student Sections (Semester 4)
    sec_cse_a = db.add_section(dept_cse_id, "2026-2027", 4, "CSE-4A", 60, r_lh101)
    sec_cse_b = db.add_section(dept_cse_id, "2026-2027", 4, "CSE-4B", 60, r_lh102)
    sec_ece_a = db.add_section(dept_ece_id, "2026-2027", 4, "ECE-4A", 55, r_lh201)
    sec_mech_a = db.add_section(dept_mech_id, "2026-2027", 4, "MECH-4A", 50, r_lh301)

    # 5. Subjects & Faculty Assignments
    # CSE Subjects
    db.add_subject("CS401", "Database Management Systems", dept_cse_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_sharma)
    db.add_subject("CS402", "Operating Systems", dept_cse_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_priya)
    db.add_subject("CS403", "Design & Analysis of Algorithms", dept_cse_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_vikram)
    db.add_subject("CS404", "Computer Networks", dept_cse_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_sneha)
    db.add_subject("CS405", "Software Engineering", dept_cse_id, 4, SUBJECT_TYPE_THEORY, 3, 1, 0, f_verma)
    # Practical Labs (3-period block consecutive, requiring lab)
    db.add_subject("CS491", "DBMS & SQL Laboratory", dept_cse_id, 4, SUBJECT_TYPE_PRACTICAL, 3, 3, 1, f_sharma)
    db.add_subject("CS492", "Algorithms & OS Laboratory", dept_cse_id, 4, SUBJECT_TYPE_PRACTICAL, 3, 3, 1, f_priya)

    # ECE Subjects
    db.add_subject("EC401", "Signals and Systems", dept_ece_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_meenakshi)
    db.add_subject("EC402", "Analog Integrated Circuits", dept_ece_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_ananya)
    db.add_subject("EC403", "Electromagnetic Fields", dept_ece_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_raman)
    db.add_subject("EC404", "Digital Communication", dept_ece_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_sunita)
    db.add_subject("EC491", "Analog Circuits Laboratory", dept_ece_id, 4, SUBJECT_TYPE_PRACTICAL, 3, 3, 1, f_ananya)

    # MECH Subjects
    db.add_subject("ME401", "Applied Thermodynamics", dept_mech_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_rao)
    db.add_subject("ME402", "Fluid Mechanics & Machinery", dept_mech_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_sanjay)
    db.add_subject("ME403", "Mechanics of Materials", dept_mech_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_amit)
    db.add_subject("ME404", "Manufacturing Technology", dept_mech_id, 4, SUBJECT_TYPE_THEORY, 4, 1, 0, f_rao)
    db.add_subject("ME491", "CAD / CAM Laboratory", dept_mech_id, 4, SUBJECT_TYPE_PRACTICAL, 3, 3, 1, f_sanjay)

    return True, "Sample college dataset loaded successfully."
