"""
Log cleanup service for automatically deleting old endpoint execution logs.
Respects per-endpoint retention settings.
"""

import logging
from datetime import datetime, timedelta, timezone
from database import db
from models import Endpoint, EndpointExecution

logger = logging.getLogger(__name__)


class LogCleanupService:
    """Service to clean up old endpoint execution logs based on retention policies."""

    @staticmethod
    def cleanup_old_logs():
        """
        Delete endpoint execution logs older than their retention period.

        This method:
        1. Fetches all endpoints with their retention settings
        2. For each endpoint, deletes logs older than the retention period
        3. Returns statistics about cleanup

        Returns:
            dict: Statistics about deleted logs
        """
        try:
            total_deleted = 0
            endpoints_processed = 0

            # Get all endpoints
            endpoints = Endpoint.query.all()

            for endpoint in endpoints:
                # Calculate cutoff time based on retention hours
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=endpoint.log_retention_hours)

                # Count logs to be deleted for this endpoint
                logs_to_delete = EndpointExecution.query.filter(
                    EndpointExecution.endpoint_id == endpoint.id,
                    EndpointExecution.executed_at < cutoff_time
                ).count()

                if logs_to_delete > 0:
                    # Delete old logs
                    EndpointExecution.query.filter(
                        EndpointExecution.endpoint_id == endpoint.id,
                        EndpointExecution.executed_at < cutoff_time
                    ).delete()

                    total_deleted += logs_to_delete
                    endpoints_processed += 1

                    logger.info(f"Deleted {logs_to_delete} logs for endpoint {endpoint.id} (retention: {endpoint.log_retention_hours}h)")

            # Commit the deletions
            db.session.commit()

            logger.info(f"Log cleanup completed: {total_deleted} logs deleted across {endpoints_processed} endpoints")

            return {
                'success': True,
                'total_deleted': total_deleted,
                'endpoints_processed': endpoints_processed
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error during log cleanup: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def cleanup_logs_for_endpoint(endpoint_id: str):
        """
        Delete old logs for a specific endpoint.

        Args:
            endpoint_id: UUID of the endpoint

        Returns:
            dict: Statistics about deleted logs
        """
        try:
            endpoint = Endpoint.query.get(endpoint_id)
            if not endpoint:
                return {
                    'success': False,
                    'error': 'Endpoint not found'
                }

            # Calculate cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=endpoint.log_retention_hours)

            # Delete old logs
            deleted_count = EndpointExecution.query.filter(
                EndpointExecution.endpoint_id == endpoint_id,
                EndpointExecution.executed_at < cutoff_time
            ).delete()

            db.session.commit()

            logger.info(f"Deleted {deleted_count} logs for endpoint {endpoint_id}")

            return {
                'success': True,
                'deleted_count': deleted_count
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error cleaning up logs for endpoint {endpoint_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


# Global instance
log_cleanup_service = LogCleanupService()
