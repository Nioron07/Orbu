"""
Base Deployer - Abstract base class for cloud platform deployers.

Each cloud platform (GCP, Azure, AWS) implements this interface.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class DeploymentStatus(Enum):
    """Status of a deployment step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DeploymentStep:
    """Represents a single deployment step."""
    name: str
    description: str
    status: DeploymentStatus = DeploymentStatus.PENDING
    error_message: Optional[str] = None


@dataclass
class DeploymentConfig:
    """Configuration for deployment."""
    # Platform-agnostic
    platform: str  # 'gcp', 'azure', 'aws'

    # Organization
    org_name: str = ''  # Display name (e.g., "Nioron")
    org_slug: str = ''  # URL-safe slug (e.g., "nioron")

    # Database
    db_connection_method: str = ''  # 'managed', 'external'
    db_host: str = ''
    db_port: str = ''
    db_name: str = ''
    db_user: str = ''
    db_password: str = ''

    # Admin credentials
    admin_email: str = ''
    admin_password: str = ''  # Plain text, will be hashed before storage

    # Platform-specific (set by subclasses)
    platform_config: Dict[str, Any] = None

    def __post_init__(self):
        if self.platform_config is None:
            self.platform_config = {}


class BaseDeployer(ABC):
    """
    Abstract base class for cloud platform deployers.

    Each platform implements:
    - check_prerequisites() - Verify CLI tools are installed
    - get_deployment_steps() - Return list of deployment steps
    - setup_secrets() - Create secrets in the platform's secret manager
    - setup_permissions() - Configure IAM/RBAC
    - build_and_push() - Build and push Docker image
    - deploy() - Deploy to the container service
    - verify_health() - Check the deployed service is healthy
    """

    def __init__(self, progress_callback: Callable[[str, DeploymentStatus, Optional[str]], None] = None):
        """
        Initialize the deployer.

        Args:
            progress_callback: Function called with (step_name, status, message) updates
        """
        self.progress_callback = progress_callback or (lambda *args: None)
        self.config: Optional[DeploymentConfig] = None
        self.service_url: Optional[str] = None

    def update_progress(self, step_name: str, status: DeploymentStatus, message: str = None):
        """Update progress for a deployment step."""
        self.progress_callback(step_name, status, message)

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name."""
        pass

    @property
    @abstractmethod
    def platform_id(self) -> str:
        """Platform identifier (gcp, azure, aws)."""
        pass

    @abstractmethod
    def check_prerequisites(self) -> tuple[bool, list[str]]:
        """
        Check if required CLI tools are installed.

        Returns:
            Tuple of (all_ok, list_of_missing_tools)
        """
        pass

    @abstractmethod
    def check_authentication(self) -> tuple[bool, Optional[str]]:
        """
        Check if user is authenticated with the platform.

        Returns:
            Tuple of (is_authenticated, account_name_or_error)
        """
        pass

    @abstractmethod
    def get_deployment_steps(self) -> list[DeploymentStep]:
        """Return list of deployment steps for this platform."""
        pass

    @abstractmethod
    def setup_secrets(self, config: DeploymentConfig) -> bool:
        """
        Create secrets in the platform's secret manager.

        Args:
            config: Deployment configuration

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def setup_permissions(self, config: DeploymentConfig) -> bool:
        """
        Configure IAM/RBAC permissions.

        Args:
            config: Deployment configuration

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def build_and_push(self, config: DeploymentConfig, source_path: str) -> bool:
        """
        Build Docker image and push to container registry.

        Args:
            config: Deployment configuration
            source_path: Path to Orbu source code

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def deploy(self, config: DeploymentConfig) -> Optional[str]:
        """
        Deploy to the container service.

        Args:
            config: Deployment configuration

        Returns:
            Service URL if successful, None otherwise
        """
        pass

    @abstractmethod
    def verify_health(self, url: str) -> tuple[bool, str]:
        """
        Check if the deployed service is healthy.

        Args:
            url: Service URL

        Returns:
            Tuple of (is_healthy, status_message)
        """
        pass

    def run_deployment(self, config: DeploymentConfig, source_path: str) -> tuple[bool, Optional[str]]:
        """
        Run the full deployment pipeline.

        Args:
            config: Deployment configuration
            source_path: Path to Orbu source code

        Returns:
            Tuple of (success, service_url)
        """
        self.config = config

        steps = self.get_deployment_steps()

        try:
            # Step 1: Setup secrets
            self.update_progress("secrets", DeploymentStatus.IN_PROGRESS, "Creating secrets...")
            if not self.setup_secrets(config):
                self.update_progress("secrets", DeploymentStatus.FAILED, "Failed to create secrets")
                return False, None
            self.update_progress("secrets", DeploymentStatus.SUCCESS, "Secrets created")

            # Step 2: Setup permissions
            self.update_progress("permissions", DeploymentStatus.IN_PROGRESS, "Configuring permissions...")
            if not self.setup_permissions(config):
                self.update_progress("permissions", DeploymentStatus.FAILED, "Failed to configure permissions")
                return False, None
            self.update_progress("permissions", DeploymentStatus.SUCCESS, "Permissions configured")

            # Step 3: Build and push
            self.update_progress("build", DeploymentStatus.IN_PROGRESS, "Building Docker image...")
            if not self.build_and_push(config, source_path):
                self.update_progress("build", DeploymentStatus.FAILED, "Failed to build/push image")
                return False, None
            self.update_progress("build", DeploymentStatus.SUCCESS, "Image built and pushed")

            # Step 4: Deploy
            self.update_progress("deploy", DeploymentStatus.IN_PROGRESS, "Deploying to cloud...")
            url = self.deploy(config)
            if not url:
                self.update_progress("deploy", DeploymentStatus.FAILED, "Deployment failed")
                return False, None
            self.update_progress("deploy", DeploymentStatus.SUCCESS, f"Deployed to {url}")
            self.service_url = url

            # Step 5: Verify health
            self.update_progress("health", DeploymentStatus.IN_PROGRESS, "Checking service health...")
            is_healthy, health_message = self.verify_health(url)
            if is_healthy:
                self.update_progress("health", DeploymentStatus.SUCCESS, health_message)
            else:
                self.update_progress("health", DeploymentStatus.FAILED, health_message)
                # Don't fail deployment on health check - service might still be starting

            return True, url

        except Exception as e:
            self.update_progress("error", DeploymentStatus.FAILED, str(e))
            return False, None
