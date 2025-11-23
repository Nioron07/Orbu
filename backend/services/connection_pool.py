"""
Connection Pool Service

Manages persistent Acumatica client connections for endpoint execution.
Separate from session-based connections used for frontend management.
"""

import logging
from datetime import datetime, timezone, timedelta
from threading import Lock
from easy_acumatica import AcumaticaClient
from models import Client
from encryption import get_encryption_service

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Manages a pool of persistent Acumatica client connections.

    Each client can have one persistent connection that is:
    - Created on first endpoint request
    - Kept alive for multiple requests
    - Automatically reconnected if expired
    - Thread-safe for concurrent requests
    """

    def __init__(self):
        self._connections = {}  # client_id -> (acumatica_client, last_used_timestamp)
        self._locks = {}        # client_id -> threading.Lock
        self._global_lock = Lock()

    def get_connection(self, client_id: str) -> AcumaticaClient:
        """
        Get or create a persistent connection for a client.

        Args:
            client_id: UUID of the client

        Returns:
            AcumaticaClient instance

        Raises:
            Exception if connection fails
        """
        # Ensure we have a lock for this client
        with self._global_lock:
            if client_id not in self._locks:
                self._locks[client_id] = Lock()

        # Thread-safe connection retrieval/creation
        with self._locks[client_id]:
            # Check if we have an existing connection
            if client_id in self._connections:
                acumatica_client, last_used = self._connections[client_id]

                # Check if connection is still valid (used within last 30 minutes)
                if datetime.now(timezone.utc) - last_used < timedelta(minutes=30):
                    # Update last used timestamp
                    self._connections[client_id] = (acumatica_client, datetime.now(timezone.utc))
                    logger.info(f"Reusing existing connection for client {client_id}")
                    return acumatica_client
                else:
                    # Connection too old, disconnect and create new
                    logger.info(f"Connection expired for client {client_id}, reconnecting")
                    try:
                        acumatica_client.logout()
                    except Exception as e:
                        logger.warning(f"Error logging out expired connection: {e}")

            # Create new connection
            logger.info(f"Creating new connection for client {client_id}")
            acumatica_client = self._create_connection(client_id)

            # Store in pool
            self._connections[client_id] = (acumatica_client, datetime.now(timezone.utc))

            return acumatica_client

    def _create_connection(self, client_id: str) -> AcumaticaClient:
        """
        Create a new Acumatica client connection.

        Args:
            client_id: UUID of the client

        Returns:
            AcumaticaClient instance

        Raises:
            Exception if client not found or connection fails
        """
        # Get client from database
        client = Client.query.get(client_id)
        if not client:
            raise Exception(f"Client {client_id} not found")

        if not client.is_active:
            raise Exception(f"Client {client_id} is inactive")

        # Decrypt credentials
        encryption = get_encryption_service()
        username = encryption.decrypt(client.encrypted_username)
        password = encryption.decrypt(client.encrypted_password)

        # Check if decryption failed
        if not username or not password:
            logger.error(f"Failed to decrypt credentials for client {client_id}")
            raise Exception(f"Failed to decrypt client credentials. The encryption key may have changed. Please delete and recreate this client.")

        # Create Acumatica client
        acumatica_client = AcumaticaClient(
            base_url=client.base_url,
            username=username,
            password=password,
            tenant=client.tenant,
            branch=client.branch,
            endpoint_name=client.endpoint_name,
            endpoint_version=client.endpoint_version,
            locale=client.locale,
            verify_ssl=client.verify_ssl,
            persistent_login=client.persistent_login,
            retry_on_idle_logout=client.retry_on_idle_logout,
            timeout=client.timeout,
            rate_limit_calls_per_second=client.rate_limit_calls_per_second,
        )

        # Login
        try:
            acumatica_client.login()
            logger.info(f"Successfully logged in to client {client_id}")
        except Exception as e:
            logger.error(f"Failed to login to client {client_id}: {e}")
            raise

        return acumatica_client

    def disconnect(self, client_id: str) -> bool:
        """
        Disconnect and remove a client from the pool.

        Args:
            client_id: UUID of the client

        Returns:
            True if disconnected, False if not in pool
        """
        with self._global_lock:
            if client_id not in self._connections:
                return False

            acumatica_client, _ = self._connections[client_id]

            try:
                acumatica_client.logout()
                logger.info(f"Logged out client {client_id}")
            except Exception as e:
                logger.warning(f"Error logging out client {client_id}: {e}")

            # Remove from pool
            del self._connections[client_id]

            return True

    def disconnect_all(self):
        """Disconnect all clients in the pool."""
        with self._global_lock:
            client_ids = list(self._connections.keys())

        for client_id in client_ids:
            try:
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error disconnecting client {client_id}: {e}")

    def get_pool_status(self) -> dict:
        """
        Get status information about the connection pool.

        Returns:
            Dict with pool statistics
        """
        with self._global_lock:
            return {
                'active_connections': len(self._connections),
                'client_ids': list(self._connections.keys()),
                'connections': [
                    {
                        'client_id': client_id,
                        'last_used': last_used.isoformat(),
                        'age_minutes': (datetime.now(timezone.utc) - last_used).total_seconds() / 60
                    }
                    for client_id, (_, last_used) in self._connections.items()
                ]
            }

    def refresh_connection(self, client_id: str) -> AcumaticaClient:
        """
        Force refresh a connection (disconnect and reconnect).

        Args:
            client_id: UUID of the client

        Returns:
            New AcumaticaClient instance
        """
        self.disconnect(client_id)
        return self.get_connection(client_id)


# Global singleton instance
_connection_pool = None


def get_connection_pool() -> ConnectionPool:
    """
    Get the global connection pool instance.

    Returns:
        ConnectionPool singleton
    """
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = ConnectionPool()
    return _connection_pool


def init_connection_pool():
    """Initialize the connection pool (called on app startup)."""
    global _connection_pool
    _connection_pool = ConnectionPool()
    logger.info("Connection pool initialized")
    return _connection_pool
