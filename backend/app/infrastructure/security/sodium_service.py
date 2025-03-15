from nacl.secret import SecretBox
from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random
import base64
from typing import Tuple, Optional, Union

class SodiumService:
    """Service for handling encryption using Libsodium (PyNaCl)"""

    def __init__(self):
        # Generate keypair for public-key encryption
        self._private_key = PrivateKey.generate()
        self.public_key = self._private_key.public_key

    def symmetric_encrypt(self, data: str) -> Tuple[str, str]:
        """Encrypt data using Libsodium's SecretBox (XSalsa20-Poly1305)"""
        key = random(SecretBox.KEY_SIZE)
        box = SecretBox(key)
        encrypted = box.encrypt(data.encode())
        return (
            base64.b64encode(encrypted).decode(),
            base64.b64encode(key).decode()
        )

    def symmetric_decrypt(self, encrypted_data: str, key: str) -> str:
        """Decrypt data using Libsodium's SecretBox"""
        box = SecretBox(base64.b64decode(key))
        decrypted = box.decrypt(base64.b64decode(encrypted_data))
        return decrypted.decode()

    def asymmetric_encrypt(self, data: str, recipient_public_key: Union[PublicKey, bytes]) -> str:
        """
        Encrypt data using Libsodium's Box (curve25519xsalsa20poly1305)

        Args:
            data: The string data to encrypt
            recipient_public_key: The recipient's PublicKey object or bytes
        """
        if isinstance(recipient_public_key, bytes):
            recipient_public_key = PublicKey(recipient_public_key)

        box = Box(self._private_key, recipient_public_key)
        encrypted = box.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()

    def asymmetric_decrypt(self, encrypted_data: str, sender_public_key: Union[PublicKey, bytes]) -> str:
        """
        Decrypt data using Libsodium's Box

        Args:
            encrypted_data: The encrypted data as a base64 string
            sender_public_key: The sender's PublicKey object or bytes
        """
        if isinstance(sender_public_key, bytes):
            sender_public_key = PublicKey(sender_public_key)

        box = Box(self._private_key, sender_public_key)
        decrypted = box.decrypt(base64.b64decode(encrypted_data))
        return decrypted.decode()
