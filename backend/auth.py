"""
API Key Authentication Middleware for AcuNexus
"""

from functools import wraps
from flask import request, jsonify
from models import Client
import uuid


def require_api_key(f):
    """
    Decorator to require API key authentication for endpoint execution.

    API key should be provided in either:
    - X-API-Key header
    - Authorization: Bearer <key> header

    The decorator will:
    1. Extract the API key from headers
    2. Validate it against the database
    3. Attach the client object to request.client
    4. Return 401 if invalid or missing

    Usage:
        @app.route('/api/endpoint')
        @require_api_key
        def my_endpoint():
            client = request.client  # Access the authenticated client
            return jsonify({"message": "Success"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract API key from headers
        api_key = None

        # Check X-API-Key header
        if 'X-API-Key' in request.headers:
            api_key = request.headers.get('X-API-Key')

        # Check Authorization header (Bearer token)
        elif 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                api_key = auth_header.replace('Bearer ', '').strip()

        # No API key provided
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'Missing API key. Provide via X-API-Key header or Authorization: Bearer <key>'
            }), 401

        # Validate API key format (should be a valid UUID)
        try:
            api_key_uuid = uuid.UUID(api_key)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid API key format'
            }), 401

        # Look up client by API key
        client = Client.query.filter_by(api_key=api_key_uuid).first()

        if not client:
            return jsonify({
                'success': False,
                'error': 'Invalid API key'
            }), 401

        # Check if client is active
        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'Client is inactive'
            }), 403

        # Attach client to request for use in the endpoint function
        request.client = client

        # Call the actual endpoint function
        return f(*args, **kwargs)

    return decorated_function


def get_client_from_api_key(api_key_str):
    """
    Helper function to get a client object from an API key string.

    Args:
        api_key_str: API key as string (UUID format)

    Returns:
        Client object if valid, None otherwise
    """
    try:
        api_key_uuid = uuid.UUID(api_key_str)
        client = Client.query.filter_by(api_key=api_key_uuid).first()
        return client if client and client.is_active else None
    except (ValueError, AttributeError):
        return None
