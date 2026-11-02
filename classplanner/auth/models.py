"""
ClassPlanner - Authentication & Multi-Tenant Session Models
Defines user roles, active user session, and permission helpers.
"""

from dataclasses import dataclass
from typing import Optional


class UserRole:
    """User role constants for Role-Based Access Control (RBAC)."""
    SUPER_ADMIN = "super_admin"
    COLLEGE_ADMIN = "college_admin"
    FACULTY = "faculty"

    ALL_ROLES = [SUPER_ADMIN, COLLEGE_ADMIN, FACULTY]

    @classmethod
    def display_name(cls, role: str) -> str:
        mapping = {
            cls.SUPER_ADMIN: "Super Administrator",
            cls.COLLEGE_ADMIN: "College Administrator",
            cls.FACULTY: "Faculty Member"
        }
        return mapping.get(role, role.title())


@dataclass
class Session:
    """Represents an authenticated user's active session state."""
    user_id: int
    email: str
    full_name: str
    role: str
    college_id: Optional[int] = None
    college_name: Optional[str] = None
    college_code: Optional[str] = None
    college_status: Optional[str] = "active"
    token: Optional[str] = None
    is_authenticated: bool = False

    def is_super_admin(self) -> bool:
        return self.is_authenticated and self.role == UserRole.SUPER_ADMIN

    def is_college_admin(self) -> bool:
        return self.is_authenticated and self.role == UserRole.COLLEGE_ADMIN

    def is_faculty(self) -> bool:
        return self.is_authenticated and self.role == UserRole.FACULTY

    def can_manage_college(self, college_id: Optional[int]) -> bool:
        if not self.is_authenticated:
            return False
        if self.is_super_admin():
            return True
        return self.college_id is not None and self.college_id == college_id

    def get_role_badge(self) -> str:
        return UserRole.display_name(self.role)

