"""
Authentication service implementations for the GPT Wrapper Boilerplate.

This module provides interfaces and implementations for authentication mechanisms
used throughout the application to secure endpoints and verify user identity.
"""

import jwt
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.domain.models.user import User, UserRole


class AuthenticationError(Exception):
    """Base exception for authentication-related errors."""
    pass


class InvalidTokenError(AuthenticationError):
    """Exception raised when a token is invalid or malformed."""
    pass


class ExpiredTokenError(AuthenticationError):
    """Exception raised when a token has expired."""
    pass


class AuthenticationService(ABC):
    """
    Abstract base class for authentication service implementations.

    This interface defines the contract for all authentication adapters in the system,
    allowing for different implementations (JWT, session-based, etc.) while
    maintaining a consistent API.
    """

    @abstractmethod
    def generate_token(self, user: User, expiry_minutes: Optional[int] = None) -> str:
        """
        Generate an authentication token for a user.

        Args:
            user: The user to generate a token for
            expiry_minutes: Optional token expiration time in minutes

        Returns:
            A string token that can be used for authentication
        """
        pass

    @abstractmethod
    def validate_token(self, token: str) -> User:
        """
        Validate an authentication token and return the associated user.

        Args:
            token: The token to validate

        Returns:
            The User associated with the token if valid

        Raises:
            InvalidTokenError: If the token is invalid or malformed
            ExpiredTokenError: If the token has expired
        """
        pass

    @abstractmethod
    def refresh_token(self, token: str) -> str:
        """
        Generate a new token from an existing valid token.

        Args:
            token: The current valid token to refresh

        Returns:
            A new token with extended expiration time

        Raises:
            InvalidTokenError: If the token is invalid or malformed
            ExpiredTokenError: If the token has expired
        """
        pass


class JWTAuthenticationService(AuthenticationService):
    """
    JWT-based implementation of the authentication service.

    This implementation uses JSON Web Tokens (JWT) for stateless authentication,
    making it suitable for distributed environments.
    """

    DEFAULT_EXPIRY_MINUTES = 60  # 1 hour default expiration

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        """
        Initialize the JWT authentication service.

        Args:
            secret_key: The secret key used to sign tokens
            algorithm: The JWT algorithm to use (default: HS256)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def generate_token(self, user: User, expiry_minutes: Optional[int] = None) -> str:
        """
        Generate a JWT token for a user.

        Args:
            user: The user to generate a token for
            expiry_minutes: Optional token expiration time in minutes

        Returns:
            A JWT token string
        """
        if expiry_minutes is None:
            expiry_minutes = self.DEFAULT_EXPIRY_MINUTES

        now = int(time.time())
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "iat": now,
            "exp": now + (expiry_minutes * 60)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> User:
        """
        Validate a JWT token and return the associated user.

        Args:
            token: The JWT token to validate

        Returns:
            The User associated with the token

        Raises:
            InvalidTokenError: If the token is invalid or malformed
            ExpiredTokenError: If the token has expired
        """
        try:
            # Configure validation options with leeway
            options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iat", "sub", "username", "email", "role"]
            }

            # Decode and validate the token with 10 seconds leeway
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options=options,
                leeway=10  # Allow 10 seconds leeway for timing differences
            )

            return User(
                id=payload["sub"],
                username=payload["username"],
                email=payload["email"],
                role=UserRole(payload["role"]),
                created_at=datetime.fromtimestamp(payload["iat"])
            )
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid token: {str(e)}")

    def refresh_token(self, token: str) -> str:
        """
        Generate a new JWT token from an existing valid token.

        Args:
            token: The current valid token to refresh

        Returns:
            A new JWT token with extended expiration time

        Raises:
            InvalidTokenError: If the token is invalid or malformed
            ExpiredTokenError: If the token has expired
        """
        # First validate the current token
        user = self.validate_token(token)

        # Generate a new token for the same user with fresh timestamps
        now = int(time.time())
        payload = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "iat": now,
            "exp": now + (self.DEFAULT_EXPIRY_MINUTES * 60)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
