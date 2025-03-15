"""
Tests for authorization service implementation.

This module contains unit tests for the authorization service adapters,
following the AAA pattern (Arrange, Act, Assert).
"""

import pytest
from datetime import datetime

from app.domain.models.user import User, UserRole, UserStatus
from app.infrastructure.adapters.security.authorization import (
    AuthorizationService,
    RBACAuthorizationService,
    UnauthorizedError,
    ResourcePolicy,
    Permission
)


class TestRBACAuthorizationService:
    """
    Tests for the RBAC-based authorization service implementation.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_RBACAuth_CheckAccess_AdminUserHasAccess_ReturnsTrue(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        admin_user = User(
            id="admin123",
            username="admin",
            email="admin@example.com",
            role=UserRole.ADMIN
        )
        resource = "sensitive_data"
        permission = Permission.READ

        # Act
        result = auth_service.check_access(admin_user, resource, permission)

        # Assert
        assert result is True

    def test_RBACAuth_CheckAccess_StandardUserWithPermission_ReturnsTrue(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "public_data"
        permission = Permission.READ

        # Add a policy that allows users to read public data
        policy = ResourcePolicy(
            resource="public_data",
            allowed_roles=[UserRole.USER, UserRole.ADMIN],
            allowed_permissions=[Permission.READ]
        )
        auth_service.add_policy(policy)

        # Act
        result = auth_service.check_access(user, resource, permission)

        # Assert
        assert result is True

    def test_RBACAuth_CheckAccess_StandardUserWithoutPermission_ReturnsFalse(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "sensitive_data"
        permission = Permission.WRITE

        # Add a policy that only allows admins to write sensitive data
        policy = ResourcePolicy(
            resource="sensitive_data",
            allowed_roles=[UserRole.ADMIN],
            allowed_permissions=[Permission.WRITE]
        )
        auth_service.add_policy(policy)

        # Act
        result = auth_service.check_access(user, resource, permission)

        # Assert
        assert result is False

    def test_RBACAuth_EnforceAccess_UnauthorizedUser_RaisesException(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "sensitive_data"
        permission = Permission.WRITE

        # Add a policy that only allows admins to write sensitive data
        policy = ResourcePolicy(
            resource="sensitive_data",
            allowed_roles=[UserRole.ADMIN],
            allowed_permissions=[Permission.WRITE]
        )
        auth_service.add_policy(policy)

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            auth_service.enforce_access(user, resource, permission)

    def test_RBACAuth_CheckAccess_InactiveUser_ReturnsFalse(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.INACTIVE
        )
        resource = "any_resource"
        permission = Permission.READ

        # Act
        result = auth_service.check_access(user, resource, permission)

        # Assert
        assert result is False

    def test_RBACAuth_CheckAccess_MultiplePermissions_ChecksAll(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "document"
        permissions = [Permission.READ, Permission.WRITE]

        # Add a policy that allows users to read and write documents
        policy = ResourcePolicy(
            resource="document",
            allowed_roles=[UserRole.USER],
            allowed_permissions=[Permission.READ, Permission.WRITE]
        )
        auth_service.add_policy(policy)

        # Act
        result = auth_service.check_access(user, resource, permissions)

        # Assert
        assert result is True

    def test_RBACAuth_RemovePolicy_PolicyRemoved_ReturnsFalse(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "temp_resource"
        permission = Permission.READ

        # Add a temporary policy
        policy = ResourcePolicy(
            resource="temp_resource",
            allowed_roles=[UserRole.USER],
            allowed_permissions=[Permission.READ]
        )
        auth_service.add_policy(policy)

        # Verify access is initially granted
        initial_access = auth_service.check_access(user, resource, permission)

        # Act
        auth_service.remove_policy(policy)
        result = auth_service.check_access(user, resource, permission)

        # Assert
        assert initial_access is True
        assert result is False

    def test_RBACAuth_UpdatePolicy_PolicyUpdated_ReflectsChanges(self):
        # Arrange
        auth_service = RBACAuthorizationService()
        user = User(
            id="user123",
            username="user",
            email="user@example.com",
            role=UserRole.USER
        )
        resource = "dynamic_resource"
        permission = Permission.WRITE

        # Add initial policy
        initial_policy = ResourcePolicy(
            resource="dynamic_resource",
            allowed_roles=[UserRole.ADMIN],
            allowed_permissions=[Permission.WRITE]
        )
        auth_service.add_policy(initial_policy)

        # Verify initial access is denied
        initial_access = auth_service.check_access(user, resource, permission)

        # Update policy to allow users
        updated_policy = ResourcePolicy(
            resource="dynamic_resource",
            allowed_roles=[UserRole.USER, UserRole.ADMIN],
            allowed_permissions=[Permission.WRITE]
        )
        auth_service.update_policy(updated_policy)

        # Act
        result = auth_service.check_access(user, resource, permission)

        # Assert
        assert initial_access is False
        assert result is True
