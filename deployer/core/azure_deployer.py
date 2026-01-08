"""
Azure Deployer - Deploys Orbu to Azure Container Apps.

STATUS: Coming Soon - Not yet implemented.
"""

from typing import Optional
from core.base_deployer import (
    BaseDeployer,
    DeploymentConfig,
    DeploymentStep,
    DeploymentStatus,
)


class AzureDeployer(BaseDeployer):
    """Deployer for Microsoft Azure (Container Apps)."""

    @property
    def platform_name(self) -> str:
        return "Microsoft Azure"

    @property
    def platform_id(self) -> str:
        return "azure"

    def check_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if Azure CLI and docker are installed."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def check_authentication(self) -> tuple[bool, Optional[str]]:
        """Check if user is logged into Azure CLI."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def get_deployment_steps(self) -> list[DeploymentStep]:
        """Return list of deployment steps."""
        return [
            DeploymentStep("keyvault", "Create Azure Key Vault secrets"),
            DeploymentStep("identity", "Configure Managed Identity"),
            DeploymentStep("acr", "Push to Azure Container Registry"),
            DeploymentStep("deploy", "Deploy to Container Apps"),
            DeploymentStep("health", "Verify service health"),
        ]

    def setup_secrets(self, config: DeploymentConfig) -> bool:
        """Create secrets in Azure Key Vault."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def setup_permissions(self, config: DeploymentConfig) -> bool:
        """Configure Azure RBAC permissions."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def build_and_push(self, config: DeploymentConfig, source_path: str) -> bool:
        """Build Docker image and push to Azure Container Registry."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def deploy(self, config: DeploymentConfig) -> Optional[str]:
        """Deploy to Azure Container Apps."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def verify_health(self, url: str) -> tuple[bool, str]:
        """Check if the deployed service is healthy."""
        raise NotImplementedError(
            "Azure deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )
