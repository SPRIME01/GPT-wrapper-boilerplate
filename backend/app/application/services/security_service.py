"""
Security service for the GPT Wrapper Boilerplate.

This module provides a high-level security service that coordinates between
authentication and authorization mechanisms.
"""

from functools import wraps
from typing import Optional, Callable, Any, List, Union, Dict

from app.domain.models.user import User
from app.infrastructure.adapters.security.authentication import (
    AuthenticationService,
    AuthenticationError
)
from app.infrastructure.adapters.security.authorization import (
    AuthorizationService,
    Permission,
    ResourcePolicy,
    UnauthorizedError
)


def secure_endpoint(
    resource: str,
    permissions: Union[Permission, List[Permission]]
) -> Callable:
    """
    Decorator factory for securing API endpoints.

    This decorator handles both authentication and authorization in a single step.
    It expects the decorated function to have a 'token' parameter.

    Args:
        resource: The resource being accessed
        permissions: Required permission(s) for the resource

    Returns:
        A decorator function that checks authentication and authorization

    Example:
        @secure_endpoint("user_data", Permission.READ)
        async def get_user_data(token: str, user_id: str) -> Dict:
            # Function implementation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(security_service: "SecurityService", token: str, *args, **kwargs) -> Any:
            # Authenticate the user
            user = security_service.authenticate_token(token)

            # Check authorization
            security_service.enforce_access(user, resource, permissions)

            # Call the original function
            return await func(token=token, *args, **kwargs)
        return wrapper
    return decorator


class SecurityService:
    """
    Application service for coordinating security operations.

    This service provides a high-level interface for handling authentication
    and authorization, abstracting away the implementation details.
    """

    def __init__(
        self,
        auth_service: AuthenticationService,
        authz_service: AuthorizationService
    ):
        """
        Initialize the security service.

        Args:
            auth_service: Authentication service implementation
            authz_service: Authorization service implementation
        """
        self._auth_service = auth_service
        self._authz_service = authz_service

    def authenticate_token(self, token: str) -> User:
        """
        Validate an authentication token and return the associated user.

        Args:
            token: The token to validate

        Returns:
            The authenticated User

        Raises:
            AuthenticationError: If authentication fails
        """
        return self._auth_service.validate_token(token)

    def generate_token(self, user: User, expiry_minutes: Optional[int] = None) -> str:
        """
        Generate an authentication token for a user.

        Args:
            user: The user to generate a token for
            expiry_minutes: Optional token expiration time in minutes

        Returns:
            A new authentication token
        """
        return self._auth_service.generate_token(user, expiry_minutes)

    def refresh_token(self, token: str) -> str:
        """
        Generate a new token from an existing valid token.

        Args:
            token: The current valid token to refresh

        Returns:
            A new token with extended expiration time

        Raises:
            AuthenticationError: If the current token is invalid
        """
        return self._auth_service.refresh_token(token)

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
        return self._authz_service.check_access(user, resource, permissions)

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
        self._authz_service.enforce_access(user, resource, permissions)

    def add_policy(self, policy: ResourcePolicy) -> None:
        """
        Add a new access policy.

        Args:
            policy: The policy to add
        """
        self._authz_service.add_policy(policy)

    def remove_policy(self, policy: ResourcePolicy) -> None:
        """
        Remove an access policy.

        Args:
            policy: The policy to remove
        """
        self._authz_service.remove_policy(policy)

    def update_policy(self, policy: ResourcePolicy) -> None:
        """
        Update an existing access policy.

        Args:
            policy: The updated policy
        """
        self._authz_service.update_policy(policy)
