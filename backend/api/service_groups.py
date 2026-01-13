"""
Service Groups API Blueprint

Manages service groups for organizing endpoints within a client.
Service groups provide logical grouping of endpoints (e.g., 'Inventory App', 'Customer App').
"""

from flask import Blueprint, request, jsonify
from models import ServiceGroup, Client
from database import db
from api.auth import require_auth
import logging
import re

logger = logging.getLogger(__name__)

service_groups_bp = Blueprint('service_groups', __name__, url_prefix='/api/v1/clients')


def slugify(name):
    """Convert a name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug


def create_default_service_group(client_id):
    """
    Create a default service group for a client.
    Called automatically when a new client is created.
    """
    try:
        existing = ServiceGroup.query.filter_by(client_id=client_id, name='default').first()
        if existing:
            return existing

        service_group = ServiceGroup(
            client_id=client_id,
            name='default',
            display_name='Default',
            description='Default service group for endpoints',
            is_active=True
        )
        db.session.add(service_group)
        db.session.commit()
        logger.info(f"Created default service group for client {client_id}")
        return service_group
    except Exception as e:
        logger.error(f"Error creating default service group: {e}", exc_info=True)
        db.session.rollback()
        return None


@service_groups_bp.route('/<uuid:client_id>/service-groups', methods=['GET'])
@require_auth
def list_service_groups(client_id):
    """List all service groups for a client."""
    try:
        # Check if client exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        query = ServiceGroup.query.filter_by(client_id=client_id)

        # Filter by active status if provided
        is_active = request.args.get('is_active')
        if is_active is not None:
            query = query.filter_by(is_active=is_active.lower() == 'true')

        service_groups = query.order_by(ServiceGroup.created_at.desc()).all()

        # Include endpoint count for each service group
        result = []
        for sg in service_groups:
            sg_dict = sg.to_dict()
            sg_dict['endpoint_count'] = sg.endpoints.count()
            result.append(sg_dict)

        return jsonify({
            'success': True,
            'service_groups': result,
            'count': len(result)
        })
    except Exception as e:
        logger.error(f"Error listing service groups: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups', methods=['POST'])
@require_auth
def create_service_group(client_id):
    """Create a new service group."""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get('name'):
            return jsonify({'success': False, 'error': 'name is required'}), 400

        # Check if client exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404

        # Slugify the name for URL-safe usage
        name_slug = slugify(data['name'])

        if not name_slug:
            return jsonify({'success': False, 'error': 'Invalid name - must contain alphanumeric characters'}), 400

        # Check if name already exists for this client
        existing = ServiceGroup.query.filter_by(client_id=client_id, name=name_slug).first()
        if existing:
            return jsonify({
                'success': False,
                'error': f'Service group "{name_slug}" already exists for this client'
            }), 409

        # Create service group
        service_group = ServiceGroup(
            client_id=client_id,
            name=name_slug,
            display_name=data.get('display_name', data['name']),
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )

        db.session.add(service_group)
        db.session.commit()

        logger.info(f"Created service group {service_group.id} for client {client_id}")

        result = service_group.to_dict()
        result['endpoint_count'] = 0

        return jsonify({
            'success': True,
            'service_group': result
        }), 201
    except Exception as e:
        logger.error(f"Error creating service group: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>', methods=['GET'])
@require_auth
def get_service_group(client_id, service_group_id):
    """Get details of a specific service group."""
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        # Include endpoint count
        result = service_group.to_dict()
        result['endpoint_count'] = service_group.endpoints.count()

        return jsonify({
            'success': True,
            'service_group': result
        })
    except Exception as e:
        logger.error(f"Error getting service group: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>', methods=['PUT'])
@require_auth
def update_service_group(client_id, service_group_id):
    """Update a service group."""
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        data = request.get_json()

        # Update fields
        if 'name' in data:
            new_name = slugify(data['name'])
            if not new_name:
                return jsonify({'success': False, 'error': 'Invalid name'}), 400

            # Check for duplicate
            existing = ServiceGroup.query.filter_by(client_id=client_id, name=new_name).first()
            if existing and existing.id != service_group_id:
                return jsonify({
                    'success': False,
                    'error': f'Service group "{new_name}" already exists'
                }), 409
            service_group.name = new_name

        if 'display_name' in data:
            service_group.display_name = data['display_name']
        if 'description' in data:
            service_group.description = data['description']
        if 'is_active' in data:
            service_group.is_active = data['is_active']

        db.session.commit()

        result = service_group.to_dict()
        result['endpoint_count'] = service_group.endpoints.count()

        return jsonify({
            'success': True,
            'service_group': result
        })
    except Exception as e:
        logger.error(f"Error updating service group: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>', methods=['DELETE'])
@require_auth
def delete_service_group(client_id, service_group_id):
    """Delete a service group and all its endpoints."""
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        # Count endpoints that will be deleted
        endpoint_count = service_group.endpoints.count()

        # Prevent deletion of the last service group
        remaining_groups = ServiceGroup.query.filter_by(client_id=client_id).count()
        if remaining_groups <= 1:
            return jsonify({
                'success': False,
                'error': 'Cannot delete the last service group. At least one service group is required per client.'
            }), 400

        db.session.delete(service_group)
        db.session.commit()

        logger.info(f"Deleted service group {service_group_id} with {endpoint_count} endpoints")

        return jsonify({
            'success': True,
            'message': f'Service group deleted with {endpoint_count} endpoints'
        })
    except Exception as e:
        logger.error(f"Error deleting service group: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>/activate', methods=['POST'])
@require_auth
def activate_service_group(client_id, service_group_id):
    """Activate a service group."""
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        service_group.is_active = True
        db.session.commit()

        result = service_group.to_dict()
        result['endpoint_count'] = service_group.endpoints.count()

        return jsonify({
            'success': True,
            'service_group': result
        })
    except Exception as e:
        logger.error(f"Error activating service group: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>/deactivate', methods=['POST'])
@require_auth
def deactivate_service_group(client_id, service_group_id):
    """Deactivate a service group."""
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        service_group.is_active = False
        db.session.commit()

        result = service_group.to_dict()
        result['endpoint_count'] = service_group.endpoints.count()

        return jsonify({
            'success': True,
            'service_group': result
        })
    except Exception as e:
        logger.error(f"Error deactivating service group: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@service_groups_bp.route('/<uuid:client_id>/service-groups/<uuid:service_group_id>/deployed-methods', methods=['GET'])
@require_auth
def get_deployed_methods(client_id, service_group_id):
    """
    Get list of already deployed service/method combinations for a service group.
    Used by the frontend to filter out already-deployed methods in the deployment dialog.
    """
    try:
        service_group = ServiceGroup.query.filter_by(
            id=service_group_id,
            client_id=client_id
        ).first()

        if not service_group:
            return jsonify({'success': False, 'error': 'Service group not found'}), 404

        endpoints = service_group.endpoints.all()

        # Build a dict of service_name -> list of method_names
        deployed = {}
        for ep in endpoints:
            if ep.service_name not in deployed:
                deployed[ep.service_name] = []
            deployed[ep.service_name].append(ep.method_name)

        return jsonify({
            'success': True,
            'deployed_methods': deployed
        })
    except Exception as e:
        logger.error(f"Error getting deployed methods: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
