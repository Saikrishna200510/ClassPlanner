"""
ClassPlanner - Authentication Service
Handles credential verification, role-based session initialization,
college identification, and password management.
"""

import hashlib
import secrets
from typing import Tuple, Optional
from classplanner.auth.models import Session, UserRole
from classplanner.database.db_manager import DatabaseManager


def hash_password(password: str) -> str:
    """Computes standard SHA-256 hash of password string."""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


class AuthService:
    """Authentication and session lifecycle manager."""
    _current_session: Optional[Session] = None

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or DatabaseManager()

    @classmethod
    def get_current_session(cls) -> Optional[Session]:
        return cls._current_session

    @classmethod
    def set_current_session(cls, session: Optional[Session]):
        cls._current_session = session

    @classmethod
    def logout(cls):
        """Clears active session and resets DB tenant context."""
        cls._current_session = None
        db = DatabaseManager()
        db.current_college_id = None

    def login(
        self,
        email: str,
        password: str,
        expected_role: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Session]]:
        """
        Authenticates user with email and password.
        Identifies role, validates status, and resolves tenant college.
        """
        email = email.strip().lower()
        password = password.strip()

        if not email or not password:
            return False, "Email and password are required.", None

        profile = self.db.get_profile_by_email(email)
        if not profile:
            return False, "Invalid email address or user not found.", None

        # Verify password hash
        provided_hash = hash_password(password)
        if profile["password_hash"] != provided_hash:
            return False, "Incorrect password. Please verify and try again.", None

        # Check user active status
        if profile.get("is_active", 1) == 0:
            return False, "Your account has been deactivated. Please contact the administrator.", None

        user_role = profile["role"]

        # If a specific login portal was used, verify role matches
        if expected_role and user_role != expected_role:
            if expected_role == UserRole.SUPER_ADMIN:
                return False, "Access denied: This account is not a Super Administrator.", None
            elif expected_role == UserRole.COLLEGE_ADMIN and user_role not in [UserRole.COLLEGE_ADMIN, UserRole.FACULTY]:
                return False, "Please use the Super Admin login portal.", None

        # Resolve College Details
        college_id = profile["college_id"]
        college_name = None
        college_code = None
        college_status = "active"

        if college_id:
            college = self.db.get_college(college_id)
            if college:
                college_name = college["college_name"]
                college_code = college["college_code"]
                college_status = college.get("status", "active")

                # If college is inactive, deny access to college admins & faculty
                if college_status == "inactive" and user_role != UserRole.SUPER_ADMIN:
                    return False, f"Account access suspended: {college_name} is marked as inactive by the Super Administrator.", None
            else:
                if user_role != UserRole.SUPER_ADMIN:
                    return False, "Associated college record not found.", None

        # Build authenticated session
        session = Session(
            user_id=profile["id"],
            email=profile["email"],
            full_name=profile["full_name"],
            role=user_role,
            college_id=college_id,
            college_name=college_name,
            college_code=college_code,
            college_status=college_status,
            token=secrets.token_hex(16),
            is_authenticated=True
        )

        AuthService.set_current_session(session)

        # Configure DatabaseManager's tenant scope
        if user_role == UserRole.SUPER_ADMIN:
            # Super Admin can switch colleges, default to None or first college
            self.db.current_college_id = None
        else:
            self.db.current_college_id = college_id

        return True, "Login successful.", session

    def change_password(self, user_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Allows an authenticated user to change their own password."""
        profile = self.db.get_profile(user_id)
        if not profile:
            return False, "User not found."

        if profile["password_hash"] != hash_password(old_password):
            return False, "Current password does not match."

        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        self.db.update_user_password(user_id, hash_password(new_password))
        return True, "Password updated successfully."

    def reset_password_by_admin(self, user_id: int, new_password: str) -> Tuple[bool, str]:
        """Allows an administrator to reset a user's password."""
        if len(new_password) < 6:
            return False, "New password must be at least 6 characters long."

        self.db.update_user_password(user_id, hash_password(new_password))
        return True, "Password reset successfully."

    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """Initiates password reset process for an email."""
        email = email.strip().lower()
        profile = self.db.get_profile_by_email(email)
        if not profile:
            # Return generic message to avoid email enumeration
            return True, "If this email is registered, password reset instructions have been dispatched."

        # In production Supabase, trigger supabase.auth.reset_password_for_email
        # Here we generate an audit log / temporary token
        reset_token = secrets.token_urlsafe(8)
        return True, f"Password reset instructions and verification code ({reset_token}) have been logged for {email}."

