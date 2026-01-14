"""
Updates API Blueprint

Provides endpoints for checking and applying updates.
Platform-specific deployment logic is in separate modules (gcp.py, azure.py, aws.py).
"""

from flask import Blueprint

updates_bp = Blueprint('updates', __name__, url_prefix='/api/updates')

from api.updates import routes  # noqa: E402, F401
