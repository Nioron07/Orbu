"""
GCP Cloud Run specific deployment logic.

Triggers a redeployment of the Cloud Run service by updating
an annotation, which forces Cloud Run to pull the latest image.
"""

import os
import time
import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def deploy_gcp():
    """
    Trigger Cloud Run redeployment by updating service annotations.

    This causes Cloud Run to create a new revision and pull the latest
    image from the container registry.

    Required environment variables:
        - GCP_PROJECT_ID: The GCP project ID
        - GCP_REGION: The Cloud Run region (e.g., us-central1)
        - GCP_SERVICE_NAME: The Cloud Run service name
    """
    try:
        from google.cloud import run_v2

        project = os.getenv('GCP_PROJECT_ID')
        region = os.getenv('GCP_REGION')
        service_name = os.getenv('GCP_SERVICE_NAME')

        if not all([project, region, service_name]):
            missing = []
            if not project:
                missing.append('GCP_PROJECT_ID')
            if not region:
                missing.append('GCP_REGION')
            if not service_name:
                missing.append('GCP_SERVICE_NAME')

            logger.error(f"Missing GCP configuration: {', '.join(missing)}")
            return jsonify({
                'success': False,
                'error': f'Missing GCP configuration: {", ".join(missing)}'
            }), 500

        logger.info(f"Triggering Cloud Run redeployment: {service_name} in {region}")

        client = run_v2.ServicesClient()
        service_path = f"projects/{project}/locations/{region}/services/{service_name}"

        # Get current service configuration
        service = client.get_service(name=service_path)

        # Update annotation to trigger new revision
        # This forces Cloud Run to pull the latest image
        if not service.template.annotations:
            service.template.annotations = {}

        service.template.annotations['deploy-trigger'] = str(int(time.time()))

        # Update the service (this triggers a new revision)
        operation = client.update_service(service=service)

        logger.info(f"Cloud Run redeployment triggered for {service_name}")

        return jsonify({
            'success': True,
            'message': 'Deployment started. The application will restart shortly.',
            'service': service_name,
            'region': region
        })

    except ImportError:
        logger.error("google-cloud-run package not installed")
        return jsonify({
            'success': False,
            'error': 'Cloud Run SDK not available. Please ensure google-cloud-run is installed.'
        }), 500

    except Exception as e:
        logger.error(f"Failed to trigger GCP deployment: {e}")
        return jsonify({
            'success': False,
            'error': f'Deployment failed: {str(e)}'
        }), 500
