"""
Endpoint Executor Service

Handles execution of deployed endpoints, including:
- Connection management
- Method invocation
- Response formatting
- Error handling
- Execution logging
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from flask import request
from models import Endpoint, EndpointExecution, Client, ServiceGroup
from database import db
from services.connection_pool import get_connection_pool

logger = logging.getLogger(__name__)


class EndpointExecutor:
    """Service for executing deployed endpoints."""

    @staticmethod
    def execute_endpoint(
        client_id: str,
        service_group_name: str,
        service_name: str,
        method_name: str,
        request_body: Dict[str, Any]
    ) -> tuple[Dict[str, Any], int]:
        """
        Execute a deployed endpoint.

        Args:
            client_id: UUID of the client
            service_group_name: Name of the service group (URL slug)
            service_name: Name of the Acumatica service
            method_name: Name of the method to execute
            request_body: Request parameters from the POST body

        Returns:
            Tuple of (response_dict, http_status_code)
        """
        start_time = time.time()
        endpoint = None
        execution_log = None

        try:
            # Find the service group first
            service_group = ServiceGroup.query.filter_by(
                client_id=client_id,
                name=service_group_name
            ).first()

            if not service_group:
                return {
                    'success': False,
                    'error': f'Service group not found: {service_group_name}'
                }, 404

            # Check if service group is active
            if not service_group.is_active:
                return {
                    'success': False,
                    'error': 'Service group is inactive'
                }, 403

            # Find the endpoint within the service group
            endpoint = Endpoint.query.filter_by(
                service_group_id=service_group.id,
                service_name=service_name,
                method_name=method_name
            ).first()

            if not endpoint:
                return {
                    'success': False,
                    'error': f'Endpoint not found: {service_name}.{method_name}'
                }, 404

            # Check if endpoint is active
            if not endpoint.is_active:
                return {
                    'success': False,
                    'error': 'Endpoint is inactive'
                }, 403

            # Get connection from pool
            connection_pool = get_connection_pool()
            acumatica_client = connection_pool.get_connection(str(client_id))

            # Convert service name from PascalCase to snake_case for attribute access
            service_attr_name = EndpointExecutor._pascal_to_snake(service_name)

            # Get the service object
            try:
                service_obj = getattr(acumatica_client, service_attr_name)
            except AttributeError:
                return {
                    'success': False,
                    'error': f'Service not found: {service_name}'
                }, 404

            # Get the method
            try:
                method = getattr(service_obj, method_name)
            except AttributeError:
                return {
                    'success': False,
                    'error': f'Method not found: {service_name}.{method_name}'
                }, 404

            # Execute the method with parameters from request body
            try:
                result = method(**request_body)
            except TypeError as e:
                return {
                    'success': False,
                    'error': f'Invalid parameters: {str(e)}'
                }, 400
            except Exception as e:
                logger.error(f"Error executing {service_name}.{method_name}: {e}", exc_info=True)
                return {
                    'success': False,
                    'error': f'Execution error: {str(e)}'
                }, 500

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Create execution log
            execution_log = EndpointExecution(
                endpoint_id=endpoint.id,
                executed_at=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                status_code=200,
                request_method=request.method,
                request_path=request.path,
                ip_address=EndpointExecutor._get_client_ip(),
                user_agent=request.headers.get('User-Agent'),
                request_data=request_body,
                response_data=result if isinstance(result, dict) else {'result': str(result)}
            )
            db.session.add(execution_log)
            db.session.commit()

            # Format response
            response = {
                'success': True,
                'data': result,
                'meta': {
                    'duration_ms': duration_ms,
                    'endpoint_id': str(endpoint.id),
                    'executed_at': datetime.now(timezone.utc).isoformat()
                }
            }

            return response, 200

        except Exception as e:
            logger.error(f"Unexpected error executing endpoint: {e}", exc_info=True)

            # Log failed execution
            if endpoint:
                duration_ms = int((time.time() - start_time) * 1000)
                execution_log = EndpointExecution(
                    endpoint_id=endpoint.id,
                    executed_at=datetime.now(timezone.utc),
                    duration_ms=duration_ms,
                    status_code=500,
                    error_message=str(e),
                    request_method=request.method,
                    request_path=request.path,
                    ip_address=EndpointExecutor._get_client_ip(),
                    user_agent=request.headers.get('User-Agent'),
                    request_data=request_body
                )
                db.session.add(execution_log)
                db.session.commit()

            return {
                'success': False,
                'error': str(e)
            }, 500

    @staticmethod
    def _pascal_to_snake(name: str) -> str:
        """
        Convert PascalCase to snake_case.

        Args:
            name: PascalCase string

        Returns:
            snake_case string
        """
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('_')
            result.append(char.lower())
        return ''.join(result)

    @staticmethod
    def _get_client_ip() -> Optional[str]:
        """
        Get the client's IP address from the request.

        Returns:
            IP address string or None
        """
        # Check for proxy headers first
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr

    @staticmethod
    def get_execution_logs(endpoint_id: str, limit: int = 100) -> list:
        """
        Get execution logs for an endpoint.

        Args:
            endpoint_id: UUID of the endpoint
            limit: Maximum number of logs to return

        Returns:
            List of execution log dicts
        """
        logs = EndpointExecution.query.filter_by(endpoint_id=endpoint_id)\
            .order_by(EndpointExecution.executed_at.desc())\
            .limit(limit)\
            .all()

        return [log.to_dict() for log in logs]

    @staticmethod
    def get_execution_stats(endpoint_id: str) -> Dict[str, Any]:
        """
        Get statistics for an endpoint's executions.

        Args:
            endpoint_id: UUID of the endpoint

        Returns:
            Dict with statistics
        """
        from sqlalchemy import func

        stats = db.session.query(
            func.count(EndpointExecution.id).label('total_executions'),
            func.avg(EndpointExecution.duration_ms).label('avg_duration_ms'),
            func.min(EndpointExecution.duration_ms).label('min_duration_ms'),
            func.max(EndpointExecution.duration_ms).label('max_duration_ms'),
            func.sum(func.cast(EndpointExecution.status_code == 200, db.Integer)).label('successful'),
            func.sum(func.cast(EndpointExecution.status_code != 200, db.Integer)).label('failed'),
        ).filter_by(endpoint_id=endpoint_id).first()

        return {
            'total_executions': stats.total_executions or 0,
            'avg_duration_ms': int(stats.avg_duration_ms) if stats.avg_duration_ms else 0,
            'min_duration_ms': stats.min_duration_ms or 0,
            'max_duration_ms': stats.max_duration_ms or 0,
            'successful': stats.successful or 0,
            'failed': stats.failed or 0,
            'success_rate': (stats.successful / stats.total_executions * 100)
                if stats.total_executions else 0
        }
