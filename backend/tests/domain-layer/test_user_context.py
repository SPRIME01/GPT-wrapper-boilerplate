import pytest
from app.domain.models.user_context import UserContext

class TestUserContext:
    def test_create_user_context_with_valid_data(self):
        """Test creating a UserContext with valid data"""
        context_data = {
            "user_id": "user123",
            "conversation_history": ["Hello", "Hi there!"],
            "preferences": {
                "tone": "friendly",
                "verbosity": "concise"
            }
        }

        context = UserContext(**context_data)

        assert context.user_id == "user123"
        assert context.conversation_history == ["Hello", "Hi there!"]
        assert context.preferences == {"tone": "friendly", "verbosity": "concise"}
        assert context.created_at is not None
        assert context.updated_at is not None

    def test_user_context_validation(self):
        """Test validation checks when creating a UserContext"""
        with pytest.raises(ValueError):
            # Test empty user_id
            UserContext(user_id="", conversation_history=[])

    def test_user_context_default_values(self):
        """Test default values are set correctly when not provided"""
        context = UserContext(user_id="user123")

        assert context.conversation_history == []  # Default empty list
        assert context.preferences == {}  # Default empty dict

    def test_add_conversation_entry(self):
        """Test adding a new entry to conversation history"""
        context = UserContext(user_id="user123")

        # Initial state
        assert len(context.conversation_history) == 0

        # Add an entry
        context.add_to_conversation("Hello GPT")
        assert len(context.conversation_history) == 1
        assert context.conversation_history[0] == "Hello GPT"

        # Add another entry
        context.add_to_conversation("Response from GPT")
        assert len(context.conversation_history) == 2

    def test_update_preferences(self):
        """Test updating user preferences"""
        context = UserContext(user_id="user123",
                              preferences={"tone": "formal"})

        # Initial state
        assert context.preferences == {"tone": "formal"}

        # Update preferences
        context.update_preferences({"verbosity": "detailed"})

        # Should merge with existing preferences
        assert context.preferences == {"tone": "formal", "verbosity": "detailed"}

        # Should override existing value
        context.update_preferences({"tone": "casual"})
        assert context.preferences == {"tone": "casual", "verbosity": "detailed"}

    def test_clear_conversation_history(self):
        """Test clearing conversation history"""
        context = UserContext(
            user_id="user123",
            conversation_history=["Hello", "Hi there", "How are you?"]
        )

        # Initial state
        assert len(context.conversation_history) == 3

        # Clear history
        context.clear_conversation_history()

        # Should be empty
        assert len(context.conversation_history) == 0
