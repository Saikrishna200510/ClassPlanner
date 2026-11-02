-- =====================================================================
-- ClassPlanner - Multi-Tenant Supabase PostgreSQL Database Architecture
-- Centralized Super Admin, College Admin accounts, and Row Level Security (RLS)
-- =====================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ---------------------------------------------------------------------
-- 1. Colleges Table (Central Multi-Tenant Registry)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.colleges (
    id SERIAL PRIMARY KEY,
    college_name TEXT NOT NULL,
    college_code TEXT UNIQUE NOT NULL,
    address TEXT,
    email TEXT,
    phone TEXT,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    logo_path TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 2. User Profiles Table (Supabase Authentication & Multi-Tenant RBAC)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id SERIAL PRIMARY KEY,
    auth_user_id UUID UNIQUE, -- References auth.users(id) when using Supabase GoTrue Auth
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('super_admin', 'college_admin', 'faculty')),
    college_id INTEGER REFERENCES public.colleges(id) ON DELETE CASCADE,
    phone TEXT,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 3. Academic Departments Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.departments (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    hod_name TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, code)
);

-- ---------------------------------------------------------------------
-- 4. Academic Courses / Programs Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.courses (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    course_code TEXT NOT NULL,
    course_name TEXT NOT NULL,
    department_id INTEGER REFERENCES public.departments(id) ON DELETE SET NULL,
    duration_years INTEGER DEFAULT 4,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, course_code)
);

-- ---------------------------------------------------------------------
-- 5. Semesters Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.semesters (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    semester_number INTEGER NOT NULL,
    academic_year TEXT NOT NULL,
    term_type TEXT NOT NULL DEFAULT 'Even' CHECK (term_type IN ('Odd', 'Even')),
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, academic_year, semester_number)
);

-- ---------------------------------------------------------------------
-- 6. Faculty Members Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.faculty (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    faculty_id TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES public.departments(id) ON DELETE RESTRICT,
    designation TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    max_hours_per_day INTEGER DEFAULT 4,
    max_hours_per_week INTEGER DEFAULT 18,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, faculty_id)
);

-- ---------------------------------------------------------------------
-- 7. Faculty Availability Matrix Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.faculty_availability (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES public.faculty(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    is_available INTEGER DEFAULT 1 CHECK (is_available IN (0, 1)),
    UNIQUE(college_id, faculty_id, day_name, slot_number)
);

-- ---------------------------------------------------------------------
-- 8. Classrooms & Laboratories Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.classrooms (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    room_number TEXT NOT NULL,
    building_name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    department_id INTEGER REFERENCES public.departments(id) ON DELETE SET NULL,
    is_available INTEGER DEFAULT 1 CHECK (is_available IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, room_number)
);

-- ---------------------------------------------------------------------
-- 9. Subjects Curriculum Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.subjects (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    department_id INTEGER NOT NULL REFERENCES public.departments(id) ON DELETE RESTRICT,
    semester INTEGER NOT NULL,
    subject_type TEXT NOT NULL,
    weekly_hours INTEGER NOT NULL DEFAULT 4,
    consecutive_periods INTEGER NOT NULL DEFAULT 1,
    requires_lab INTEGER NOT NULL DEFAULT 0 CHECK (requires_lab IN (0, 1)),
    default_faculty_id INTEGER REFERENCES public.faculty(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, code)
);

-- ---------------------------------------------------------------------
-- 10. Subject-Faculty Mapping Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.subject_faculty (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES public.faculty(id) ON DELETE CASCADE,
    is_primary INTEGER DEFAULT 1 CHECK (is_primary IN (0, 1)),
    UNIQUE(college_id, subject_id, faculty_id)
);

-- ---------------------------------------------------------------------
-- 11. Student Sections Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.sections (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES public.departments(id) ON DELETE RESTRICT,
    academic_year TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section_name TEXT NOT NULL,
    student_count INTEGER NOT NULL DEFAULT 60,
    assigned_classroom_id INTEGER REFERENCES public.classrooms(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, department_id, semester, section_name)
);

-- ---------------------------------------------------------------------
-- 12. Working Days Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.working_days (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    is_working INTEGER DEFAULT 1 CHECK (is_working IN (0, 1)),
    display_order INTEGER NOT NULL,
    UNIQUE(college_id, day_name)
);

-- ---------------------------------------------------------------------
-- 13. Time Slots Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.time_slots (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    slot_number INTEGER NOT NULL,
    slot_name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_break INTEGER DEFAULT 0 CHECK (is_break IN (0, 1)),
    break_type TEXT DEFAULT '',
    display_order INTEGER NOT NULL,
    UNIQUE(college_id, slot_number)
);

-- ---------------------------------------------------------------------
-- 14. Master Timetables Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.timetables (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    academic_year TEXT NOT NULL,
    semester_type TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK (is_active IN (0, 1)),
    generation_fitness REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- 15. Timetable Entries Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.timetable_entries (
    id SERIAL PRIMARY KEY,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    timetable_id INTEGER NOT NULL REFERENCES public.timetables(id) ON DELETE CASCADE,
    section_id INTEGER NOT NULL REFERENCES public.sections(id) ON DELETE CASCADE,
    day_name TEXT NOT NULL,
    slot_number INTEGER NOT NULL,
    subject_id INTEGER NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    faculty_id INTEGER NOT NULL REFERENCES public.faculty(id) ON DELETE CASCADE,
    classroom_id INTEGER NOT NULL REFERENCES public.classrooms(id) ON DELETE CASCADE,
    is_locked INTEGER DEFAULT 0 CHECK (is_locked IN (0, 1)),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(college_id, timetable_id, section_id, day_name, slot_number)
);

-- ---------------------------------------------------------------------
-- 16. Timetable Slots View (Multi-Tenant Alias)
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW public.timetable_slots AS 
SELECT id, college_id, timetable_id, section_id, day_name, slot_number, subject_id, faculty_id, classroom_id, is_locked, created_at 
FROM public.timetable_entries;

-- ---------------------------------------------------------------------
-- 17. Application & College Settings Table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.app_settings (
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    college_id INTEGER NOT NULL REFERENCES public.colleges(id) ON DELETE CASCADE,
    PRIMARY KEY(key, college_id)
);

-- =====================================================================
-- ROW LEVEL SECURITY (RLS) HELPER FUNCTIONS & PROCEDURES
-- =====================================================================

-- Helper: Retrieve current user's role from JWT or profiles table
CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS TEXT AS $$
DECLARE
    user_role TEXT;
BEGIN
    -- Check custom claims or session setting first
    user_role := NULLIF(current_setting('app.current_user_role', true), '');
    IF user_role IS NOT NULL THEN
        RETURN user_role;
    END IF;

    -- Lookup from profiles using auth.uid() or jwt email
    SELECT role INTO user_role 
    FROM public.profiles 
    WHERE (auth_user_id IS NOT NULL AND auth_user_id = auth.uid())
       OR (email = auth.jwt() ->> 'email')
    LIMIT 1;

    RETURN COALESCE(user_role, 'anonymous');
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Helper: Retrieve current user's college_id
CREATE OR REPLACE FUNCTION public.get_current_user_college_id()
RETURNS INTEGER AS $$
DECLARE
    cid INTEGER;
BEGIN
    cid := NULLIF(current_setting('app.current_college_id', true), '')::INTEGER;
    IF cid IS NOT NULL THEN
        RETURN cid;
    END IF;

    SELECT college_id INTO cid 
    FROM public.profiles 
    WHERE (auth_user_id IS NOT NULL AND auth_user_id = auth.uid())
       OR (email = auth.jwt() ->> 'email')
    LIMIT 1;

    RETURN cid;
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- Helper: Check if current user is Super Administrator
CREATE OR REPLACE FUNCTION public.is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    RETURN (public.get_current_user_role() = 'super_admin');
END;
$$ LANGUAGE plpgsql STABLE SECURITY DEFINER;

-- =====================================================================
-- ENABLE ROW LEVEL SECURITY (RLS) ACROSS ALL TABLES
-- =====================================================================

ALTER TABLE public.colleges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.semesters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.faculty_availability ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.classrooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subject_faculty ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.working_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.time_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timetables ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.timetable_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.app_settings ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- ROW LEVEL SECURITY POLICIES
-- =====================================================================

-- 1. Colleges Policies
DROP POLICY IF EXISTS super_admin_colleges_all ON public.colleges;
CREATE POLICY super_admin_colleges_all ON public.colleges
    FOR ALL USING (public.is_super_admin());

DROP POLICY IF EXISTS college_admin_view_own ON public.colleges;
CREATE POLICY college_admin_view_own ON public.colleges
    FOR SELECT USING (id = public.get_current_user_college_id());

DROP POLICY IF EXISTS college_admin_update_own ON public.colleges;
CREATE POLICY college_admin_update_own ON public.colleges
    FOR UPDATE USING (id = public.get_current_user_college_id() AND public.get_current_user_role() = 'college_admin');

-- 2. Profiles Policies
DROP POLICY IF EXISTS super_admin_profiles_all ON public.profiles;
CREATE POLICY super_admin_profiles_all ON public.profiles
    FOR ALL USING (public.is_super_admin());

DROP POLICY IF EXISTS college_admin_manage_users ON public.profiles;
CREATE POLICY college_admin_manage_users ON public.profiles
    FOR ALL USING (
        college_id = public.get_current_user_college_id() 
        AND public.get_current_user_role() = 'college_admin'
        AND role IN ('college_admin', 'faculty')
    );

DROP POLICY IF EXISTS user_read_own_profile ON public.profiles;
CREATE POLICY user_read_own_profile ON public.profiles
    FOR SELECT USING (
        (auth_user_id IS NOT NULL AND auth_user_id = auth.uid())
        OR (email = auth.jwt() ->> 'email')
    );

-- 3. Dynamic Multi-Tenant Policies for all College-related tables
DO $$
DECLARE
    tbl_name TEXT;
    tenant_tables TEXT[] := ARRAY[
        'departments', 'courses', 'semesters', 'faculty', 
        'faculty_availability', 'classrooms', 'subjects', 
        'subject_faculty', 'sections', 'working_days', 
        'time_slots', 'timetables', 'timetable_entries', 'app_settings'
    ];
BEGIN
    FOREACH tbl_name IN ARRAY tenant_tables LOOP
        -- Super Admin Full Access Policy
        EXECUTE format('DROP POLICY IF EXISTS super_admin_manage_%I ON public.%I', tbl_name, tbl_name);
        EXECUTE format(
            'CREATE POLICY super_admin_manage_%I ON public.%I FOR ALL USING (public.is_super_admin()) WITH CHECK (public.is_super_admin())',
            tbl_name, tbl_name
        );

        -- College Admin Full Access to Own College Policy
        EXECUTE format('DROP POLICY IF EXISTS college_admin_manage_%I ON public.%I', tbl_name, tbl_name);
        EXECUTE format(
            'CREATE POLICY college_admin_manage_%I ON public.%I FOR ALL ' ||
            'USING (college_id = public.get_current_user_college_id() AND public.get_current_user_role() IN (''super_admin'', ''college_admin'')) ' ||
            'WITH CHECK (college_id = public.get_current_user_college_id() AND public.get_current_user_role() IN (''super_admin'', ''college_admin''))',
            tbl_name, tbl_name
        );

        -- Faculty Read-Only Policy
        EXECUTE format('DROP POLICY IF EXISTS faculty_view_%I ON public.%I', tbl_name, tbl_name);
        EXECUTE format(
            'CREATE POLICY faculty_view_%I ON public.%I FOR SELECT ' ||
            'USING (college_id = public.get_current_user_college_id())',
            tbl_name, tbl_name
        );
    END LOOP;
END $$;

-- =====================================================================
-- SEED INITIAL MULTI-TENANT ACCOUNTS & COLLEGES
-- =====================================================================

-- 1. Initial Colleges
INSERT INTO public.colleges (id, college_name, college_code, address, email, phone, status)
VALUES 
    (1, 'Government Engineering College', 'GEC-01', 'University Road, North Campus', 'contact@gec.edu', '+91 98765 43210', 'active'),
    (2, 'National Institute of Technology', 'NIT-02', 'Tech Park Boulevard, South Zone', 'admin@nit.edu', '+91 98765 88990', 'active')
ON CONFLICT (college_code) DO NOTHING;

-- Reset sequence for colleges
SELECT setval(pg_get_serial_sequence('public.colleges', 'id'), COALESCE(MAX(id), 1)) FROM public.colleges;

-- 2. Initial Accounts
-- Passwords:
-- superadmin@classplanner.edu -> Admin@12345 (SHA256: 7110eda4d09e062aa5e4a390b0a572ac0d2c0220ac52749179cbf5cf284e3d31)
-- admin@gec.edu               -> College@12345 (SHA256: 82cf300bfa3693e4d9c79fa2d64a069e2c6615b8045e0fb143c651e7041f92e7)
-- admin@nit.edu               -> Nit@12345 (SHA256: 3c5740b79d2b8b99d5069a194916a4b1fc7e4b52cb5239a032ecf5cb2342ab81)
INSERT INTO public.profiles (full_name, email, password_hash, role, college_id, phone, is_active)
VALUES 
    ('ClassPlanner Super Administrator', 'superadmin@classplanner.edu', '7110eda4d09e062aa5e4a390b0a572ac0d2c0220ac52749179cbf5cf284e3d31', 'super_admin', NULL, '+91 90000 00001', 1),
    ('GEC College Administrator', 'admin@gec.edu', '82cf300bfa3693e4d9c79fa2d64a069e2c6615b8045e0fb143c651e7041f92e7', 'college_admin', 1, '+91 98765 43211', 1),
    ('NIT College Administrator', 'admin@nit.edu', '3c5740b79d2b8b99d5069a194916a4b1fc7e4b52cb5239a032ecf5cb2342ab81', 'college_admin', 2, '+91 98765 88991', 1)
ON CONFLICT (email) DO NOTHING;

