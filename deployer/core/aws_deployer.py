"""
AWS Deployer - Deploys Orbu to AWS App Runner.

STATUS: Coming Soon - Not yet implemented.
"""

from typing import Optional
from core.base_deployer import (
    BaseDeployer,
    DeploymentConfig,
    DeploymentStep,
    DeploymentStatus,
)


class AWSDeployer(BaseDeployer):
    """Deployer for Amazon Web Services (App Runner)."""

    @property
    def platform_name(self) -> str:
        return "Amazon Web Services"

    @property
    def platform_id(self) -> str:
        return "aws"

    def check_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if AWS CLI and docker are installed."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def check_authentication(self) -> tuple[bool, Optional[str]]:
        """Check if user is logged into AWS CLI."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def get_deployment_steps(self) -> list[DeploymentStep]:
        """Return list of deployment steps."""
        return [
            DeploymentStep("secrets", "Create AWS Secrets Manager secrets"),
            DeploymentStep("iam", "Configure IAM Role"),
            DeploymentStep("ecr", "Push to Elastic Container Registry"),
            DeploymentStep("deploy", "Deploy to App Runner"),
            DeploymentStep("health", "Verify service health"),
        ]

    def setup_secrets(self, config: DeploymentConfig) -> bool:
        """Create secrets in AWS Secrets Manager."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def setup_permissions(self, config: DeploymentConfig) -> bool:
        """Configure AWS IAM permissions."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def build_and_push(self, config: DeploymentConfig, source_path: str) -> bool:
        """Build Docker image and push to ECR."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def deploy(self, config: DeploymentConfig) -> Optional[str]:
        """Deploy to AWS App Runner."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )

    def verify_health(self, url: str) -> tuple[bool, str]:
        """Check if the deployed service is healthy."""
        raise NotImplementedError(
            "AWS deployment is coming soon. "
            "Please use Google Cloud Platform for now."
        )
