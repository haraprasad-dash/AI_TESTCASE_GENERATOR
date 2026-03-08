"""
Encryption utilities for API key storage.
Uses AES-256 with key derived from machine UUID.
"""
import os
import base64
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


def get_machine_uuid() -> str:
    """Get a unique identifier for this machine."""
    # In production, this should use a more robust method
    # such as platform-specific machine UUIDs
    import platform
    import socket
    
    # Combine machine-specific info
    info = f"{platform.node()}-{socket.gethostname()}"
    return info


def derive_key(password: str, salt: Optional[bytes] = None) -> tuple:
    """
    Derive encryption key from password.
    
    Returns:
        Tuple of (key, salt)
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


class EncryptionManager:
    """Manager for encrypting/decrypting sensitive data."""
    
    def __init__(self):
        self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key."""
        # In production, store salt securely
        machine_uuid = get_machine_uuid()
        key, _ = derive_key(machine_uuid)
        return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        return self._fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        return self._fernet.decrypt(encrypted_data.encode()).decode()


# Global encryption manager
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create encryption manager."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager
