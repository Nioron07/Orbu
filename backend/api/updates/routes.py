"""
Update routes for version checking and deployment triggering.

Common routes that work across all platforms. Platform-specific
deployment logic is delegated to separate modules.
"""

import os
import logging
import requests
from flask import jsonify

from api.updates import updates_bp
from api.auth import require_auth, require_admin

logger = logging.getLogger(__name__)

GITHUB_REPO = "Nioron07/Orbu"
CURRENT_VERSION = os.getenv('ORBU_VERSION', '0.0.0')
CLOUD_PLATFORM = os.getenv('CLOUD_PLATFORM', 'unknown')


def compare_versions(v1: str, v2: str) -> int:
    """
    Compare semantic versions.

    Returns:
        1 if v1 > v2
        -1 if v1 < v2
        0 if equal
    """
    try:
        parts1 = [int(x) for x in v1.split('.')]
        parts2 = [int(x) for x in v2.split('.')]
        for i in range(max(len(parts1), len(parts2))):
            p1 = parts1[i] if i < len(parts1) else 0
            p2 = parts2[i] if i < len(parts2) else 0
            if p1 > p2:
                return 1
            if p1 < p2:
                return -1
        return 0
    except (ValueError, AttributeError):
        return 0


@updates_bp.route('/current', methods=['GET'])
@require_auth
def get_current_version():
    """Get current version info."""
    return jsonify({
        'success': True,
        'version': CURRENT_VERSION,
        'platform': CLOUD_PLATFORM,
        'can_auto_update': CLOUD_PLATFORM == 'gcp'
    })


@updates_bp.route('/check', methods=['GET'])
@require_auth
@require_admin
def check_for_updates():
    """Check GitHub for latest release."""
    try:
        response = requests.get(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            latest = data['tag_name'].lstrip('v')
            update_available = compare_versions(latest, CURRENT_VERSION) > 0

            logger.info(f"Update check: current={CURRENT_VERSION}, latest={latest}, available={update_available}")

            return jsonify({
                'success': True,
                'current_version': CURRENT_VERSION,
                'latest_version': latest,
                'update_available': update_available,
                'release_url': data['html_url'],
                'release_notes': data.get('body', ''),
                'platform': CLOUD_PLATFORM,
                'can_auto_update': CLOUD_PLATFORM == 'gcp'
            })
        elif response.status_code == 404:
            return jsonify({
                'success': True,
                'current_version': CURRENT_VERSION,
                'latest_version': None,
                'update_available': False,
                'release_url': None,
                'release_notes': 'No releases found',
                'platform': CLOUD_PLATFORM,
                'can_auto_update': CLOUD_PLATFORM == 'gcp'
            })
        else:
            logger.error(f"GitHub API returned status {response.status_code}")
            return jsonify({
                'success': False,
                'error': f'GitHub API returned status {response.status_code}'
            }), 500

    except requests.exceptions.Timeout:
        logger.error("Timeout while checking for updates")
        return jsonify({
            'success': False,
            'error': 'Timeout while checking for updates'
        }), 500
    except Exception as e:
        logger.error(f"Error checking for updates: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@updates_bp.route('/deploy', methods=['POST'])
@require_auth
@require_admin
def trigger_deploy():
    """Trigger platform-specific redeployment."""
    logger.info(f"Deploy triggered on platform: {CLOUD_PLATFORM}")

    if CLOUD_PLATFORM == 'gcp':
        from api.updates.gcp import deploy_gcp
        return deploy_gcp()
    elif CLOUD_PLATFORM == 'azure':
        # Future: from api.updates.azure import deploy_azure
        return jsonify({
            'success': False,
            'error': 'Azure auto-update is not yet implemented'
        }), 400
    elif CLOUD_PLATFORM == 'aws':
        # Future: from api.updates.aws import deploy_aws
        return jsonify({
            'success': False,
            'error': 'AWS auto-update is not yet implemented'
        }), 400
    else:
        return jsonify({
            'success': False,
            'error': f'Auto-update not supported for platform: {CLOUD_PLATFORM}'
        }), 400
