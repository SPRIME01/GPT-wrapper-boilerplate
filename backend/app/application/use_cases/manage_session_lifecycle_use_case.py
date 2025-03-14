from dataclasses import dataclass
from typing import Dict, Optional, Protocol
from app.domain.models.user_context import UserContext

@dataclass
class CreateSessionCommand:
    """Command for creating a new user session"""
    user_id: str
    preferences: Dict[str, str]

@dataclass
class UpdateSessionCommand:
    """Command for updating an existing session"""
    user_id: str
    preferences: Dict[str, str]

class SessionRepository(Protocol):
    """Port interface for session persistence"""
    async def save_session(self, session: UserContext) -> None: ...
    async def get_session(self, user_id: str) -> Optional[UserContext]: ...
    async def delete_session(self, user_id: str) -> None: ...

class ManageSessionLifecycleUseCase:
    """
    Use case for managing user session lifecycle, including creation,
    updates, and termination.
    """

    def __init__(self, session_repository: SessionRepository):
        self.session_repository = session_repository

    async def create_session(self, command: CreateSessionCommand) -> UserContext:
        """
        Create a new user session with specified preferences.

        Args:
            command: Session creation parameters

        Returns:
            UserContext: The newly created session
        """
        session = UserContext(
            user_id=command.user_id,
            preferences=command.preferences
        )
        await self.session_repository.save_session(session)
        return session

    async def update_session(self, command: UpdateSessionCommand) -> UserContext:
        """
        Update an existing user session with new preferences.

        Args:
            command: Session update parameters

        Returns:
            UserContext: The updated session

        Raises:
            ValueError: If session does not exist
        """
        current_session = await self.session_repository.get_session(command.user_id)
        if not current_session:
            raise ValueError(f"No session found for user {command.user_id}")

        updated_session = UserContext(
            user_id=command.user_id,
            preferences=command.preferences
        )
        await self.session_repository.save_session(updated_session)
        return updated_session

    async def end_session(self, user_id: str) -> None:
        """
        End a user session and cleanup any resources.

        Args:
            user_id: ID of the user whose session to end
        """
        await self.session_repository.delete_session(user_id)
