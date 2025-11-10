"""
Database models for AcuNexus.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from database import db


class Client(db.Model):
    """
    Represents an Acumatica client configuration.
    Each client is a connection to a specific Acumatica instance.
    """
    __tablename__ = 'clients'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)

    # Connection details
    base_url = Column(String(500), nullable=False)
    tenant = Column(String(100), nullable=False)
    branch = Column(String(100))

    # Encrypted credentials (will be encrypted before storage)
    encrypted_username = Column(Text, nullable=False)
    encrypted_password = Column(Text, nullable=False)

    # API configuration
    endpoint_name = Column(String(100), default='Default')
    endpoint_version = Column(String(50))
    locale = Column(String(10), default='en-US')

    # Connection options
    verify_ssl = Column(Boolean, default=True)
    persistent_login = Column(Boolean, default=True)
    retry_on_idle_logout = Column(Boolean, default=True)
    timeout = Column(Integer, default=60)
    rate_limit_calls_per_second = Column(Float, default=10.0)

    # Caching options
    cache_methods = Column(Boolean, default=True)
    cache_ttl_hours = Column(Integer, default=24)

    # Status and metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_connected_at = Column(DateTime(timezone=True))

    def to_dict(self, include_sensitive=False):
        """
        Convert client to dictionary for API responses.

        Args:
            include_sensitive: Whether to include sensitive data (never include passwords)

        Returns:
            dict: Client data as dictionary
        """
        data = {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'base_url': self.base_url,
            'tenant': self.tenant,
            'branch': self.branch,
            'endpoint_name': self.endpoint_name,
            'endpoint_version': self.endpoint_version,
            'locale': self.locale,
            'verify_ssl': self.verify_ssl,
            'persistent_login': self.persistent_login,
            'retry_on_idle_logout': self.retry_on_idle_logout,
            'timeout': self.timeout,
            'rate_limit_calls_per_second': self.rate_limit_calls_per_second,
            'cache_methods': self.cache_methods,
            'cache_ttl_hours': self.cache_ttl_hours,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_connected_at': self.last_connected_at.isoformat() if self.last_connected_at else None,
        }

        # Never return encrypted passwords
        # Username could be included if needed for display purposes
        if include_sensitive:
            # We'll decrypt username for display (but never password)
            # This will be handled by the encryption service
            pass

        return data

    def __repr__(self):
        return f'<Client {self.name}>'


class ClientMetadataCache(db.Model):
    """
    Caches expensive metadata queries per client to improve performance.
    """
    __tablename__ = 'client_metadata_cache'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to client
    client_id = Column(UUID(as_uuid=True), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)

    # Cache data
    cache_key = Column(String(100), nullable=False)  # e.g., 'services_list', 'models_list'
    cache_data = Column(JSON, nullable=False)  # Stored as JSON
    cached_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True))

    # Relationship
    client = db.relationship('Client', backref=db.backref('metadata_cache', lazy='dynamic', cascade='all, delete-orphan'))

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('client_id', 'cache_key', name='unique_client_cache_key'),
    )

    def is_expired(self):
        """Check if cache entry is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self):
        return f'<ClientMetadataCache {self.cache_key} for client {self.client_id}>'


class ConnectionLog(db.Model):
    """
    Tracks connection attempts and usage for auditing and debugging.
    """
    __tablename__ = 'connection_logs'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to client
    client_id = Column(UUID(as_uuid=True), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)

    # Log data
    event_type = Column(String(50), nullable=False)  # 'connect', 'disconnect', 'error', 'test'
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    session_info = Column(JSON)  # Additional session data if needed
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationship
    client = db.relationship('Client', backref=db.backref('connection_logs', lazy='dynamic', cascade='all, delete-orphan'))

    def to_dict(self):
        """Convert log entry to dictionary."""
        return {
            'id': str(self.id),
            'client_id': str(self.client_id),
            'event_type': self.event_type,
            'success': self.success,
            'error_message': self.error_message,
            'user_agent': self.user_agent,
            'ip_address': self.ip_address,
            'session_info': self.session_info,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f'<ConnectionLog {self.event_type} for client {self.client_id}>'