"""
GCP Deployer - Deploys Orbu to Google Cloud Run.

Handles:
- Secret Manager setup
- Service account creation and IAM permissions
- Docker image build and push to GCR
- Cloud Run deployment
"""

import subprocess
import os
import time
import urllib.request
import bcrypt
from typing import Optional, Callable
from dataclasses import dataclass

from core.base_deployer import (
    BaseDeployer,
    DeploymentConfig,
    DeploymentStep,
    DeploymentStatus,
)


@dataclass
class GCPConfig:
    """GCP-specific configuration."""
    project_id: str
    region: str
    cloud_sql_connection: Optional[str] = None  # PROJECT:REGION:INSTANCE


class GCPDeployer(BaseDeployer):
    """Deployer for Google Cloud Platform (Cloud Run)."""

    @property
    def platform_name(self) -> str:
        return "Google Cloud Platform"

    @property
    def platform_id(self) -> str:
        return "gcp"

    def _run_cmd(self, cmd: str, capture: bool = True, check: bool = True) -> Optional[str]:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=capture,
                text=True,
                check=check
            )
            return result.stdout.strip() if capture else None
        except subprocess.CalledProcessError as e:
            if check:
                raise
            return None

    def _cmd_exists(self, cmd: str) -> bool:
        """Check if a command exists."""
        try:
            check_cmd = f"where {cmd}" if os.name == 'nt' else f"which {cmd}"
            subprocess.run(check_cmd, shell=True, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def check_prerequisites(self) -> tuple[bool, list[str]]:
        """Check if gcloud and docker are installed."""
        missing = []

        if not self._cmd_exists("gcloud"):
            missing.append("gcloud (Google Cloud SDK)")

        if not self._cmd_exists("docker"):
            missing.append("docker")

        return len(missing) == 0, missing

    def check_authentication(self) -> tuple[bool, Optional[str]]:
        """Check if user is logged into gcloud."""
        try:
            null_redirect = "2>nul" if os.name == 'nt' else "2>/dev/null"
            account = self._run_cmd(f"gcloud config get-value account {null_redirect}")
            if account and account != "(unset)":
                return True, account
            return False, "Not logged in"
        except Exception:
            return False, "Failed to check authentication"

    def get_projects(self) -> list[str]:
        """Get list of available GCP projects."""
        try:
            output = self._run_cmd("gcloud projects list --format='value(projectId)'", check=False)
            if output:
                return [p.strip() for p in output.split('\n') if p.strip()]
            return []
        except Exception:
            return []

    def get_current_project(self) -> Optional[str]:
        """Get the currently configured project."""
        try:
            null_redirect = "2>nul" if os.name == 'nt' else "2>/dev/null"
            project = self._run_cmd(f"gcloud config get-value project {null_redirect}", check=False)
            if project and project != "(unset)":
                return project
            return None
        except Exception:
            return None

    def get_deployment_steps(self) -> list[DeploymentStep]:
        """Return list of deployment steps."""
        return [
            DeploymentStep("apis", "Enable GCP APIs"),
            DeploymentStep("secrets", "Create secrets in Secret Manager"),
            DeploymentStep("permissions", "Configure service account and IAM"),
            DeploymentStep("build", "Build Docker image"),
            DeploymentStep("push", "Push image to Container Registry"),
            DeploymentStep("deploy", "Deploy to Cloud Run"),
            DeploymentStep("health", "Verify service health"),
        ]

    def _enable_apis(self, project_id: str) -> bool:
        """Enable required GCP APIs."""
        apis = [
            ("secretmanager.googleapis.com", "Secret Manager API"),
            ("artifactregistry.googleapis.com", "Artifact Registry API"),
            ("run.googleapis.com", "Cloud Run API"),
            ("sqladmin.googleapis.com", "Cloud SQL Admin API"),
        ]

        for api, name in apis:
            self.update_progress("apis", DeploymentStatus.IN_PROGRESS, f"Enabling {name}...")
            result = subprocess.run(
                f"gcloud services enable {api} --project={project_id}",
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                self.update_progress("apis", DeploymentStatus.FAILED, f"Failed to enable {name}")
                return False

        return True

    def _create_or_update_secret(self, secret_name: str, secret_value: str, project_id: str) -> bool:
        """Create or update a secret in Secret Manager."""
        null_redirect = "2>nul" if os.name == 'nt' else "2>/dev/null"

        # Check if secret exists
        existing = self._run_cmd(
            f"gcloud secrets describe {secret_name} --project={project_id} {null_redirect}",
            check=False
        )

        temp_file = os.path.join(os.environ.get('TEMP', '/tmp'), f'orbu_secret_{secret_name}.tmp')
        try:
            with open(temp_file, 'w') as f:
                f.write(secret_value)

            if existing:
                # Add new version
                result = subprocess.run(
                    f"gcloud secrets versions add {secret_name} --data-file={temp_file} --project={project_id}",
                    shell=True, capture_output=True, text=True
                )
            else:
                # Create new secret
                result = subprocess.run(
                    f"gcloud secrets create {secret_name} --data-file={temp_file} --project={project_id}",
                    shell=True, capture_output=True, text=True
                )

            return result.returncode == 0 or "already exists" in result.stderr.lower()
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _get_service_name(self, config: DeploymentConfig) -> str:
        """Get the service name based on org slug."""
        org_slug = config.org_slug or 'orbu'
        return f"{org_slug}-orbu"

    def _get_secret_prefix(self, config: DeploymentConfig) -> str:
        """Get the secret name prefix based on org slug."""
        org_slug = config.org_slug or 'orbu'
        return f"{org_slug}-orbu"

    def _get_sa_name(self, config: DeploymentConfig) -> str:
        """Get the service account name based on org slug."""
        org_slug = config.org_slug or 'orbu'
        return f"{org_slug}-orbu-sa"

    def setup_secrets(self, config: DeploymentConfig) -> bool:
        """Create secrets in Secret Manager."""
        gcp_config: GCPConfig = config.platform_config
        project_id = gcp_config.project_id
        prefix = self._get_secret_prefix(config)

        # Enable Secret Manager API first
        self._run_cmd(f"gcloud services enable secretmanager.googleapis.com --project={project_id}", check=False)

        secrets = {
            f'{prefix}-postgres-host': config.db_host,
            f'{prefix}-postgres-db': config.db_name,
            f'{prefix}-postgres-user': config.db_user,
            f'{prefix}-postgres-password': config.db_password,
        }

        # Add Cloud SQL connection if using Python Connector
        if gcp_config.cloud_sql_connection and config.db_connection_method == 'python_connector':
            secrets[f'{prefix}-cloud-sql-connection'] = gcp_config.cloud_sql_connection

        # Add admin credentials (hash the password)
        if config.admin_email and config.admin_password:
            secrets[f'{prefix}-admin-email'] = config.admin_email
            self.update_progress("secrets", DeploymentStatus.IN_PROGRESS, "Hashing admin password...")
            secrets[f'{prefix}-admin-password-hash'] = self._hash_password(config.admin_password)

        # Add organization name as a secret (for the app header)
        if config.org_name:
            secrets[f'{prefix}-org-name'] = config.org_name

        for secret_name, secret_value in secrets.items():
            if not secret_value:
                continue
            self.update_progress("secrets", DeploymentStatus.IN_PROGRESS, f"Creating {secret_name}...")
            if not self._create_or_update_secret(secret_name, secret_value, project_id):
                return False

        return True

    def setup_permissions(self, config: DeploymentConfig) -> bool:
        """Create service account and configure IAM permissions."""
        gcp_config: GCPConfig = config.platform_config
        project_id = gcp_config.project_id
        sa_name = self._get_sa_name(config)
        sa_email = f"{sa_name}@{project_id}.iam.gserviceaccount.com"
        display_name = f"{config.org_name or 'Orbu'} Service Account"

        null_redirect = "2>nul" if os.name == 'nt' else "2>/dev/null"

        # Check if SA exists
        existing = self._run_cmd(
            f"gcloud iam service-accounts describe {sa_email} {null_redirect}",
            check=False
        )

        if not existing:
            self.update_progress("permissions", DeploymentStatus.IN_PROGRESS, "Creating service account...")
            result = subprocess.run(
                f'gcloud iam service-accounts create {sa_name} --display-name="{display_name}" --project={project_id}',
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0 and "already exists" not in result.stderr.lower():
                return False

        # Grant permissions
        permissions = [
            ("roles/secretmanager.secretAccessor", "Secret Manager access"),
            ("roles/cloudsql.client", "Cloud SQL access"),
        ]

        for role, description in permissions:
            self.update_progress("permissions", DeploymentStatus.IN_PROGRESS, f"Granting {description}...")
            subprocess.run(
                f"gcloud projects add-iam-policy-binding {project_id} "
                f"--member=serviceAccount:{sa_email} "
                f"--role={role} "
                f"--condition=None "
                f"--quiet",
                shell=True, capture_output=True, text=True
            )

        # Wait for IAM propagation
        self.update_progress("permissions", DeploymentStatus.IN_PROGRESS, "Waiting for IAM propagation (30s)...")
        time.sleep(30)

        return True

    def _get_subprocess_flags(self) -> dict:
        """Get platform-specific subprocess flags to hide console window on Windows."""
        flags = {}
        if os.name == 'nt':
            # Hide console window on Windows
            flags['creationflags'] = subprocess.CREATE_NO_WINDOW
        return flags

    def build_and_push(self, config: DeploymentConfig, source_path: str) -> bool:
        """Build Docker image and push to GCR."""
        gcp_config: GCPConfig = config.platform_config
        project_id = gcp_config.project_id
        service_name = self._get_service_name(config)
        image = f"gcr.io/{project_id}/{service_name}:latest"

        # Enable APIs
        self.update_progress("apis", DeploymentStatus.IN_PROGRESS, "Enabling required APIs...")
        if not self._enable_apis(project_id):
            return False
        self.update_progress("apis", DeploymentStatus.SUCCESS, "APIs enabled")

        # Configure Docker for GCR
        self.update_progress("build", DeploymentStatus.IN_PROGRESS, "Configuring Docker for GCR...")
        self._run_cmd("gcloud auth configure-docker gcr.io --quiet")

        # Build image
        self.update_progress("build", DeploymentStatus.IN_PROGRESS, "Building Docker image (this may take a few minutes)...")
        original_dir = os.getcwd()
        os.chdir(source_path)

        try:
            result = subprocess.run(
                ["docker", "build", "--no-cache", "-t", image, "."],
                capture_output=True, text=True,
                **self._get_subprocess_flags()
            )
            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self.update_progress("build", DeploymentStatus.FAILED, f"Docker build failed: {error_msg}")
                return False
            self.update_progress("build", DeploymentStatus.SUCCESS, "Docker image built")

            # Push image
            self.update_progress("push", DeploymentStatus.IN_PROGRESS, "Pushing image to GCR...")
            result = subprocess.run(
                ["docker", "push", image],
                capture_output=True, text=True,
                **self._get_subprocess_flags()
            )
            if result.returncode != 0:
                error_msg = result.stderr[:500] if result.stderr else "Unknown error"
                self.update_progress("push", DeploymentStatus.FAILED, f"Docker push failed: {error_msg}")
                return False
            self.update_progress("push", DeploymentStatus.SUCCESS, "Image pushed to GCR")

            return True
        finally:
            os.chdir(original_dir)

    def deploy(self, config: DeploymentConfig) -> Optional[str]:
        """Deploy to Cloud Run."""
        gcp_config: GCPConfig = config.platform_config
        project_id = gcp_config.project_id
        region = gcp_config.region
        service_name = self._get_service_name(config)
        prefix = self._get_secret_prefix(config)
        sa_name = self._get_sa_name(config)
        image = f"gcr.io/{project_id}/{service_name}:latest"

        self.update_progress("deploy", DeploymentStatus.IN_PROGRESS, "Preparing Cloud Run deployment...")

        # Build deploy command with dynamic secret names
        secrets_list = (
            f"POSTGRES_HOST={prefix}-postgres-host:latest,"
            f"POSTGRES_DB={prefix}-postgres-db:latest,"
            f"POSTGRES_USER={prefix}-postgres-user:latest,"
            f"POSTGRES_PASSWORD={prefix}-postgres-password:latest,"
            f"ADMIN_EMAIL={prefix}-admin-email:latest,"
            f"ADMIN_PASSWORD_HASH={prefix}-admin-password-hash:latest,"
            f"ORG_NAME={prefix}-org-name:latest"
        )

        deploy_cmd = (
            f"gcloud run deploy {service_name} "
            f"--image={image} "
            f"--region={region} "
            f"--project={project_id} "
            f"--platform=managed "
            f"--allow-unauthenticated "
            f"--service-account={sa_name}@{project_id}.iam.gserviceaccount.com "
            f"--cpu=2 "
            f"--memory=2Gi "
            f"--min-instances=1 "
            f"--max-instances=10 "
            f"--concurrency=80 "
            f"--timeout=300 "
            f"--execution-environment=gen2 "
            f"--cpu-boost "
            f"--set-env-vars=GCP_PROJECT_ID={project_id},CORS_ORIGINS=* "
            f"--set-secrets={secrets_list}"
        )

        # Add Cloud SQL connection if using unix socket
        if config.db_connection_method == 'unix_socket' and gcp_config.cloud_sql_connection:
            deploy_cmd += f" --add-cloudsql-instances={gcp_config.cloud_sql_connection}"
        elif config.db_connection_method == 'python_connector':
            deploy_cmd += f" --update-secrets=CLOUD_SQL_CONNECTION={prefix}-cloud-sql-connection:latest"

        self.update_progress("deploy", DeploymentStatus.IN_PROGRESS, "Deploying to Cloud Run (this may take a few minutes)...")

        result = subprocess.run(deploy_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            # Format error message - prefer stderr, fall back to stdout
            error_output = result.stderr or result.stdout or "Unknown error"
            error_msg = error_output[:500] if len(error_output) > 500 else error_output
            self.update_progress("deploy", DeploymentStatus.FAILED, f"Cloud Run deploy failed: {error_msg}")
            return None

        self.update_progress("deploy", DeploymentStatus.IN_PROGRESS, "Retrieving service URL...")

        # Get service URL - use double quotes for Windows compatibility
        url_cmd = f'gcloud run services describe {service_name} --region={region} --project={project_id} --format="value(status.url)"'
        url_result = subprocess.run(url_cmd, shell=True, capture_output=True, text=True)

        if url_result.returncode == 0 and url_result.stdout.strip():
            url = url_result.stdout.strip()
            self.update_progress("deploy", DeploymentStatus.SUCCESS, f"Deployed to {url}")
            return url
        else:
            # Deploy succeeded but couldn't get URL - try alternative method
            self.update_progress("deploy", DeploymentStatus.IN_PROGRESS, "Trying alternative URL retrieval...")
            list_cmd = f'gcloud run services list --region={region} --project={project_id} --format="value(URL)" --filter="SERVICE:{service_name}"'
            list_result = subprocess.run(list_cmd, shell=True, capture_output=True, text=True)

            if list_result.returncode == 0 and list_result.stdout.strip():
                url = list_result.stdout.strip()
                self.update_progress("deploy", DeploymentStatus.SUCCESS, f"Deployed to {url}")
                return url

            # Still can't get URL - construct it manually (Cloud Run URL format is predictable)
            fallback_url = f"https://{service_name}-{project_id[:20]}.{region}.run.app"
            self.update_progress("deploy", DeploymentStatus.SUCCESS, f"Deployed (URL may be: {fallback_url})")
            return fallback_url

    def verify_health(self, url: str) -> tuple[bool, str]:
        """Check if the deployed service is healthy."""
        try:
            health_url = f"{url}/api/health"
            req = urllib.request.Request(health_url, headers={'User-Agent': 'orbu-deployer'})
            with urllib.request.urlopen(req, timeout=30) as response:
                health_data = response.read().decode('utf-8')
                if '"healthy"' in health_data:
                    return True, "Service is healthy"
                elif '"degraded"' in health_data:
                    return True, "Service is degraded (database may still be connecting)"
                else:
                    return False, f"Unexpected health response: {health_data}"
        except Exception as e:
            return False, f"Health check failed: {str(e)}"
