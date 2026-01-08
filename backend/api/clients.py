"""
Client management API endpoints.
Handles CRUD operations for Acumatica client configurations.

Architecture:
- Client configurations are stored in the database
- Acumatica connections are managed via a per-instance connection pool
- Connection state is tracked in the database for frontend visibility
- Each Cloud Run instance maintains its own connection pool
- Connections are created on-demand and cached for reuse
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, timezone
from easy_acumatica import AcumaticaClient
import uuid
import logging

from database import db
from models import Client, ConnectionLog, ClientMetadataCache, ServiceGroup
from encryption import get_encryption_service
from services.connection_pool import get_connection_pool

logger = logging.getLogger(__name__)

# Create blueprint
clients_bp = Blueprint('clients', __name__, url_prefix='/api/v1/clients')


def get_client_connection(client_id):
    """
    Get an Acumatica client connection from the pool.
    Creates a new connection if one doesn't exist.

    Args:
        client_id: UUID of the client

    Returns:
        AcumaticaClient instance

    Raises:
        Exception if connection fails
    """
    pool = get_connection_pool()
    return pool.get_connection(str(client_id))


def disconnect_client(client_id):
    """
    Disconnect a client from the pool.

    Args:
        client_id: UUID of the client

    Returns:
        True if disconnected, False if not in pool
    """
    pool = get_connection_pool()
    return pool.disconnect(str(client_id))


@clients_bp.route('', methods=['GET'])
def list_clients():
    """
    List all clients with optional filtering.

    Query Parameters:
        - active: Filter by active status (true/false)
        - search: Search in name and description

    Returns:
        JSON response with list of clients
    """
    try:
        # Start query
        query = Client.query

        # Apply filters
        active = request.args.get('active')
        if active is not None:
            query = query.filter_by(is_active=(active.lower() == 'true'))

        search = request.args.get('search')
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    Client.name.ilike(search_pattern),
                    Client.description.ilike(search_pattern)
                )
            )

        # Order by created date (newest first)
        query = query.order_by(Client.created_at.desc())

        # Execute query
        clients = query.all()

        # Convert to dictionary
        clients_data = [client.to_dict() for client in clients]

        return jsonify({
            'success': True,
            'clients': clients_data,
            'total': len(clients_data)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('', methods=['POST'])
def create_client():
    """
    Create a new client configuration.

    Request Body:
        JSON with client configuration including credentials

    Returns:
        JSON response with created client (without credentials)
    """
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['name', 'base_url', 'tenant', 'username', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400

        # Check if name already exists
        existing = Client.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Client with name "{data["name"]}" already exists'
            }), 409

        # Encrypt credentials
        encryption = get_encryption_service()
        encrypted_username = encryption.encrypt(data['username'])
        encrypted_password = encryption.encrypt(data['password'])

        # Create new client
        client = Client(
            name=data['name'],
            description=data.get('description'),
            base_url=data['base_url'],
            tenant=data['tenant'],
            branch=data.get('branch'),
            encrypted_username=encrypted_username,
            encrypted_password=encrypted_password,
            endpoint_name=data.get('endpoint_name'),
            endpoint_version=data.get('endpoint_version'),
            locale=data.get('locale', 'en-US'),
            verify_ssl=data.get('verify_ssl', True),
            persistent_login=data.get('persistent_login', True),
            retry_on_idle_logout=data.get('retry_on_idle_logout', True),
            timeout=data.get('timeout', 60),
            rate_limit_calls_per_second=data.get('rate_limit_calls_per_second', 10.0),
            cache_methods=data.get('cache_methods', True),
            cache_ttl_hours=data.get('cache_ttl_hours', 24),
            is_active=data.get('is_active', True)
        )

        # Save to database
        db.session.add(client)
        db.session.commit()

        # Create default service group for the client
        default_service_group = ServiceGroup(
            client_id=client.id,
            name='default',
            display_name='Default',
            description='Default service group for endpoints',
            is_active=True
        )
        db.session.add(default_service_group)
        db.session.commit()

        logger.info(f"Created client {client.id} with default service group")

        # Show full API key only on creation
        return jsonify({
            'success': True,
            'client': client.to_dict(show_full_api_key=True),
            'message': 'Client created successfully. Save the API key - it will be masked in future responses.'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>', methods=['GET'])
def get_client(client_id):
    """
    Get details of a specific client.

    Args:
        client_id: UUID of the client

    Returns:
        JSON response with client details (without credentials)
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        return jsonify({
            'success': True,
            'client': client.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>', methods=['PUT'])
def update_client(client_id):
    """
    Update a client configuration.

    Args:
        client_id: UUID of the client

    Request Body:
        JSON with fields to update

    Returns:
        JSON response with updated client
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        data = request.get_json()

        # Update allowed fields
        updatable_fields = [
            'name', 'description', 'base_url', 'tenant', 'branch',
            'endpoint_name', 'endpoint_version', 'locale',
            'verify_ssl', 'persistent_login', 'retry_on_idle_logout',
            'timeout', 'rate_limit_calls_per_second',
            'cache_methods', 'cache_ttl_hours', 'is_active'
        ]

        for field in updatable_fields:
            if field in data:
                setattr(client, field, data[field])

        # Handle credential updates separately (need encryption)
        encryption = get_encryption_service()
        credentials_changed = False
        if 'username' in data and data['username']:
            client.encrypted_username = encryption.encrypt(data['username'])
            credentials_changed = True
        if 'password' in data and data['password']:
            client.encrypted_password = encryption.encrypt(data['password'])
            credentials_changed = True

        # Update timestamp
        client.updated_at = datetime.now(timezone.utc)

        # If credentials changed, disconnect from pool to force reconnect with new credentials
        if credentials_changed:
            disconnect_client(client_id)

        # If client is being deactivated, disconnect from pool
        if 'is_active' in data and not data['is_active']:
            disconnect_client(client_id)

        db.session.commit()

        return jsonify({
            'success': True,
            'client': client.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """
    Delete a client configuration.

    Args:
        client_id: UUID of the client

    Returns:
        No content on success
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Disconnect from pool if connected
        disconnect_client(client_id)

        # Delete from database (cascade will handle related records)
        db.session.delete(client)
        db.session.commit()

        return '', 204

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/connect', methods=['POST'])
def connect_to_client(client_id):
    """
    Connect to a client (validates credentials and adds to connection pool).

    This endpoint:
    1. Validates the client exists and is active
    2. Attempts to establish an Acumatica connection
    3. Stores the connection in the pool for reuse
    4. Updates last_connected_at timestamp

    Args:
        client_id: UUID of the client

    Returns:
        JSON response with connection status
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Check if client is active
        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'This client is currently inactive. Please activate it before connecting.'
            }), 403

        logger.info(f"Connecting to client {client_id}: base_url={client.base_url}, tenant={client.tenant}")

        # Try to get/create connection via pool
        try:
            acumatica_client = get_client_connection(client_id)

            # Update last connected timestamp
            client.last_connected_at = datetime.now(timezone.utc)
            db.session.commit()

            # Log successful connection
            log = ConnectionLog(
                client_id=client_id,
                event_type='connect',
                success=True,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Connected successfully',
                'client_id': str(client_id),
                'connection_info': {
                    'url': client.base_url,
                    'tenant': client.tenant,
                    'branch': client.branch or 'Default'
                }
            }), 200

        except Exception as login_error:
            # Log failed connection
            log = ConnectionLog(
                client_id=client_id,
                event_type='connect',
                success=False,
                error_message=str(login_error),
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                'success': False,
                'error': f'Connection failed: {str(login_error)}'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/disconnect', methods=['POST'])
def disconnect_from_client(client_id):
    """
    Disconnect from a client (removes from connection pool).

    Args:
        client_id: UUID of the client

    Returns:
        JSON response confirming disconnection
    """
    try:
        # Remove from pool
        was_connected = disconnect_client(client_id)

        # Log disconnection
        log = ConnectionLog(
            client_id=client_id,
            event_type='disconnect',
            success=True,
            user_agent=request.headers.get('User-Agent'),
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Disconnected successfully' if was_connected else 'Not connected to this client'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/rebuild', methods=['POST'])
def rebuild_client(client_id):
    """
    Rebuild/refresh a client connection by invalidating cache and reconnecting.

    This will:
    1. Disconnect the current connection if any
    2. Clear any cached metadata
    3. Reconnect to force a fresh client instance

    Args:
        client_id: UUID of the client

    Returns:
        JSON response with rebuild status
    """
    try:
        # Get the client from database
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Step 1: Disconnect from pool
        was_connected = disconnect_client(client_id)

        # Step 2: Clear cached metadata (this invalidates the cache)
        ClientMetadataCache.query.filter_by(client_id=client_id).delete()
        db.session.commit()

        # Step 3: Reconnect if client is active
        if client.is_active:
            pool = get_connection_pool()
            pool.refresh_connection(str(client_id))

            # Update last connected timestamp
            client.last_connected_at = datetime.now(timezone.utc)
            db.session.commit()

            # Log the rebuild
            log = ConnectionLog(
                client_id=client_id,
                event_type='rebuild',
                success=True,
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Client rebuilt successfully',
                'was_connected': was_connected
            }), 200
        else:
            return jsonify({
                'success': True,
                'message': 'Client cache cleared (client is inactive)',
                'was_connected': was_connected
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/activate', methods=['POST'])
def activate_client(client_id):
    """
    Activate a client to make it available for connections.

    Args:
        client_id: UUID of the client

    Returns:
        JSON response confirming activation
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Set client as active
        client.is_active = True
        client.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Client activated successfully',
            'client': client.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/deactivate', methods=['POST'])
def deactivate_client(client_id):
    """
    Deactivate a client and disconnect if currently connected.

    Args:
        client_id: UUID of the client

    Returns:
        JSON response confirming deactivation
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Disconnect from pool
        was_connected = disconnect_client(client_id)

        # Set client as inactive
        client.is_active = False
        client.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Client deactivated successfully',
            'client': client.to_dict(),
            'was_connected': was_connected
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/api-key', methods=['GET'])
def get_api_key(client_id):
    """
    Get the full API key for a client (for copying purposes).

    Args:
        client_id: UUID of the client

    Returns:
        JSON response with the full API key
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        return jsonify({
            'success': True,
            'api_key': str(client.api_key)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/regenerate-api-key', methods=['POST'])
def regenerate_api_key(client_id):
    """
    Regenerate the API key for a client.

    This will invalidate the old API key and generate a new one.
    All existing deployed endpoints will continue to work with the new key.

    Args:
        client_id: UUID of the client

    Returns:
        JSON response with the new API key (shown in full, only time)
    """
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        # Generate new API key
        client.api_key = uuid.uuid4()
        client.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'API key regenerated successfully',
            'api_key': str(client.api_key),  # Show full key only on regeneration
            'warning': 'The old API key has been invalidated. Update all external services with the new key.'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/services', methods=['GET'])
def list_client_services(client_id):
    """
    List available services for a client.
    Automatically connects if not already connected.

    Args:
        client_id: UUID of the client

    Query Parameters:
        - search: Search filter for service names

    Returns:
        JSON response with list of services
    """
    try:
        # Get client from database first to validate it exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'Client is inactive. Please activate it first.'
            }), 400

        # Get connection from pool (creates if needed)
        acumatica_client = get_client_connection(client_id)

        # Check cache first
        cache_key = 'services_list'
        cache = ClientMetadataCache.query.filter_by(
            client_id=client_id,
            cache_key=cache_key
        ).first()

        if cache and not cache.is_expired():
            services = cache.cache_data
        else:
            # Get services from Acumatica (returns list of service names)
            service_names = acumatica_client.list_services()

            # Build services dict with basic info
            services = {}
            for name in service_names:
                try:
                    info = acumatica_client.get_service_info(name)
                    services[name] = info.get('methods', {})
                except Exception as e:
                    # If we can't get info, just add the name
                    services[name] = {}

            # Update cache
            if cache:
                cache.cache_data = services
                cache.cached_at = datetime.now(timezone.utc)
                cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            else:
                cache = ClientMetadataCache(
                    client_id=client_id,
                    cache_key=cache_key,
                    cache_data=services,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db.session.add(cache)
            db.session.commit()

        # Format response
        services_list = []
        for name, methods in services.items():
            services_list.append({
                'name': name,
                'methods': list(methods.keys()) if isinstance(methods, dict) else methods,
                'method_count': len(methods) if methods else 0
            })

        return jsonify({
            'success': True,
            'client_id': str(client_id),
            'services': services_list,
            'total': len(services_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/services/<service_name>', methods=['GET'])
def get_client_service_details(client_id, service_name):
    """
    Get details of a specific service for a client.
    Automatically connects if not already connected.

    Args:
        client_id: UUID of the client
        service_name: Name of the service

    Returns:
        JSON response with service details
    """
    import inspect

    try:
        # Get client from database first to validate it exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'Client is inactive. Please activate it first.'
            }), 400

        # Get connection from pool (creates if needed)
        acumatica_client = get_client_connection(client_id)

        # Get the service object directly
        # Convert PascalCase service name to snake_case (no pluralization in 0.5.6+)
        service_attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in service_name]).lstrip('_')

        try:
            service = getattr(acumatica_client, service_attr_name)
        except AttributeError:
            return jsonify({
                'success': False,
                'error': f'Service {service_name} not found (tried attribute: {service_attr_name})'
            }), 404

        # Get service methods with signatures using new get_signature method
        methods = []
        for method_name in dir(service):
            if not method_name.startswith('_') and method_name != 'get_signature':
                try:
                    method = getattr(service, method_name)
                    if callable(method):
                        # Try using the new get_signature method from easy-acumatica 0.5.5
                        signature_str = None
                        try:
                            if hasattr(service, 'get_signature'):
                                signature_str = service.get_signature(method_name)
                                logger.info(f"Got signature for {method_name}: {signature_str} (type: {type(signature_str)})")
                        except (ValueError, AttributeError) as e:
                            # Method doesn't have a signature in the registry
                            logger.debug(f"No signature for {method_name}: {e}")
                            pass

                        # Build method info
                        method_info = {
                            'name': method_name,
                            'signature': signature_str,
                            'docstring': method.__doc__ if method.__doc__ else None
                        }

                        # If we don't have a signature string, try inspect as fallback
                        if not signature_str:
                            try:
                                sig = inspect.signature(method)
                                params = []
                                for param_name, param in sig.parameters.items():
                                    if param_name != 'self':
                                        param_info = {
                                            'name': param_name,
                                            'required': param.default == inspect.Parameter.empty
                                        }
                                        if param.annotation != inspect.Parameter.empty:
                                            param_info['type'] = str(param.annotation)
                                        params.append(param_info)
                                method_info['parameters'] = params
                            except:
                                method_info['parameters'] = []

                        methods.append(method_info)
                except:
                    pass

        return jsonify({
            'success': True,
            'client_id': str(client_id),
            'service': {
                'name': service_name,
                'methods': methods,
                'total_methods': len(methods),
                'url': f"/entity/{service_name}" if hasattr(service, 'get_entity') else None
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to get service details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/models', methods=['GET'])
def list_client_models(client_id):
    """
    List available models for a client.
    Automatically connects if not already connected.

    Args:
        client_id: UUID of the client

    Query Parameters:
        - search: Search filter for model names

    Returns:
        JSON response with list of models
    """
    try:
        # Get client from database first to validate it exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'Client is inactive. Please activate it first.'
            }), 400

        # Get connection from pool (creates if needed)
        acumatica_client = get_client_connection(client_id)

        # Check cache first
        cache_key = 'models_list'
        cache = ClientMetadataCache.query.filter_by(
            client_id=client_id,
            cache_key=cache_key
        ).first()

        if cache and not cache.is_expired():
            models = cache.cache_data
        else:
            # Get models from Acumatica (returns list of model names)
            model_names = acumatica_client.list_models()

            # Build models dict with basic info
            models = {}
            for name in model_names:
                try:
                    info = acumatica_client.get_model_info(name)
                    models[name] = info.get('fields', {})
                except Exception as e:
                    # If we can't get info, just add the name
                    models[name] = {}

            # Update cache
            if cache:
                cache.cache_data = models
                cache.cached_at = datetime.now(timezone.utc)
                cache.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            else:
                cache = ClientMetadataCache(
                    client_id=client_id,
                    cache_key=cache_key,
                    cache_data=models,
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
                )
                db.session.add(cache)
            db.session.commit()

        # Format response
        models_list = []
        for name, fields in models.items():
            models_list.append({
                'name': name,
                'field_count': len(fields) if fields else 0
            })

        return jsonify({
            'success': True,
            'client_id': str(client_id),
            'models': models_list,
            'total': len(models_list)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@clients_bp.route('/<uuid:client_id>/models/<model_name>', methods=['GET'])
def get_client_model_details(client_id, model_name):
    """
    Get details of a specific model for a client.
    Automatically connects if not already connected.

    Args:
        client_id: UUID of the client
        model_name: Name of the model

    Returns:
        JSON response with model details
    """
    try:
        # Get client from database first to validate it exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404

        if not client.is_active:
            return jsonify({
                'success': False,
                'error': 'Client is inactive. Please activate it first.'
            }), 400

        # Get connection from pool (creates if needed)
        acumatica_client = get_client_connection(client_id)

        # Get the model class directly
        try:
            if hasattr(acumatica_client, 'models'):
                model_class = getattr(acumatica_client.models, model_name)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Models not available'
                }), 404
        except AttributeError:
            return jsonify({
                'success': False,
                'error': f'Model {model_name} not found'
            }), 404

        # Get model fields (for backward compatibility)
        fields = []
        if hasattr(model_class, '__dataclass_fields__'):
            for field_name, field_obj in model_class.__dataclass_fields__.items():
                field_info = {
                    'name': field_name,
                    'type': str(field_obj.type) if field_obj.type else 'Any',
                    'required': field_obj.default is None and field_obj.default_factory is None
                }

                # Add metadata if available
                if hasattr(field_obj, 'metadata') and field_obj.metadata:
                    if 'description' in field_obj.metadata:
                        field_info['description'] = field_obj.metadata['description']
                    if 'max_length' in field_obj.metadata:
                        field_info['max_length'] = field_obj.metadata['max_length']

                fields.append(field_info)

        # Try to get schema using the new get_schema method from easy-acumatica 0.5.5
        schema = None
        try:
            if hasattr(model_class, 'get_schema'):
                schema = model_class.get_schema()
        except (AttributeError, Exception) as e:
            logger.warning(f"Could not get schema for model {model_name}: {e}")

        return jsonify({
            'success': True,
            'client_id': str(client_id),
            'model': {
                'name': model_name,
                'fields': fields,
                'field_count': len(fields),
                'schema': schema,  # New schema from get_schema()
                'description': model_class.__doc__ if hasattr(model_class, '__doc__') and model_class.__doc__ else None
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to get model details: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
