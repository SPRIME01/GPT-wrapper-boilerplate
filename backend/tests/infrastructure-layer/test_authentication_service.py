"""
Tests for authentication service implementation.

This module contains unit tests for the authentication service adapters,
following the AAA pattern (Arrange, Act, Assert).
"""

import pytest
import time
from datetime import datetime, timedelta, timezone  # Added import for timezone
from unittest.mock import Mock, patch
import jwt
from freezegun import freeze_time

from app.domain.models.user import User, UserRole
from app.infrastructure.adapters.security.authentication import (
    AuthenticationService,
    JWTAuthenticationService,
    AuthenticationError,
    InvalidTokenError,
    ExpiredTokenError
)


class TestJWTAuthenticationService:
    """
    Tests for the JWT-based authentication service implementation.

    Following AAA pattern (Arrange, Act, Assert) for all tests.
    """

    def test_JWTAuthService_GenerateToken_WithValidUser_ReturnsValidJWT(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(
            id="user123",
            username="testuser",
            email="test@example.com",
            role=UserRole.USER
        )

        # Act
        token = auth_service.generate_token(user)

        # Assert
        assert token is not None
        # Verify we can decode the token with the same secret
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        assert decoded["sub"] == user.id
        assert decoded["username"] == user.username
        assert decoded["email"] == user.email
        assert decoded["role"] == user.role.value
        assert "exp" in decoded  # Should have expiration
        assert "iat" in decoded  # Should have issued at time

    def test_JWTAuthService_GenerateToken_WithCustomExpiry_SetsCorrectExpiration(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)
        expiry_minutes = 60  # 1 hour

        # Act
        token = auth_service.generate_token(user, expiry_minutes=expiry_minutes)

        # Assert
        decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
        # Check that expiration time is ~60 minutes in the future (allow for small timing differences)
        expected_exp = int(time.time()) + expiry_minutes * 60
        assert abs(decoded["exp"] - expected_exp) < 5  # Within 5 seconds

    def test_JWTAuthService_ValidateToken_WithValidToken_ReturnsUser(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        original_user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)
        token = auth_service.generate_token(original_user)

        # Act
        validated_user = auth_service.validate_token(token)

        # Assert
        assert validated_user is not None
        assert validated_user.id == original_user.id
        assert validated_user.username == original_user.username
        assert validated_user.email == original_user.email
        assert validated_user.role == original_user.role

    def test_JWTAuthService_ValidateToken_WithExpiredToken_RaisesExpiredTokenError(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)

        # Create a token that is already expired
        with patch("time.time") as mock_time:
            now = time.time()
            mock_time.return_value = now - 60  # Set time 60 seconds in the past
            token = auth_service.generate_token(user, expiry_minutes=0)  # 0 minutes (immediate expiry)

        # Act & Assert
        with pytest.raises(ExpiredTokenError):
            auth_service.validate_token(token)

    def test_JWTAuthService_ValidateToken_WithInvalidToken_RaisesInvalidTokenError(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        invalid_token = "invalid.jwt.token"

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            auth_service.validate_token(invalid_token)

    def test_JWTAuthService_ValidateToken_WithTamperedToken_RaisesInvalidTokenError(self):
        # Arrange
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)
        valid_token = auth_service.generate_token(user)

        # Create a tampered token by changing one character
        tampered_token = valid_token[:-1] + ("A" if valid_token[-1] != "A" else "B")

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            auth_service.validate_token(tampered_token)

    def test_JWTAuthService_ValidateToken_WithWrongSecretKey_RaisesInvalidTokenError(self):
        # Arrange
        secret_key = "test_secret_key"
        wrong_secret = "wrong_secret_key"

        # Create token with original secret
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)
        token = auth_service.generate_token(user)

        # Try to validate with different secret
        wrong_auth_service = JWTAuthenticationService(secret_key=wrong_secret)

        # Act & Assert
        with pytest.raises(InvalidTokenError):
            wrong_auth_service.validate_token(token)

    def test_JWTAuthService_RefreshToken_WithValidToken_ReturnsNewToken(self):
        """
        Test that a valid refresh token returns a new token with updated issue time and expiry,
        while maintaining the same user claims. Time control is achieved via freezegun.
        """
        secret_key = "test_secret_key"
        auth_service = JWTAuthenticationService(secret_key=secret_key)
        user = User(id="user123", username="testuser", email="test@example.com", role=UserRole.USER)

        # Freeze time at the initial time for token generation
        initial_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        with freeze_time(initial_time):
            original_token = auth_service.generate_token(user, expiry_minutes=60)

        # Freeze time at a later point within the token validity period
        later_time = initial_time + timedelta(seconds=1000)
        with freeze_time(later_time):
            new_token = auth_service.refresh_token(original_token)

        # Decode tokens without time validation
        decode_options = {
            "verify_signature": True,
            "verify_exp": False,
            "verify_iat": False,
        }
        original_payload = jwt.decode(
            original_token,
            secret_key,
            algorithms=["HS256"],
            options=decode_options
        )
        new_payload = jwt.decode(
            new_token,
            secret_key,
            algorithms=["HS256"],
            options=decode_options
        )

        # Assert: Verify that new token issuance time and expiry are updated
        assert original_payload["iat"] == int(initial_time.timestamp())
        assert new_payload["iat"] == int(later_time.timestamp())
        assert original_payload["exp"] < new_payload["exp"]

        # Verify that user claim data remains unchanged
        assert original_payload["sub"] == new_payload["sub"] == user.id
        assert original_payload["username"] == new_payload["username"] == user.username
        assert original_payload["email"] == new_payload["email"] == user.email
        assert original_payload["role"] == new_payload["role"] == user.role.value
