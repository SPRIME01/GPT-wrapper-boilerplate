import pytest
from app.infrastructure.security.encryption import EncryptionService

class TestEncryptionService:
    @pytest.fixture
    def encryption_service(self):
        return EncryptionService()

    def test_symmetric_encryption(self, encryption_service):
        # Arrange
        original_data = "sensitive data"

        # Act
        encrypted = encryption_service.encrypt_symmetric(original_data)
        decrypted = encryption_service.decrypt_symmetric(encrypted)

        # Assert
        assert decrypted == original_data
        assert encrypted != original_data

    def test_sodium_encryption(self, encryption_service):
        # Arrange
        original_data = "sensitive data"

        # Act
        encrypted, key = encryption_service.encrypt_sodium(original_data)
        decrypted = encryption_service.decrypt_sodium(encrypted, key)

        # Assert
        assert decrypted == original_data
        assert encrypted != original_data

    def test_public_key_serialization(self, encryption_service):
        # Act
        serialized_key = encryption_service.serialize_public_key()

        # Assert
        assert isinstance(serialized_key, str)
        assert len(serialized_key) > 0

    def test_invalid_decrypt_raises_error(self, encryption_service):
        # Arrange
        invalid_data = "invalid_encrypted_data"

        # Assert
        with pytest.raises(Exception):
            encryption_service.decrypt_symmetric(invalid_data)
