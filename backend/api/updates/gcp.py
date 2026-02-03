"""
GCP Cloud Run deployment with Cloud Build integration.

Triggers a full build pipeline:
1. Clone the specific release tag from GitHub
2. Build the Docker image using Cloud Build
3. Push the image to GCR
4. Deploy the new image to Cloud Run
"""

import os
import logging
from flask import jsonify, request

logger = logging.getLogger(__name__)

GITHUB_REPO = "Nioron07/Orbu"

# Valid Cloud Build machine types
VALID_MACHINE_TYPES = [
    'UNSPECIFIED',
    'N1_HIGHCPU_8',
    'N1_HIGHCPU_32',
    'E2_HIGHCPU_8',
    'E2_HIGHCPU_32',
    'E2_MEDIUM',
]


def get_cloudbuild_config(version: str, project_id: str, service_name: str, machine_type: str = 'E2_HIGHCPU_8') -> dict:
    """Generate Cloud Build configuration for building from GitHub release."""
    if machine_type not in VALID_MACHINE_TYPES:
        machine_type = 'E2_HIGHCPU_8'

    return {
        'steps': [
            # Clone the specific release tag from GitHub
            {
                'name': 'gcr.io/cloud-builders/git',
                'args': ['clone', '--depth', '1', '--branch', f'v{version}',
                         f'https://github.com/{GITHUB_REPO}.git', '.']
            },
            # Build Docker image with both versioned and latest tags
            {
                'name': 'gcr.io/cloud-builders/docker',
                'args': ['build', '-t', f'gcr.io/{project_id}/{service_name}:v{version}',
                         '-t', f'gcr.io/{project_id}/{service_name}:latest', '.']
            },
            # Push both tags
            {
                'name': 'gcr.io/cloud-builders/docker',
                'args': ['push', '--all-tags', f'gcr.io/{project_id}/{service_name}']
            },
        ],
        'images': [
            f'gcr.io/{project_id}/{service_name}:v{version}',
            f'gcr.io/{project_id}/{service_name}:latest'
        ],
        'timeout': '1800s',  # 30 minute timeout
        'options': {
            'machine_type': machine_type,
            'logging': 'CLOUD_LOGGING_ONLY'
        }
    }


def trigger_build(version: str, machine_type: str = 'E2_HIGHCPU_8') -> tuple:
    """
    Trigger Cloud Build to build new image from GitHub release.

    Args:
        version: The version tag to build (without 'v' prefix)
        machine_type: Cloud Build machine type

    Returns:
        Tuple of (build_id, logs_url)
    """
    from google.cloud.devtools import cloudbuild_v1

    project = os.getenv('GCP_PROJECT_ID')
    service_name = os.getenv('GCP_SERVICE_NAME')

    if not project or not service_name:
        raise ValueError("Missing GCP_PROJECT_ID or GCP_SERVICE_NAME environment variable")

    client = cloudbuild_v1.CloudBuildClient()

    build_config = get_cloudbuild_config(version, project, service_name, machine_type)
    build = cloudbuild_v1.Build(build_config)

    operation = client.create_build(project_id=project, build=build)
    build_result = operation.metadata.build

    logs_url = f"https://console.cloud.google.com/cloud-build/builds/{build_result.id}?project={project}"

    logger.info(f"Triggered Cloud Build {build_result.id} for version {version}")

    return build_result.id, logs_url


def get_build_status(build_id: str) -> dict:
    """
    Get the status of a Cloud Build job.

    Args:
        build_id: The Cloud Build job ID

    Returns:
        Dict with status, step, and logs_url
    """
    from google.cloud.devtools import cloudbuild_v1

    project = os.getenv('GCP_PROJECT_ID')

    if not project:
        raise ValueError("Missing GCP_PROJECT_ID environment variable")

    client = cloudbuild_v1.CloudBuildClient()
    build = client.get_build(project_id=project, id=build_id)

    status_map = {
        cloudbuild_v1.Build.Status.STATUS_UNKNOWN: 'UNKNOWN',
        cloudbuild_v1.Build.Status.PENDING: 'QUEUED',
        cloudbuild_v1.Build.Status.QUEUED: 'QUEUED',
        cloudbuild_v1.Build.Status.WORKING: 'WORKING',
        cloudbuild_v1.Build.Status.SUCCESS: 'SUCCESS',
        cloudbuild_v1.Build.Status.FAILURE: 'FAILURE',
        cloudbuild_v1.Build.Status.CANCELLED: 'CANCELLED',
        cloudbuild_v1.Build.Status.TIMEOUT: 'TIMEOUT',
    }

    step = "Initializing..."
    if build.status in (cloudbuild_v1.Build.Status.PENDING, cloudbuild_v1.Build.Status.QUEUED):
        step = "Queued, waiting for build worker..."
    elif build.status == cloudbuild_v1.Build.Status.WORKING:
        step = "Building..."
    elif build.status == cloudbuild_v1.Build.Status.SUCCESS:
        step = "Build complete, deploying..."
    elif build.status == cloudbuild_v1.Build.Status.FAILURE:
        step = "Build failed"
    elif build.status == cloudbuild_v1.Build.Status.CANCELLED:
        step = "Build cancelled"
    elif build.status == cloudbuild_v1.Build.Status.TIMEOUT:
        step = "Build timed out"

    return {
        'status': status_map.get(build.status, 'UNKNOWN'),
        'step': step,
        'logs_url': build.log_url or f"https://console.cloud.google.com/cloud-build/builds/{build_id}?project={project}"
    }


def deploy_new_image(version: str):
    """
    Update Cloud Run to use the newly built image.

    Args:
        version: The version to deploy (without 'v' prefix)
    """
    from google.cloud import run_v2

    project = os.getenv('GCP_PROJECT_ID')
    region = os.getenv('GCP_REGION')
    service_name = os.getenv('GCP_SERVICE_NAME')

    if not all([project, region, service_name]):
        raise ValueError("Missing GCP configuration environment variables")

    client = run_v2.ServicesClient()
    service_path = f"projects/{project}/locations/{region}/services/{service_name}"

    service = client.get_service(name=service_path)

    # Update to use the new versioned image
    new_image = f"gcr.io/{project}/{service_name}:v{version}"
    service.template.containers[0].image = new_image

    # Update ORBU_VERSION env var
    for env_var in service.template.containers[0].env:
        if env_var.name == 'ORBU_VERSION':
            env_var.value = version
            break

    client.update_service(service=service)
    logger.info(f"Deployed new image {new_image} to Cloud Run")


def deploy_gcp():
    """
    Trigger full Cloud Build + Deploy pipeline.

    This is called from the /api/updates/deploy endpoint.
    It fetches the latest release from GitHub, triggers a Cloud Build
    to build the new image, and returns the build ID for status polling.
    """
    try:
        import requests

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

        # Get latest version from GitHub
        logger.info(f"Fetching latest release from GitHub: {GITHUB_REPO}")
        response = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )

        if response.status_code == 404:
            return jsonify({
                'success': False,
                'error': 'No releases found in GitHub repository'
            }), 404

        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Failed to fetch latest release from GitHub: {response.status_code}'
            }), 500

        release_data = response.json()
        latest_version = release_data['tag_name'].lstrip('v')

        # Get machine type from request body (default: E2_HIGHCPU_8)
        data = request.get_json(silent=True) or {}
        machine_type = data.get('machine_type', 'E2_HIGHCPU_8')

        logger.info(f"Starting Cloud Build for version {latest_version} with machine {machine_type}")

        # Trigger Cloud Build
        build_id, logs_url = trigger_build(latest_version, machine_type)

        return jsonify({
            'success': True,
            'build_id': build_id,
            'version': latest_version,
            'message': 'Build started. This may take 5-10 minutes.',
            'logs_url': logs_url
        })

    except ImportError as e:
        logger.error(f"Cloud Build SDK not available: {e}")
        return jsonify({
            'success': False,
            'error': 'Cloud Build SDK not available. Please ensure google-cloud-build is installed.'
        }), 500

    except Exception as e:
        logger.error(f"Failed to trigger build: {e}")
        return jsonify({
            'success': False,
            'error': f'Build failed: {str(e)}'
        }), 500
