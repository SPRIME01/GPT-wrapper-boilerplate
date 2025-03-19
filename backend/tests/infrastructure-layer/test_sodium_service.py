import pytest
from nacl.public import PrivateKey, Box
import base64
from app.infrastructure.security.sodium_service import SodiumService

class TestSodiumService:
    @pytest.fixture
    def sodium_service(self):
        return SodiumService()

    @pytest.fixture
    def other_private_key(self):
        return PrivateKey.generate()

    def test_asymmetric_encryption(self, sodium_service, other_private_key):
        # Arrange
        original_data = "sensitive data"
        other_public_key = other_private_key.public_key

        # Act
        # Encrypt with other's public key
        encrypted = sodium_service.asymmetric_encrypt(
            original_data,
            other_public_key
        )

        # Decrypt with other's private key and sodium_service's public key
        box = Box(other_private_key, sodium_service.public_key)
        decrypted_bytes = box.decrypt(base64.b64decode(encrypted))
        decrypted = decrypted_bytes.decode()

        # Assert
        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert decrypted == original_data

    def test_symmetric_encryption(self, sodium_service):
        # Arrange
        original_data = "sensitive data"

        # Act
        encrypted, key = sodium_service.symmetric_encrypt(original_data)
        decrypted = sodium_service.symmetric_decrypt(encrypted, key)

        # Assert
        assert encrypted != original_data
        assert decrypted == original_data

    def test_asymmetric_encryption_with_invalid_key(self, sodium_service):
        # Arrange
        original_data = "sensitive data"
        invalid_public_key = b"invalid_key"

        # Act & Assert
        with pytest.raises(Exception):
            sodium_service.asymmetric_encrypt(original_data, invalid_public_key)

    def test_symmetric_decryption_with_invalid_key(self, sodium_service):
        # Arrange
        original_data = "sensitive data"
        encrypted, key = sodium_service.symmetric_encrypt(original_data)
        invalid_key = "invalid_key"

        # Act & Assert
        with pytest.raises(Exception):
            sodium_service.symmetric_decrypt(encrypted, invalid_key)

    def test_asymmetric_decryption_with_invalid_key(self, sodium_service, other_private_key):
        # Arrange
        original_data = "sensitive data"
        other_public_key = other_private_key.public_key
        encrypted = sodium_service.asymmetric_encrypt(original_data, other_public_key)
        invalid_private_key = PrivateKey.generate()

        # Act & Assert
        with pytest.raises(Exception):
            box = Box(invalid_private_key, sodium_service.public_key)
            box.decrypt(base64.b64decode(encrypted))
