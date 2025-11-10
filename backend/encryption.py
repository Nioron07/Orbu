"""
Encryption service for securing sensitive data like passwords.
Uses Fernet symmetric encryption from the cryptography library.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data.
    """

    def __init__(self, encryption_key=None):
        """
        Initialize the encryption service.

        Args:
            encryption_key: Base64 encoded encryption key. If None, will use environment variable.
        """
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Get key from environment or generate a new one
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                # For development, generate a key if not provided
                # In production, this should always be provided via environment
                print("WARNING: No ENCRYPTION_KEY found. Generating a new one.")
                print("Save this key in your .env file:")
                key = Fernet.generate_key().decode()
                print(f"ENCRYPTION_KEY={key}")

            self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    @staticmethod
    def generate_key():
        """
        Generate a new encryption key.

        Returns:
            str: Base64 encoded encryption key
        """
        return Fernet.generate_key().decode()

    @staticmethod
    def derive_key_from_password(password, salt=None):
        """
        Derive an encryption key from a password using PBKDF2.

        Args:
            password: Password to derive key from
            salt: Salt for key derivation. If None, a random salt is generated.

        Returns:
            tuple: (key, salt) - Base64 encoded key and salt
        """
        if salt is None:
            salt = os.urandom(16)
        elif isinstance(salt, str):
            salt = base64.b64decode(salt)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        return key.decode(), base64.b64encode(salt).decode()

    def encrypt(self, plaintext):
        """
        Encrypt plaintext string.

        Args:
            plaintext: String to encrypt

        Returns:
            str: Encrypted string (base64 encoded)
        """
        if not plaintext:
            return None

        # Ensure we're working with bytes
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()

        # Encrypt the data
        encrypted = self.fernet.encrypt(plaintext)

        # Return as base64 encoded string
        return encrypted.decode()

    def decrypt(self, ciphertext):
        """
        Decrypt ciphertext string.

        Args:
            ciphertext: Encrypted string (base64 encoded)

        Returns:
            str: Decrypted plaintext string
        """
        if not ciphertext:
            return None

        # Ensure we're working with bytes
        if isinstance(ciphertext, str):
            ciphertext = ciphertext.encode()

        try:
            # Decrypt the data
            decrypted = self.fernet.decrypt(ciphertext)

            # Return as string
            return decrypted.decode()
        except Exception as e:
            # Log the error (in production, use proper logging)
            print(f"Decryption error: {e}")
            return None

    def encrypt_dict(self, data):
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary with potential sensitive fields

        Returns:
            dict: Dictionary with encrypted sensitive fields
        """
        encrypted_data = data.copy()

        # List of fields to encrypt
        sensitive_fields = ['password', 'api_key', 'secret', 'token']

        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(encrypted_data[field])

        return encrypted_data

    def decrypt_dict(self, data):
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary with encrypted sensitive fields

        Returns:
            dict: Dictionary with decrypted sensitive fields
        """
        decrypted_data = data.copy()

        # List of fields to decrypt
        encrypted_fields = ['password', 'api_key', 'secret', 'token']

        for field in encrypted_fields:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_data[field] = self.decrypt(decrypted_data[field])

        return decrypted_data


# Global instance (will be initialized with app)
encryption_service = None


def init_encryption(app=None):
    """
    Initialize the global encryption service.

    Args:
        app: Flask application instance (optional)

    Returns:
        EncryptionService: Initialized encryption service
    """
    global encryption_service

    if app:
        # Get key from app config
        encryption_key = app.config.get('ENCRYPTION_KEY') or os.getenv('ENCRYPTION_KEY')
        encryption_service = EncryptionService(encryption_key)
    else:
        # Initialize with environment variable
        encryption_service = EncryptionService()

    return encryption_service


def get_encryption_service():
    """
    Get the global encryption service instance.

    Returns:
        EncryptionService: Global encryption service
    """
    global encryption_service

    if encryption_service is None:
        encryption_service = init_encryption()

    return encryption_service