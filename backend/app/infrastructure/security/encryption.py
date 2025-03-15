from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from nacl.secret import SecretBox
from nacl.utils import random
import base64
from typing import Tuple, Optional
from .sodium_service import SodiumService

class EncryptionService:
    def __init__(self):
        self._fernet_key = self._generate_fernet_key()
        self._fernet = Fernet(self._fernet_key)
        self._sodium = SodiumService()
        self.private_key, self.public_key = self._generate_ecc_keypair()

    def _generate_fernet_key(self) -> bytes:
        """Generate a Fernet key for AES-256 encryption"""
        return Fernet.generate_key()

    def _generate_ecc_keypair(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        """Generate ECC key pair for asymmetric encryption"""
        private_key = ec.generate_private_key(ec.SECP384R1())
        return private_key, private_key.public_key()

    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using AES-256"""
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt AES-256 encrypted data"""
        return self._fernet.decrypt(encrypted_data.encode()).decode()

    def encrypt_sodium(self, data: str) -> Tuple[str, str]:
        """Encrypt data using Libsodium"""
        return self._sodium.symmetric_encrypt(data)

    def decrypt_sodium(self, encrypted_data: str, key: str) -> str:
        """Decrypt Libsodium encrypted data"""
        return self._sodium.symmetric_decrypt(encrypted_data, key)

    def encrypt_sodium_asymmetric(self, data: str, recipient_public_key: bytes) -> str:
        """Encrypt data using Libsodium asymmetric encryption"""
        return self._sodium.asymmetric_encrypt(data, recipient_public_key)

    def decrypt_sodium_asymmetric(self, encrypted_data: str, sender_public_key: bytes) -> str:
        """Decrypt Libsodium asymmetric encrypted data"""
        return self._sodium.asymmetric_decrypt(encrypted_data, sender_public_key)

    def serialize_public_key(self) -> str:
        """Serialize public key for sharing"""
        return base64.b64encode(
            self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
        ).decode()
