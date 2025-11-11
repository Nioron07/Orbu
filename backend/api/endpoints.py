"""
Endpoints API Blueprint

Manages deployed endpoints for exposing Acumatica service methods as REST APIs.
"""

import logging
from flask import Blueprint, request, jsonify
from models import Endpoint, Client
from database import db
from auth import require_api_key
from services.endpoint_executor import EndpointExecutor
from services.schema_service import SchemaService
from api.clients import get_client_from_session
import uuid

logger = logging.getLogger(__name__)

# Create blueprint
endpoints_bp = Blueprint('endpoints', __name__, url_prefix='/api/v1')


# ============================================================================
# Management Endpoints (for frontend - no API key required, uses sessions)
# ============================================================================

@endpoints_bp.route('/clients/<uuid:client_id>/endpoints', methods=['GET'])
def list_client_endpoints(client_id):
    """
    List all endpoints for a specific client.

    Query params:
        - is_active: Filter by active status (true/false)
        - service_name: Filter by service name
        - method_name: Filter by method name
    """
    try:
        # Build query
        query = Endpoint.query.filter_by(client_id=client_id)

        # Apply filters
        if request.args.get('is_active'):
            is_active = request.args.get('is_active').lower() == 'true'
            query = query.filter_by(is_active=is_active)

        if request.args.get('service_name'):
            query = query.filter_by(service_name=request.args.get('service_name'))

        if request.args.get('method_name'):
            query = query.filter_by(method_name=request.args.get('method_name'))

        # Execute query
        endpoints = query.order_by(Endpoint.created_at.desc()).all()

        return jsonify({
            'success': True,
            'endpoints': [ep.to_dict() for ep in endpoints],
            'count': len(endpoints)
        })

    except Exception as e:
        logger.error(f"Error listing endpoints: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/clients/<uuid:client_id>/endpoints', methods=['POST'])
def create_endpoint(client_id):
    """
    Create a single endpoint for a client.

    Request body:
        - service_name: Name of the Acumatica service (required)
        - method_name: Name of the method (required)
        - display_name: User-friendly name (optional)
        - description: Description (optional)
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('service_name') or not data.get('method_name'):
            return jsonify({
                'success': False,
                'error': 'service_name and method_name are required'
            }), 400

        # Check if client exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        # Check if endpoint already exists
        existing = Endpoint.query.filter_by(
            client_id=client_id,
            service_name=data['service_name'],
            method_name=data['method_name']
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'error': 'Endpoint already exists for this service method'
            }), 409

        # Always generate schemas from method signature
        request_schema = {}
        response_schema = {}

        try:
            # Get client connection to introspect method
            acumatica_client = get_client_from_session(client_id)
            if acumatica_client:
                service_attr = EndpointExecutor._pascal_to_snake(data['service_name'])
                service_obj = getattr(acumatica_client, service_attr, None)

                if service_obj:
                    complete_schema = SchemaService.get_complete_schema(
                        service_obj,
                        data['method_name']
                    )
                    request_schema = complete_schema['request_schema']
                    response_schema = complete_schema['response_schema']
                else:
                    logger.warning(f"Service {data['service_name']} not found for schema generation")
            else:
                logger.warning(f"Client not connected, cannot generate schema")
        except Exception as e:
            logger.warning(f"Failed to generate schema: {e}")

        # Create endpoint
        endpoint = Endpoint(
            client_id=client_id,
            service_name=data['service_name'],
            method_name=data['method_name'],
            display_name=data.get('display_name'),
            description=data.get('description'),
            request_schema=request_schema,
            response_schema=response_schema,
            is_active=data.get('is_active', True)
        )

        db.session.add(endpoint)
        db.session.commit()

        logger.info(f"Created endpoint {endpoint.id} for {data['service_name']}.{data['method_name']}")

        return jsonify({
            'success': True,
            'endpoint': endpoint.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Error creating endpoint: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/clients/<uuid:client_id>/endpoints/batch', methods=['POST'])
def deploy_service(client_id):
    """
    Deploy all methods of a service as endpoints.

    Request body:
        - service_name: Name of the service (required)
        - methods: Optional list of specific methods to deploy (if empty, deploys all)
    """
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('service_name'):
            return jsonify({
                'success': False,
                'error': 'service_name is required'
            }), 400

        # Check if client exists and is connected
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        # Get client connection
        acumatica_client = get_client_from_session(client_id)
        if not acumatica_client:
            return jsonify({
                'success': False,
                'error': 'Client not connected. Please connect to the client first.'
            }), 400

        # Get service object
        service_attr = EndpointExecutor._pascal_to_snake(data['service_name'])
        try:
            service_obj = getattr(acumatica_client, service_attr)
        except AttributeError:
            return jsonify({
                'success': False,
                'error': f'Service {data["service_name"]} not found'
            }), 404

        # Get methods to deploy
        methods_to_deploy = data.get('methods', [])
        if not methods_to_deploy:
            # Get all public methods
            methods_to_deploy = [
                method for method in dir(service_obj)
                if not method.startswith('_') and callable(getattr(service_obj, method))
            ]

        # Deploy each method
        created_endpoints = []
        skipped_endpoints = []
        errors = []

        for method_name in methods_to_deploy:
            try:
                # Check if already exists
                existing = Endpoint.query.filter_by(
                    client_id=client_id,
                    service_name=data['service_name'],
                    method_name=method_name
                ).first()

                if existing:
                    skipped_endpoints.append({
                        'method_name': method_name,
                        'reason': 'Already exists'
                    })
                    continue

                # Always generate schemas
                request_schema = {}
                response_schema = {}

                try:
                    complete_schema = SchemaService.get_complete_schema(service_obj, method_name)
                    request_schema = complete_schema['request_schema']
                    response_schema = complete_schema['response_schema']
                except Exception as e:
                    logger.warning(f"Failed to generate schema for {method_name}: {e}")

                # Create endpoint
                endpoint = Endpoint(
                    client_id=client_id,
                    service_name=data['service_name'],
                    method_name=method_name,
                    display_name=f"{data['service_name']}.{method_name}",
                    request_schema=request_schema,
                    response_schema=response_schema,
                    is_active=True
                )

                db.session.add(endpoint)
                created_endpoints.append(method_name)

            except Exception as e:
                logger.error(f"Error deploying method {method_name}: {e}")
                errors.append({
                    'method_name': method_name,
                    'error': str(e)
                })

        # Commit all endpoints
        db.session.commit()

        logger.info(f"Deployed {len(created_endpoints)} endpoints for service {data['service_name']}")

        return jsonify({
            'success': True,
            'created': created_endpoints,
            'skipped': skipped_endpoints,
            'errors': errors,
            'summary': {
                'created_count': len(created_endpoints),
                'skipped_count': len(skipped_endpoints),
                'error_count': len(errors)
            }
        }), 201

    except Exception as e:
        logger.error(f"Error deploying service: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>', methods=['GET'])
def get_endpoint(endpoint_id):
    """Get details of a specific endpoint."""
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        # Get execution stats
        stats = EndpointExecutor.get_execution_stats(str(endpoint_id))

        response = endpoint.to_dict()
        response['stats'] = stats

        return jsonify({
            'success': True,
            'endpoint': response
        })

    except Exception as e:
        logger.error(f"Error getting endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>', methods=['PUT'])
def update_endpoint(endpoint_id):
    """
    Update an endpoint.

    Updatable fields:
        - display_name
        - description
        - request_schema
        - response_schema
    """
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        data = request.get_json()

        # Update fields
        if 'display_name' in data:
            endpoint.display_name = data['display_name']
        if 'description' in data:
            endpoint.description = data['description']
        if 'request_schema' in data:
            endpoint.request_schema = data['request_schema']
        if 'response_schema' in data:
            endpoint.response_schema = data['response_schema']

        db.session.commit()

        logger.info(f"Updated endpoint {endpoint_id}")

        return jsonify({
            'success': True,
            'endpoint': endpoint.to_dict()
        })

    except Exception as e:
        logger.error(f"Error updating endpoint: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>', methods=['DELETE'])
def delete_endpoint(endpoint_id):
    """Delete an endpoint."""
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        db.session.delete(endpoint)
        db.session.commit()

        logger.info(f"Deleted endpoint {endpoint_id}")

        return jsonify({
            'success': True,
            'message': 'Endpoint deleted successfully'
        })

    except Exception as e:
        logger.error(f"Error deleting endpoint: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>/activate', methods=['POST'])
def activate_endpoint(endpoint_id):
    """Activate an endpoint."""
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        endpoint.is_active = True
        db.session.commit()

        logger.info(f"Activated endpoint {endpoint_id}")

        return jsonify({
            'success': True,
            'endpoint': endpoint.to_dict()
        })

    except Exception as e:
        logger.error(f"Error activating endpoint: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>/deactivate', methods=['POST'])
def deactivate_endpoint(endpoint_id):
    """Deactivate an endpoint."""
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        endpoint.is_active = False
        db.session.commit()

        logger.info(f"Deactivated endpoint {endpoint_id}")

        return jsonify({
            'success': True,
            'endpoint': endpoint.to_dict()
        })

    except Exception as e:
        logger.error(f"Error deactivating endpoint: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>/logs', methods=['GET'])
def get_endpoint_logs(endpoint_id):
    """
    Get execution logs for an endpoint.

    Query params:
        - limit: Number of logs to return (default: 100, max: 1000)
    """
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        limit = min(int(request.args.get('limit', 100)), 1000)

        logs = EndpointExecutor.get_execution_logs(str(endpoint_id), limit=limit)

        return jsonify({
            'success': True,
            'logs': logs,
            'count': len(logs)
        })

    except Exception as e:
        logger.error(f"Error getting endpoint logs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@endpoints_bp.route('/endpoints/<uuid:endpoint_id>/test', methods=['POST'])
def test_endpoint(endpoint_id):
    """
    Test an endpoint with provided parameters (management UI only).

    Request body: Parameters to pass to the method
    """
    try:
        endpoint = Endpoint.query.get(endpoint_id)

        if not endpoint:
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

        request_body = request.get_json() or {}

        # Execute the endpoint
        response, status_code = EndpointExecutor.execute_endpoint(
            str(endpoint.client_id),
            endpoint.service_name,
            endpoint.method_name,
            request_body
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Error testing endpoint: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# Execution Endpoints (for external services - API key required)
# ============================================================================

@endpoints_bp.route('/endpoints/<uuid:client_id>/<service_name>/<method_name>', methods=['POST'])
@require_api_key
def execute_endpoint(client_id, service_name, method_name):
    """
    Execute a deployed endpoint (external API - requires API key).

    Headers:
        - X-API-Key: API key for the client
        OR
        - Authorization: Bearer <API key>

    Request body: JSON object with method parameters

    Response:
        {
            "success": true,
            "data": {...},
            "meta": {
                "duration_ms": 123,
                "endpoint_id": "...",
                "executed_at": "..."
            }
        }
    """
    try:
        # Get request body
        request_body = request.get_json() or {}

        # Execute the endpoint
        response, status_code = EndpointExecutor.execute_endpoint(
            str(client_id),
            service_name,
            method_name,
            request_body
        )

        return jsonify(response), status_code

    except Exception as e:
        logger.error(f"Error executing endpoint: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
