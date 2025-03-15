"""
User domain model for the GPT Wrapper Boilerplate.

This module defines the User domain model and related enums that represent
user information and roles in the system.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Dict, Optional, Any


class UserRole(Enum):
    """
    Enumeration of possible user roles in the system.
    """

    ADMIN = "admin"
    USER = "user"
    API_CLIENT = "api_client"


class UserStatus(Enum):
    """
    Enumeration of possible user statuses.
    """

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


@dataclass
class User:
    """
    Domain model representing a user in the system.

    This class encapsulates user data including authentication
    and authorization information.
    """

    id: str
    """Unique identifier for the user."""

    username: str
    """Username used for authentication."""

    email: str
    """User's email address."""

    role: UserRole
    """User's role in the system."""

    status: UserStatus = UserStatus.ACTIVE
    """Current status of the user account."""

    created_at: datetime = None
    """When the user was created."""

    last_login: Optional[datetime] = None
    """When the user last logged in."""

    metadata: Dict[str, Any] = None
    """Additional user metadata."""

    def __post_init__(self):
        """
        Initialize default values after dataclass initialization.
        """
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    @property
    def is_active(self) -> bool:
        """
        Check if the user account is active.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return self.status == UserStatus.ACTIVE

    @property
    def is_admin(self) -> bool:
        """
        Check if the user has admin privileges.

        Returns:
            bool: True if the user is an admin, False otherwise.
        """
        return self.role == UserRole.ADMIN

    def can_access(self, resource: str) -> bool:
        """
        Check if the user has access to a specific resource.

        Args:
            resource: The resource to check access for

        Returns:
            bool: True if the user can access the resource, False otherwise
        """
        if not self.is_active:
            return False

        # Admins have access to everything
        if self.is_admin:
            return True

        # Implement specific resource access rules here
        # This is a placeholder implementation
        return True

    def update_last_login(self) -> None:
        """
        Update the user's last login timestamp to now.
        """
        self.last_login = datetime.now()
