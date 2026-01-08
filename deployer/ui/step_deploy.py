"""
Step 6: Deployment Progress

Shows real-time deployment progress.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
import sys
import os
import tempfile
import shutil
from typing import Dict, Any, Optional

from .wizard import WizardStep, WizardController
from ..core.base_deployer import DeploymentConfig, DeploymentStatus
from ..core.gcp_deployer import GCPDeployer, GCPConfig


class StepDeploy(WizardStep):
    """Deployment progress step."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.deployer: Optional[GCPDeployer] = None
        self.deploy_thread: Optional[threading.Thread] = None
        self.progress_queue = queue.Queue()
        self.is_deploying = False
        self.deployment_success = False
        self.service_url: Optional[str] = None
        self.source_path: Optional[str] = None

        # Title
        title = ttk.Label(
            self,
            text="Deploying Orbu",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(pady=(20, 10))

        self.subtitle = ttk.Label(
            self,
            text="Please wait while Orbu is being deployed...",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        self.subtitle.pack(pady=(0, 20))

        # Progress steps
        self.steps_frame = ttk.Frame(self)
        self.steps_frame.pack(fill=tk.X, padx=50, pady=10)

        self.step_labels = {}
        steps = [
            ("apis", "Enable GCP APIs"),
            ("secrets", "Create secrets"),
            ("permissions", "Configure permissions"),
            ("build", "Build Docker image"),
            ("push", "Push to registry"),
            ("deploy", "Deploy to Cloud Run"),
            ("health", "Verify health"),
        ]

        for step_id, step_name in steps:
            frame = ttk.Frame(self.steps_frame)
            frame.pack(fill=tk.X, pady=5)

            status_label = ttk.Label(frame, text="○", font=('Segoe UI', 12), width=3)
            status_label.pack(side=tk.LEFT)

            name_label = ttk.Label(frame, text=step_name, font=('Segoe UI', 10))
            name_label.pack(side=tk.LEFT)

            detail_label = ttk.Label(frame, text="", font=('Segoe UI', 9), foreground='#888')
            detail_label.pack(side=tk.LEFT, padx=(10, 0))

            self.step_labels[step_id] = {
                'status': status_label,
                'name': name_label,
                'detail': detail_label
            }

        # Log output
        log_label = ttk.Label(
            self,
            text="Deployment Log",
            font=('Segoe UI', 10, 'bold')
        )
        log_label.pack(anchor=tk.W, padx=50, pady=(20, 5))

        log_frame = ttk.Frame(self)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=(0, 10))

        self.log_text = tk.Text(
            log_frame,
            height=8,
            font=('Consolas', 9),
            bg='#1e1e1e',
            fg='#d4d4d4',
            state=tk.DISABLED
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)

        # Cancel button
        self.cancel_button = ttk.Button(
            self,
            text="Cancel",
            command=self._on_cancel
        )
        self.cancel_button.pack(pady=10)

    def on_enter(self):
        """Start deployment when step becomes visible."""
        # Hide navigation buttons
        self.wizard.hide_navigation()

        # Reset state
        self.deployment_success = False
        self.service_url = None

        # Clear log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # Reset step indicators
        for step_id, labels in self.step_labels.items():
            labels['status'].config(text="○", foreground='#888')
            labels['detail'].config(text="")

        # Extract source code and start deployment
        self.after(500, self._start_deployment)

    def _log(self, message: str):
        """Add message to log."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _update_step(self, step_id: str, status: DeploymentStatus, message: str = None):
        """Update a step's status."""
        if step_id not in self.step_labels:
            return

        labels = self.step_labels[step_id]

        if status == DeploymentStatus.PENDING:
            labels['status'].config(text="○", foreground='#888')
        elif status == DeploymentStatus.IN_PROGRESS:
            labels['status'].config(text="◐", foreground='#2196f3')
        elif status == DeploymentStatus.SUCCESS:
            labels['status'].config(text="✓", foreground='green')
        elif status == DeploymentStatus.FAILED:
            labels['status'].config(text="✗", foreground='red')

        if message:
            labels['detail'].config(text=message)

    def _extract_source(self) -> Optional[str]:
        """Extract bundled source code to temp directory."""
        # When running as PyInstaller bundle, source is in _MEIPASS
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
            source_dir = os.path.join(bundle_dir, 'orbu_source')
            if os.path.exists(source_dir):
                # Copy to temp directory
                temp_dir = tempfile.mkdtemp(prefix='orbu_deploy_')
                dest_dir = os.path.join(temp_dir, 'orbu')
                shutil.copytree(source_dir, dest_dir)
                self._log(f"Extracted source to: {dest_dir}")
                return dest_dir

        # Running from source - find project root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up from deployer/ui to project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

        # Check if we're in the right place
        if os.path.exists(os.path.join(project_root, 'Dockerfile')):
            self._log(f"Using source from: {project_root}")
            return project_root

        self._log("ERROR: Could not locate Orbu source code")
        return None

    def _start_deployment(self):
        """Start the deployment process."""
        self.is_deploying = True
        self._log("Starting deployment...")

        # Extract source
        self.source_path = self._extract_source()
        if not self.source_path:
            self._on_deployment_complete(False, None)
            return

        # Build config
        data = self.wizard.data
        gcp_config = GCPConfig(
            project_id=data.get('project_id'),
            region=data.get('region'),
            cloud_sql_connection=data.get('cloud_sql_connection')
        )

        config = DeploymentConfig(
            platform='gcp',
            db_connection_method=data.get('db_connection_method'),
            db_host=data.get('db_host', ''),
            db_port=data.get('db_port', '5432'),
            db_name=data.get('db_name'),
            db_user=data.get('db_user'),
            db_password=data.get('db_password'),
            platform_config=gcp_config
        )

        # Create deployer
        self.deployer = GCPDeployer(progress_callback=self._on_progress)

        # Start deployment in thread
        self.deploy_thread = threading.Thread(
            target=self._run_deployment,
            args=(config, self.source_path),
            daemon=True
        )
        self.deploy_thread.start()

        # Start polling for progress updates
        self._poll_progress()

    def _run_deployment(self, config: DeploymentConfig, source_path: str):
        """Run deployment in background thread."""
        try:
            success, url = self.deployer.run_deployment(config, source_path)
            self.progress_queue.put(('complete', success, url))
        except Exception as e:
            self.progress_queue.put(('error', str(e)))

    def _on_progress(self, step_name: str, status: DeploymentStatus, message: str = None):
        """Handle progress update from deployer."""
        self.progress_queue.put(('progress', step_name, status, message))

    def _poll_progress(self):
        """Poll for progress updates from deployment thread."""
        try:
            while True:
                item = self.progress_queue.get_nowait()

                if item[0] == 'progress':
                    _, step_name, status, message = item
                    self._update_step(step_name, status, message)
                    if message:
                        self._log(message)

                elif item[0] == 'complete':
                    _, success, url = item
                    self._on_deployment_complete(success, url)
                    return

                elif item[0] == 'error':
                    _, error = item
                    self._log(f"ERROR: {error}")
                    self._on_deployment_complete(False, None)
                    return

        except queue.Empty:
            pass

        # Continue polling if still deploying
        if self.is_deploying:
            self.after(100, self._poll_progress)

    def _on_deployment_complete(self, success: bool, url: Optional[str]):
        """Handle deployment completion."""
        self.is_deploying = False
        self.deployment_success = success
        self.service_url = url

        # Clean up temp directory
        if self.source_path and self.source_path.startswith(tempfile.gettempdir()):
            try:
                shutil.rmtree(os.path.dirname(self.source_path))
            except Exception:
                pass

        if success:
            self.subtitle.config(text="Deployment completed successfully!", foreground='green')
            self._log(f"\n✓ Deployment successful!")
            if url:
                self._log(f"Service URL: {url}")
            self.cancel_button.config(text="Continue", command=self._on_continue)
        else:
            self.subtitle.config(text="Deployment failed. See log for details.", foreground='red')
            self._log("\n✗ Deployment failed")
            self.cancel_button.config(text="Close", command=self._on_close)

    def _on_cancel(self):
        """Handle cancel button."""
        if self.is_deploying:
            if messagebox.askyesno("Cancel", "Are you sure you want to cancel the deployment?"):
                self.is_deploying = False
                self._log("Deployment cancelled by user")
                self.wizard.root.quit()
        else:
            self.wizard.root.quit()

    def _on_continue(self):
        """Continue to completion step."""
        self.wizard.data['service_url'] = self.service_url
        self.wizard.data['deployment_success'] = self.deployment_success
        self.wizard.go_next()

    def _on_close(self):
        """Close the wizard."""
        self.wizard.root.quit()

    def get_data(self) -> Dict[str, Any]:
        """Return deployment results."""
        return {
            'deployment_success': self.deployment_success,
            'service_url': self.service_url
        }
