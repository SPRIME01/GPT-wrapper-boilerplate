import pytest
from datetime import datetime, timedelta, UTC
from app.application.use_cases.manage_session_lifecycle_use_case import (
    ManageSessionLifecycleUseCase,
    CreateSessionCommand,
    UpdateSessionCommand
)
from app.domain.models.user_context import UserContext

class MockSessionRepository:
    def __init__(self):
        self.sessions = {}
        self.last_update = None

    async def save_session(self, session: UserContext) -> None:
        self.sessions[session.user_id] = session
        self.last_update = datetime.now(UTC)

    async def get_session(self, user_id: str) -> UserContext:
        return self.sessions.get(user_id)

    async def delete_session(self, user_id: str) -> None:
        if user_id in self.sessions:
            del self.sessions[user_id]

class TestManageSessionLifecycleUseCase:
    @pytest.fixture
    def session_repo(self):
        return MockSessionRepository()

    @pytest.fixture
    def use_case(self, session_repo):
        return ManageSessionLifecycleUseCase(session_repo)

    @pytest.mark.asyncio
    async def test_create_new_session(self, use_case, session_repo):
        # Arrange
        command = CreateSessionCommand(
            user_id="test_user",
            preferences={"language": "en", "model": "gpt-4"}
        )

        # Act
        session = await use_case.create_session(command)

        # Assert
        assert session.user_id == "test_user"
        assert session.preferences == {"language": "en", "model": "gpt-4"}
        assert session == session_repo.sessions["test_user"]

    @pytest.mark.asyncio
    async def test_update_existing_session(self, use_case, session_repo):
        # Arrange - Create initial session
        initial_session = UserContext(
            user_id="test_user",
            preferences={"language": "en", "model": "gpt-4"}
        )
        await session_repo.save_session(initial_session)

        # Update command
        command = UpdateSessionCommand(
            user_id="test_user",
            preferences={"language": "es", "model": "gpt-4"}
        )

        # Act
        updated_session = await use_case.update_session(command)

        # Assert
        assert updated_session.preferences["language"] == "es"
        assert session_repo.last_update is not None

    @pytest.mark.asyncio
    async def test_end_session(self, use_case, session_repo):
        # Arrange - Create session to end
        session = UserContext(
            user_id="test_user",
            preferences={"language": "en"}
        )
        await session_repo.save_session(session)

        # Act
        await use_case.end_session("test_user")

        # Assert
        assert "test_user" not in session_repo.sessions
