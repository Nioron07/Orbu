"""
Utility functions for the Orbu backend
"""

from flask import session
from easy_acumatica import AcumaticaClient
import logging

logger = logging.getLogger(__name__)


def get_client_from_session(client_id):
    """
    Get an active AcumaticaClient instance from session.

    Args:
        client_id: UUID of the client

    Returns:
        AcumaticaClient instance or None
    """
    session_key = f'client_{client_id}'
    return session.get(session_key)


def store_client_in_session(client_id, acumatica_client):
    """
    Store an AcumaticaClient instance in session.

    Args:
        client_id: UUID of the client
        acumatica_client: AcumaticaClient instance
    """
    session_key = f'client_{client_id}'
    session[session_key] = acumatica_client
    session['active_client_id'] = str(client_id)


def remove_client_from_session(client_id):
    """
    Remove an AcumaticaClient instance from session.

    Args:
        client_id: UUID of the client
    """
    session_key = f'client_{client_id}'
    if session_key in session:
        client = session[session_key]
        try:
            # Try to logout if client has that method
            if hasattr(client, 'logout'):
                client.logout()
        except Exception as e:
            logger.warning(f"Failed to logout client: {e}")

        del session[session_key]

    # Clear active client if it matches
    if session.get('active_client_id') == str(client_id):
        session.pop('active_client_id', None)


def get_active_client():
    """
    Get the currently active client from session.

    Returns:
        Tuple of (client_id, AcumaticaClient) or (None, None)
    """
    client_id = session.get('active_client_id')
    if not client_id:
        return None, None

    client = get_client_from_session(client_id)
    return client_id, client


def clear_all_clients():
    """
    Clear all client sessions.
    """
    # Find all client keys in session
    client_keys = [key for key in session.keys() if key.startswith('client_')]

    for key in client_keys:
        client = session[key]
        try:
            if hasattr(client, 'logout'):
                client.logout()
        except Exception as e:
            logger.warning(f"Failed to logout client: {e}")
        del session[key]

    # Clear active client
    session.pop('active_client_id', None)