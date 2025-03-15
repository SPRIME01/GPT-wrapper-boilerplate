"""
Tests for security service implementation.

This module contains unit tests for the security service that coordinates
authentication and authorization, following the AAA pattern.
"""

import pytest
from unittest.mock import Mock, patch, create_autospec
from datetime import datetime

from app.domain.models.user import User, UserRole, UserStatus
from app.application.services.security_service import (
    SecurityService,
    secure_endpoint
)
from app.infrastructure.adapters.security.authentication import (
    AuthenticationService,
    InvalidTokenError,
    ExpiredTokenError
)
from app.infrastructure.adapters.security.authorization import (
    AuthorizationService,
    Permission,
    ResourcePolicy,
    UnauthorizedError
)


class TestSecurityService:
    """
    Tests for the SecurityService implementation.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    @pytest.fixture
    def mock_auth_service(self):
        # Create a mock with stricter spec checking
        return create_autospec(AuthenticationService, instance=True)

    @pytest.fixture
    def mock_authz_service(self):
        # Create a mock with stricter spec checking
        return create_autospec(AuthorizationService, instance=True)

    @pytest.fixture
    def security_service(self, mock_auth_service, mock_authz_service):
        return SecurityService(mock_auth_service, mock_authz_service)

    @pytest.fixture
    def test_user(self):
        return User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER
        )

    def test_SecurityService_AuthenticateToken_ValidToken_ReturnsUser(
        self,
        security_service,
        mock_auth_service,
        test_user
    ):
        # Arrange
        token = "valid.jwt.token"
        mock_auth_service.validate_token.return_value = test_user

        # Act
        result = security_service.authenticate_token(token)

        # Assert
        assert result == test_user
        mock_auth_service.validate_token.assert_called_once_with(token)

    def test_SecurityService_AuthenticateToken_InvalidToken_RaisesError(
        self,
        security_service,
        mock_auth_service
    ):
        # Arrange
        token = "invalid.jwt.token"
        mock_auth_service.validate_token.side_effect = InvalidTokenError("Invalid token")

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            security_service.authenticate_token(token)

    def test_SecurityService_GenerateToken_ValidUser_ReturnsToken(
        self,
        security_service,
        mock_auth_service,
        test_user
    ):
        # Arrange
        expected_token = "new.jwt.token"
        mock_auth_service.generate_token.return_value = expected_token

        # Act
        token = security_service.generate_token(test_user)

        # Assert
        assert token == expected_token
        mock_auth_service.generate_token.assert_called_once_with(test_user, None)

    def test_SecurityService_CheckAccess_UserWithPermission_ReturnsTrue(
        self,
        security_service,
        mock_authz_service,
        test_user
    ):
        # Arrange
        resource = "test_resource"
        permission = Permission.READ
        mock_authz_service.check_access.return_value = True

        # Act
        result = security_service.check_access(test_user, resource, permission)

        # Assert
        assert result is True
        mock_authz_service.check_access.assert_called_once_with(
            test_user, resource, permission
        )

    def test_SecurityService_EnforceAccess_UnauthorizedUser_RaisesError(
        self,
        security_service,
        mock_authz_service,
        test_user
    ):
        # Arrange
        resource = "restricted_resource"
        permission = Permission.WRITE
        mock_authz_service.enforce_access.side_effect = UnauthorizedError(
            "Access denied"
        )

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            security_service.enforce_access(test_user, resource, permission)

    def test_SecurityService_RefreshToken_ValidToken_ReturnsNewToken(
        self,
        security_service,
        mock_auth_service
    ):
        # Arrange
        old_token = "old.jwt.token"
        new_token = "new.jwt.token"
        mock_auth_service.refresh_token.return_value = new_token

        # Act
        result = security_service.refresh_token(old_token)

        # Assert
        assert result == new_token
        mock_auth_service.refresh_token.assert_called_once_with(old_token)

    def test_SecurityService_PolicyManagement_AddRemoveUpdate(
        self,
        security_service,
        mock_authz_service
    ):
        # Arrange
        policy = ResourcePolicy(
            resource="test_resource",
            allowed_roles=[UserRole.USER],
            allowed_permissions=[Permission.READ]
        )

        # Ensure mock methods don't return values
        mock_authz_service.add_policy.return_value = None
        mock_authz_service.update_policy.return_value = None
        mock_authz_service.remove_policy.return_value = None

        # Act
        security_service.add_policy(policy)
        security_service.update_policy(policy)
        security_service.remove_policy(policy)

        # Assert
        mock_authz_service.add_policy.assert_called_once_with(policy)
        mock_authz_service.update_policy.assert_called_once_with(policy)
        mock_authz_service.remove_policy.assert_called_once_with(policy)

    @pytest.mark.asyncio
    async def test_SecureEndpoint_Decorator_ValidTokenAndPermissions_CallsFunction(
        self,
        security_service,
        mock_auth_service,
        mock_authz_service,
        test_user
    ):
        # Arrange
        token = "valid.jwt.token"
        resource = "test_resource"
        permission = Permission.READ
        expected_result = {"data": "success"}

        mock_auth_service.validate_token.return_value = test_user
        mock_authz_service.enforce_access.return_value = None  # Doesn't raise error

        @secure_endpoint(resource, permission)
        async def test_function(token: str) -> dict:
            return expected_result

        # Act
        result = await test_function(security_service=security_service, token=token)

        # Assert
        assert result == expected_result
        mock_auth_service.validate_token.assert_called_once_with(token)
        mock_authz_service.enforce_access.assert_called_once_with(
            test_user, resource, permission
        )

    @pytest.mark.asyncio
    async def test_SecureEndpoint_Decorator_InvalidToken_RaisesError(
        self,
        security_service,
        mock_auth_service
    ):
        # Arrange
        token = "invalid.jwt.token"
        resource = "test_resource"
        permission = Permission.READ

        mock_auth_service.validate_token.side_effect = InvalidTokenError("Invalid token")

        @secure_endpoint(resource, permission)
        async def test_function(token: str) -> dict:
            return {"data": "success"}

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            await test_function(security_service=security_service, token=token)

    @pytest.mark.asyncio
    async def test_SecureEndpoint_Decorator_UnauthorizedAccess_RaisesError(
        self,
        security_service,
        mock_auth_service,
        mock_authz_service,
        test_user
    ):
        # Arrange
        token = "valid.jwt.token"
        resource = "restricted_resource"
        permission = Permission.WRITE

        mock_auth_service.validate_token.return_value = test_user
        mock_authz_service.enforce_access.side_effect = UnauthorizedError("Access denied")

        @secure_endpoint(resource, permission)
        async def test_function(token: str) -> dict:
            return {"data": "success"}

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            await test_function(security_service=security_service, token=token)
