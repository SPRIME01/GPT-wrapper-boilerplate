"""
Authorization service implementations for the GPT Wrapper Boilerplate.

This module provides interfaces and implementations for authorization mechanisms
used throughout the application to control access to resources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Set, Union, Optional

from app.domain.models.user import User, UserRole


class Permission(Enum):
    """
    Enumeration of possible permissions for resources.
    """
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"


@dataclass
class ResourcePolicy:
    """
    Domain model representing an access policy for a resource.

    This class defines which roles have which permissions for a specific resource.
    """

    resource: str
    """The resource this policy applies to."""

    allowed_roles: List[UserRole]
    """Roles that have access to this resource."""

    allowed_permissions: List[Permission]
    """Permissions granted by this policy."""


class UnauthorizedError(Exception):
    """Exception raised when a user attempts an unauthorized action."""


class AuthorizationService(ABC):
    """
    Abstract base class for authorization service implementations.

    This interface defines the contract for all authorization adapters in the system,
    allowing for different implementations while maintaining a consistent API.
    """

    @abstractmethod
    def check_access(
        self,
        user: User,
        resource: str,
        permissions: Union[Permission, List[Permission]]
    ) -> bool:
        """
        Check if a user has the required permissions for a resource.

        Args:
            user: The user attempting to access the resource
            resource: The resource being accessed
            permissions: Required permission(s)

        Returns:
            bool: True if access is allowed, False otherwise
        """
        pass

    @abstractmethod
    def enforce_access(
        self,
        user: User,
        resource: str,
        permissions: Union[Permission, List[Permission]]
    ) -> None:
        """
        Enforce access control by raising an exception if access is denied.

        Args:
            user: The user attempting to access the resource
            resource: The resource being accessed
            permissions: Required permission(s)

        Raises:
            UnauthorizedError: If the user doesn't have required permissions
        """
        pass

    @abstractmethod
    def add_policy(self, policy: ResourcePolicy) -> None:
        """
        Add a new access policy for a resource.

        Args:
            policy: The policy to add
        """
        pass

    @abstractmethod
    def remove_policy(self, policy: ResourcePolicy) -> None:
        """
        Remove an access policy.

        Args:
            policy: The policy to remove
        """
        pass

    @abstractmethod
    def update_policy(self, policy: ResourcePolicy) -> None:
        """
        Update an existing access policy.

        Args:
            policy: The updated policy
        """
        pass


class RBACAuthorizationService(AuthorizationService):
    """
    Role-Based Access Control (RBAC) implementation of the authorization service.

    This implementation uses role-based policies to determine access rights,
    with support for resource-specific permissions.
    """

    def __init__(self):
        """Initialize the RBAC authorization service with empty policies."""
        self._policies: Dict[str, ResourcePolicy] = {}

    def add_policy(self, policy: ResourcePolicy) -> None:
        """
        Add a new access policy for a resource.

        Args:
            policy: The policy to add
        """
        self._policies[policy.resource] = policy

    def remove_policy(self, policy: ResourcePolicy) -> None:
        """
        Remove an access policy.

        Args:
            policy: The policy to remove
        """
        self._policies.pop(policy.resource, None)

    def update_policy(self, policy: ResourcePolicy) -> None:
        """
        Update an existing access policy.

        Args:
            policy: The updated policy
        """
        self._policies[policy.resource] = policy

    def check_access(
        self,
        user: User,
        resource: str,
        permissions: Union[Permission, List[Permission]]
    ) -> bool:
        """
        Check if a user has the required permissions for a resource.

        Args:
            user: The user attempting to access the resource
            resource: The resource being accessed
            permissions: Required permission(s)

        Returns:
            bool: True if access is allowed, False otherwise
        """
        # First check if user is active
        if not user.is_active:
            return False

        # Admins have access to everything
        if user.is_admin:
            return True

        # Convert single permission to list for uniform handling
        if isinstance(permissions, Permission):
            permissions = [permissions]

        # Get policy for the resource
        policy = self._policies.get(resource)
        if not policy:
            return False

        # Check if user's role is allowed and has all required permissions
        if user.role in policy.allowed_roles:
            return all(perm in policy.allowed_permissions for perm in permissions)

        return False

    def enforce_access(
        self,
        user: User,
        resource: str,
        permissions: Union[Permission, List[Permission]]
    ) -> None:
        """
        Enforce access control by raising an exception if access is denied.

        Args:
            user: The user attempting to access the resource
            resource: The resource being accessed
            permissions: Required permission(s)

        Raises:
            UnauthorizedError: If the user doesn't have required permissions
        """
        if not self.check_access(user, resource, permissions):
            if isinstance(permissions, Permission):
                perm_str = permissions.value
            else:
                perm_str = ", ".join(p.value for p in permissions)

            raise UnauthorizedError(
                f"User {user.username} does not have permission(s) {perm_str} "
                f"for resource {resource}"
            )
