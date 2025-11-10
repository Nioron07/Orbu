#!/usr/bin/env python3
"""
Generate encryption keys for AcuNexus
"""

import secrets
from cryptography.fernet import Fernet


def generate_encryption_key():
    """Generate a Fernet encryption key for database encryption."""
    return Fernet.generate_key().decode()


def generate_secret_key():
    """Generate a secret key for Flask sessions."""
    return secrets.token_hex(32)


def main():
    print("=" * 50)
    print("       AcuNexus Key Generator")
    print("=" * 50)
    print()

    # Generate encryption key
    encryption_key = generate_encryption_key()
    print("ENCRYPTION_KEY (for encrypting credentials):")
    print(f"  {encryption_key}")
    print()

    # Generate Flask secret key
    secret_key = generate_secret_key()
    print("SECRET_KEY (for Flask sessions):")
    print(f"  {secret_key}")
    print()

    print("-" * 50)
    print("⚠️  IMPORTANT SECURITY NOTES:")
    print("1. Save these keys in your .env file")
    print("2. Keep these keys SECRET and SECURE")
    print("3. Never commit them to version control")
    print("4. Back them up securely")
    print("5. Loss of ENCRYPTION_KEY means loss of all encrypted data!")
    print("-" * 50)
    print()

    # Offer to save to .env file
    save = input("Do you want to save these to .env file? (y/n): ")
    if save.lower() == 'y':
        try:
            with open('.env', 'r') as f:
                content = f.read()

            # Replace placeholders
            content = content.replace('ENCRYPTION_KEY=your-encryption-key-here', f'ENCRYPTION_KEY={encryption_key}')
            content = content.replace('SECRET_KEY=your-secret-key-here-generate-with-script', f'SECRET_KEY={secret_key}')

            with open('.env', 'w') as f:
                f.write(content)

            print("✅ Keys saved to .env file successfully!")
        except FileNotFoundError:
            print("❌ .env file not found. Please create it from .env.example first.")
        except Exception as e:
            print(f"❌ Error saving keys: {e}")


if __name__ == "__main__":
    main()