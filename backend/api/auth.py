"""
Authentication API endpoints.
Handles user authentication, registration, and user management.
"""

import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, g
import logging

from database import db
from models import User

logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', os.getenv('SECRET_KEY', 'dev-secret-key-change-me'))
ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRES = timedelta(days=7)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_access_token(user_id: str) -> str:
    """Create a JWT access token."""
    payload = {
        'sub': user_id,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + ACCESS_TOKEN_EXPIRES,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token."""
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + REFRESH_TOKEN_EXPIRES,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    return jwt.decode(token, JWT_SECRET, algorithms=['HS256'])


def require_auth(f):
    """Decorator to require authentication for an endpoint."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'Missing authorization header'
            }), 401

        try:
            # Extract token from "Bearer <token>"
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                return jsonify({
                    'success': False,
                    'error': 'Invalid authorization header format'
                }), 401

            token = parts[1]
            payload = decode_token(token)

            if payload.get('type') != 'access':
                return jsonify({
                    'success': False,
                    'error': 'Invalid token type'
                }), 401

            # Get user from database
            user = User.query.get(payload['sub'])
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 401

            if not user.is_approved:
                return jsonify({
                    'success': False,
                    'error': 'Account pending approval'
                }), 403

            if not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'Account has been deactivated'
                }), 403

            # Store user in g for access in route
            g.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid token: {str(e)}'
            }), 401

        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator to require admin privileges for an endpoint."""
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({
                'success': False,
                'error': 'Admin privileges required'
            }), 403
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login with email and password.

    Request Body:
        {
            "email": "user@example.com",
            "password": "password123"
        }

    Returns:
        JSON with access_token, refresh_token, and user info
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body required'
            }), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password required'
            }), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user or not verify_password(password, user.password_hash):
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401

        # Check if user is approved
        if not user.is_approved:
            return jsonify({
                'success': False,
                'error': 'Account pending approval'
            }), 403

        # Check if user is active
        if not user.is_active:
            return jsonify({
                'success': False,
                'error': 'Account has been deactivated'
            }), 403

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        db.session.commit()

        # Generate tokens
        access_token = create_access_token(str(user.id))
        refresh_token = create_refresh_token(str(user.id))

        return jsonify({
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout (client should discard tokens).

    Returns:
        JSON success response
    """
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token.

    Request Body:
        {
            "refresh_token": "..."
        }

    Returns:
        JSON with new access_token
    """
    try:
        data = request.get_json()

        if not data or 'refresh_token' not in data:
            return jsonify({
                'success': False,
                'error': 'Refresh token required'
            }), 400

        try:
            payload = decode_token(data['refresh_token'])

            if payload.get('type') != 'refresh':
                return jsonify({
                    'success': False,
                    'error': 'Invalid token type'
                }), 401

            # Get user
            user = User.query.get(payload['sub'])
            if not user:
                return jsonify({
                    'success': False,
                    'error': 'User not found'
                }), 401

            if not user.is_approved or not user.is_active:
                return jsonify({
                    'success': False,
                    'error': 'Account is not active'
                }), 403

            # Generate new access token
            access_token = create_access_token(str(user.id))

            return jsonify({
                'success': True,
                'access_token': access_token
            }), 200

        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'error': 'Refresh token has expired'
            }), 401
        except jwt.InvalidTokenError as e:
            return jsonify({
                'success': False,
                'error': f'Invalid refresh token: {str(e)}'
            }), 401

    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current user info.

    Returns:
        JSON with user info
    """
    return jsonify({
        'success': True,
        'user': g.current_user.to_dict()
    }), 200


@auth_bp.route('/me/settings', methods=['GET'])
@require_auth
def get_user_settings():
    """
    Get current user's settings.

    Returns:
        JSON with user settings
    """
    return jsonify({
        'success': True,
        'settings': g.current_user.settings or {}
    }), 200


@auth_bp.route('/me/settings', methods=['PUT'])
@require_auth
def update_user_settings():
    """
    Update current user's settings.

    Request Body:
        {
            "theme": "dark",
            "autoConnectMode": "last",
            "defaultClientId": "...",
            ...
        }

    Returns:
        JSON with updated settings
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body required'
            }), 400

        # Merge with existing settings - create a NEW dict to ensure SQLAlchemy detects the change
        current_settings = dict(g.current_user.settings or {})
        current_settings.update(data)

        # Assign the new dict (SQLAlchemy needs this to detect the change to JSON column)
        g.current_user.settings = current_settings
        g.current_user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"Updated settings for user {g.current_user.email}: {current_settings}")

        return jsonify({
            'success': True,
            'settings': g.current_user.settings
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update settings error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/config', methods=['GET'])
def get_app_config():
    """
    Get public app configuration (org name, etc.).
    This endpoint does not require authentication.

    Returns:
        JSON with app configuration
    """
    org_name = os.getenv('ORG_NAME', 'Orbu')
    return jsonify({
        'success': True,
        'config': {
            'orgName': org_name,
        }
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Request a new account (pending approval).

    Request Body:
        {
            "name": "John Doe",
            "email": "user@example.com",
            "password": "password123"
        }

    Returns:
        JSON success response
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Request body required'
            }), 400

        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400

        if not email:
            return jsonify({
                'success': False,
                'error': 'Email is required'
            }), 400

        if not password:
            return jsonify({
                'success': False,
                'error': 'Password is required'
            }), 400

        # Check if email already exists
        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'An account with this email already exists'
            }), 409

        # Create user (pending approval)
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            is_admin=False,
            is_active=True,
            is_approved=False  # Requires admin approval
        )

        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registration request: {email}")

        return jsonify({
            'success': True,
            'message': 'Account request submitted. Please wait for admin approval.'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Admin endpoints

@auth_bp.route('/users', methods=['GET'])
@require_admin
def list_users():
    """
    List all users (admin only).

    Query Parameters:
        - status: Filter by status (pending, approved, deactivated)

    Returns:
        JSON with list of users
    """
    try:
        query = User.query

        status = request.args.get('status')
        if status == 'pending':
            query = query.filter_by(is_approved=False)
        elif status == 'approved':
            query = query.filter_by(is_approved=True, is_active=True)
        elif status == 'deactivated':
            query = query.filter_by(is_active=False)

        # Order by created date (newest first)
        query = query.order_by(User.created_at.desc())

        users = query.all()

        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200

    except Exception as e:
        logger.error(f"List users error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/pending', methods=['GET'])
@require_admin
def list_pending_users():
    """
    List pending user requests (admin only).

    Returns:
        JSON with list of pending users
    """
    try:
        users = User.query.filter_by(is_approved=False).order_by(User.created_at.desc()).all()

        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        }), 200

    except Exception as e:
        logger.error(f"List pending users error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<uuid:user_id>/approve', methods=['POST'])
@require_admin
def approve_user(user_id):
    """
    Approve a user request (admin only).

    Args:
        user_id: UUID of the user to approve

    Returns:
        JSON with updated user info
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        if user.is_approved:
            return jsonify({
                'success': False,
                'error': 'User is already approved'
            }), 400

        user.is_approved = True
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"User approved: {user.email}")

        return jsonify({
            'success': True,
            'message': 'User approved successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Approve user error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<uuid:user_id>/deny', methods=['POST'])
@require_admin
def deny_user(user_id):
    """
    Deny and delete a user request (admin only).

    Args:
        user_id: UUID of the user to deny

    Returns:
        JSON success response
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        if user.is_approved:
            return jsonify({
                'success': False,
                'error': 'Cannot deny an already approved user. Use delete instead.'
            }), 400

        email = user.email
        db.session.delete(user)
        db.session.commit()

        logger.info(f"User request denied and deleted: {email}")

        return jsonify({
            'success': True,
            'message': 'User request denied and deleted'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Deny user error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<uuid:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """
    Update a user (admin only).

    Args:
        user_id: UUID of the user to update

    Request Body:
        {
            "name": "New Name",
            "is_admin": true,
            "is_active": true
        }

    Returns:
        JSON with updated user info
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        data = request.get_json()

        # Prevent removing the last admin
        if 'is_admin' in data and not data['is_admin'] and user.is_admin:
            admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
            if admin_count <= 1:
                return jsonify({
                    'success': False,
                    'error': 'Cannot remove the last admin'
                }), 400

        # Prevent deactivating yourself
        if 'is_active' in data and not data['is_active']:
            if user.id == g.current_user.id:
                return jsonify({
                    'success': False,
                    'error': 'Cannot deactivate your own account'
                }), 400

        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        if 'is_admin' in data:
            user.is_admin = data['is_admin']
        if 'is_active' in data:
            user.is_active = data['is_active']

        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()

        logger.info(f"User updated: {user.email}")

        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Update user error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@auth_bp.route('/users/<uuid:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """
    Delete a user (admin only).

    Args:
        user_id: UUID of the user to delete

    Returns:
        No content on success
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404

        # Prevent deleting yourself
        if user.id == g.current_user.id:
            return jsonify({
                'success': False,
                'error': 'Cannot delete your own account'
            }), 400

        # Prevent deleting the last admin
        if user.is_admin:
            admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
            if admin_count <= 1:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete the last admin'
                }), 400

        email = user.email
        db.session.delete(user)
        db.session.commit()

        logger.info(f"User deleted: {email}")

        return '', 204

    except Exception as e:
        db.session.rollback()
        logger.error(f"Delete user error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def init_admin_user():
    """
    Initialize the admin user from environment variables.
    Called during app startup.
    """
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password_hash = os.getenv('ADMIN_PASSWORD_HASH')

    if not admin_email or not admin_password_hash:
        logger.info("No admin credentials in environment, skipping admin initialization")
        return

    # Check if admin already exists
    existing = User.query.filter_by(email=admin_email.lower()).first()
    if existing:
        logger.info(f"Admin user already exists: {admin_email}")
        return

    # Create admin user
    admin = User(
        name='Administrator',
        email=admin_email.lower(),
        password_hash=admin_password_hash,
        is_admin=True,
        is_active=True,
        is_approved=True
    )

    db.session.add(admin)
    db.session.commit()

    logger.info(f"Admin user created: {admin_email}")
