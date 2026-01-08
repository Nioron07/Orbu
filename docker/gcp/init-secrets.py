#!/usr/bin/env python3
"""
Orbu GCP Secret Initialization
Fetches secrets from Google Secret Manager for production deployment.
"""

import os
import sys
import secrets
from cryptography.fernet import Fernet

# Environment file for secrets
SECRETS_ENV_FILE = "/tmp/orbu-secrets.env"

# GCP configuration
GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID')


def generate_secret_key():
    """Generate a random secret key for Flask sessions."""
    return secrets.token_hex(32)


def generate_encryption_key():
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()


def generate_postgres_password():
    """Generate a random PostgreSQL password."""
    return secrets.token_urlsafe(32)


def fetch_gcp_secret(secret_name):
    """Fetch a secret from Google Secret Manager."""
    try:
        from google.cloud import secretmanager
        from google.api_core.exceptions import GoogleAPIError, NotFound
        from google.api_core import retry

        if not GCP_PROJECT_ID:
            print(f"  GCP_PROJECT_ID not set, cannot fetch {secret_name}")
            return None

        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}/versions/latest"

        # Use a shorter timeout (10 seconds) to fail fast
        response = client.access_secret_version(
            request={"name": name},
            timeout=10.0
        )
        return response.payload.data.decode('UTF-8')

    except ImportError:
        print("  Google Cloud SDK not installed")
        return None
    except NotFound:
        print(f"  Secret '{secret_name}' not found in Secret Manager")
        return None
    except GoogleAPIError as e:
        print(f"  Failed to fetch secret from GCP: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error fetching GCP secret: {e}")
        return None


def create_gcp_secret(secret_name, secret_value):
    """Create a secret in Google Secret Manager."""
    try:
        from google.cloud import secretmanager
        from google.api_core.exceptions import AlreadyExists

        if not GCP_PROJECT_ID:
            return False

        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{GCP_PROJECT_ID}"

        # Create the secret
        try:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                },
                timeout=10.0
            )
            print(f"  Created secret '{secret_name}' in Secret Manager")
        except AlreadyExists:
            print(f"  Secret '{secret_name}' already exists, adding new version")

        # Add the secret version
        secret_path = f"projects/{GCP_PROJECT_ID}/secrets/{secret_name}"
        client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": secret_value.encode("UTF-8")},
            },
            timeout=10.0
        )
        print(f"  Stored value in '{secret_name}'")
        return True

    except Exception as e:
        print(f"  Failed to create secret in GCP: {e}")
        return False


def get_secret(env_var, secret_name, generator_func, required=False, auto_create=False):
    """
    Get a secret from:
    1. Environment variable (highest priority)
    2. GCP Secret Manager
    3. Auto-generate and optionally store in Secret Manager
    """
    # Check environment variable first
    value = os.getenv(env_var)
    if value:
        print(f"  {env_var}: Using value from environment")
        return value

    # Try GCP Secret Manager
    if GCP_PROJECT_ID:
        print(f"  {env_var}: Fetching from Secret Manager ({secret_name})...")
        value = fetch_gcp_secret(secret_name)
        if value:
            print(f"  {env_var}: Successfully fetched from Secret Manager")
            return value

        # Auto-create in Secret Manager if enabled
        if auto_create:
            print(f"  {env_var}: Not found, auto-generating and storing in Secret Manager...")
            value = generator_func()
            if create_gcp_secret(secret_name, value):
                print(f"  {env_var}: Successfully created in Secret Manager")
                return value
            else:
                print(f"  {env_var}: Failed to store in Secret Manager")
                if required:
                    return None
                return value

    # Auto-generate if not required (local development)
    if required and not GCP_PROJECT_ID:
        print(f"  ERROR: {env_var} is required but not found!")
        return None

    print(f"  {env_var}: Auto-generating (local development)")
    return generator_func()


def write_secrets_env(secrets_dict):
    """Write secrets to environment file for sourcing by entrypoint."""
    with open(SECRETS_ENV_FILE, 'w') as f:
        for key, value in secrets_dict.items():
            if value:
                f.write(f'export {key}="{value}"\n')
                os.environ[key] = value
    os.chmod(SECRETS_ENV_FILE, 0o600)


def main():
    """Main secret initialization routine."""
    print("=" * 50)
    print("Orbu Secret Initialization (GCP)")
    print(f"GCP Project: {GCP_PROJECT_ID or 'Not set (local mode)'}")
    print("=" * 50)

    is_production = bool(GCP_PROJECT_ID)

    # Get secrets
    print("\n[1/3] Getting Flask session secret...")
    secret_key = get_secret(
        'SECRET_KEY',
        'orbu-secret-key',
        generate_secret_key,
        required=False  # Can always generate
    )

    print("\n[2/3] Getting encryption key...")
    encryption_key = get_secret(
        'ENCRYPTION_KEY',
        'orbu-encryption-key',
        generate_encryption_key,
        required=is_production,
        auto_create=True  # Auto-create in Secret Manager on first deploy
    )

    if is_production and not encryption_key:
        print("\nERROR: ENCRYPTION_KEY is required in production!")
        print("Ensure the service account has 'Secret Manager Admin' role to auto-create secrets.")
        return 1

    print("\n[3/3] Getting PostgreSQL password...")
    postgres_password = get_secret(
        'POSTGRES_PASSWORD',
        'orbu-postgres-password',
        generate_postgres_password,
        required=is_production  # Required in production
    )

    if is_production and not postgres_password:
        print("\nERROR: POSTGRES_PASSWORD is required in production!")
        print("Create the secret in Secret Manager:")
        print(f"  echo -n 'your-password' | gcloud secrets create orbu-postgres-password --data-file=-")
        return 1

    # Write secrets to environment file
    secrets_dict = {
        'SECRET_KEY': secret_key,
        'ENCRYPTION_KEY': encryption_key,
        'POSTGRES_PASSWORD': postgres_password
    }

    print(f"\nWriting secrets to {SECRETS_ENV_FILE}")
    write_secrets_env(secrets_dict)

    print("\n" + "=" * 50)
    print("Secret initialization complete!")
    print("=" * 50)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\nERROR: Secret initialization failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
