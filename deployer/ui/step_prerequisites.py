"""
Step 2: Prerequisites Check

Checks if required tools (gcloud, docker) are installed.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import webbrowser
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController


class PrerequisiteItem(ttk.Frame):
    """A single prerequisite check item."""

    def __init__(self, parent, name: str, description: str):
        super().__init__(parent)

        self.name = name

        # Status icon
        self.status_label = ttk.Label(self, text="⏳", font=('Segoe UI', 12), width=3)
        self.status_label.pack(side=tk.LEFT)

        # Name and description
        text_frame = ttk.Frame(self)
        text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        name_label = ttk.Label(text_frame, text=name, font=('Segoe UI', 11, 'bold'))
        name_label.pack(anchor=tk.W)

        self.desc_label = ttk.Label(
            text_frame,
            text=description,
            font=('Segoe UI', 9),
            foreground='#666'
        )
        self.desc_label.pack(anchor=tk.W)

        # Action button (hidden by default)
        self.action_button = ttk.Button(self, text="Install", command=self._on_action)
        self.action_url = None

    def set_status(self, status: str, message: str = None, action_url: str = None):
        """Set the status of this prerequisite."""
        if status == 'checking':
            self.status_label.config(text="⏳")
            self.action_button.pack_forget()
        elif status == 'success':
            self.status_label.config(text="✓", foreground='green')
            if message:
                self.desc_label.config(text=message)
            self.action_button.pack_forget()
        elif status == 'error':
            self.status_label.config(text="✗", foreground='red')
            if message:
                self.desc_label.config(text=message, foreground='red')
            if action_url:
                self.action_url = action_url
                self.action_button.pack(side=tk.RIGHT)

    def _on_action(self):
        if self.action_url:
            webbrowser.open(self.action_url)


class StepPrerequisites(WizardStep):
    """Prerequisites check step."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.all_passed = False

        # Title
        title = ttk.Label(
            self,
            text="Checking Prerequisites",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(pady=(20, 10))

        subtitle = ttk.Label(
            self,
            text="The following tools must be installed to deploy Orbu",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 30))

        # Prerequisites list
        self.prereqs_frame = ttk.Frame(self)
        self.prereqs_frame.pack(fill=tk.X, padx=50)

        # Google Cloud SDK
        self.gcloud_item = PrerequisiteItem(
            self.prereqs_frame,
            "Google Cloud SDK",
            "Command-line tools for GCP"
        )
        self.gcloud_item.pack(fill=tk.X, pady=10)

        # Docker
        self.docker_item = PrerequisiteItem(
            self.prereqs_frame,
            "Docker",
            "Container runtime for building images"
        )
        self.docker_item.pack(fill=tk.X, pady=10)

        # GCloud Authentication
        self.auth_item = PrerequisiteItem(
            self.prereqs_frame,
            "GCP Authentication",
            "Logged into your Google Cloud account"
        )
        self.auth_item.pack(fill=tk.X, pady=10)

        # Recheck button
        self.recheck_button = ttk.Button(
            self,
            text="Check Again",
            command=self._run_checks
        )
        self.recheck_button.pack(pady=20)

        # Status message
        self.status_label = ttk.Label(
            self,
            text="",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        self.status_label.pack(pady=10)

    def on_enter(self):
        """Run checks when step becomes visible."""
        self.wizard.set_next_enabled(False)
        self.after(500, self._run_checks)

    def _run_checks(self):
        """Run all prerequisite checks."""
        self.all_passed = True

        # Check gcloud
        self.gcloud_item.set_status('checking')
        self.update()
        gcloud_ok = self._check_gcloud()

        # Check docker
        self.docker_item.set_status('checking')
        self.update()
        docker_ok = self._check_docker()

        # Check auth (only if gcloud is installed)
        if gcloud_ok:
            self.auth_item.set_status('checking')
            self.update()
            auth_ok = self._check_auth()
        else:
            self.auth_item.set_status('error', 'Install gcloud first')
            auth_ok = False

        # Update overall status
        self.all_passed = gcloud_ok and docker_ok and auth_ok

        if self.all_passed:
            self.status_label.config(
                text="All prerequisites met! Click Next to continue.",
                foreground='green'
            )
            self.wizard.set_next_enabled(True)
        else:
            self.status_label.config(
                text="Please install missing tools and check again.",
                foreground='red'
            )
            self.wizard.set_next_enabled(False)

    def _check_gcloud(self) -> bool:
        """Check if gcloud CLI is installed."""
        try:
            check_cmd = "where gcloud" if os.name == 'nt' else "which gcloud"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                # Get version
                version = subprocess.run(
                    "gcloud --version",
                    shell=True, capture_output=True, text=True
                )
                version_str = version.stdout.split('\n')[0] if version.stdout else "Installed"
                self.gcloud_item.set_status('success', version_str)
                return True
            else:
                self.gcloud_item.set_status(
                    'error',
                    'Not installed',
                    'https://cloud.google.com/sdk/docs/install'
                )
                return False
        except Exception:
            self.gcloud_item.set_status(
                'error',
                'Check failed',
                'https://cloud.google.com/sdk/docs/install'
            )
            return False

    def _check_docker(self) -> bool:
        """Check if Docker is installed and running."""
        try:
            check_cmd = "where docker" if os.name == 'nt' else "which docker"
            result = subprocess.run(check_cmd, shell=True, capture_output=True)
            if result.returncode != 0:
                self.docker_item.set_status(
                    'error',
                    'Not installed',
                    'https://docs.docker.com/get-docker/'
                )
                return False

            # Check if Docker is running
            result = subprocess.run(
                "docker info",
                shell=True, capture_output=True, text=True
            )
            if result.returncode == 0:
                # Get version
                version = subprocess.run(
                    "docker --version",
                    shell=True, capture_output=True, text=True
                )
                self.docker_item.set_status('success', version.stdout.strip())
                return True
            else:
                self.docker_item.set_status(
                    'error',
                    'Docker is installed but not running. Please start Docker.',
                    None
                )
                return False
        except Exception:
            self.docker_item.set_status(
                'error',
                'Check failed',
                'https://docs.docker.com/get-docker/'
            )
            return False

    def _check_auth(self) -> bool:
        """Check if user is logged into gcloud."""
        try:
            null_redirect = "2>nul" if os.name == 'nt' else "2>/dev/null"
            result = subprocess.run(
                f"gcloud config get-value account {null_redirect}",
                shell=True, capture_output=True, text=True
            )
            account = result.stdout.strip()
            if account and account != "(unset)":
                self.auth_item.set_status('success', f"Logged in as {account}")
                return True
            else:
                self.auth_item.set_status(
                    'error',
                    'Not logged in. Run: gcloud auth login',
                    None
                )
                # Add login button
                self.auth_item.action_button.config(text="Login", command=self._login_gcloud)
                self.auth_item.action_button.pack(side=tk.RIGHT)
                return False
        except Exception:
            self.auth_item.set_status('error', 'Check failed')
            return False

    def _login_gcloud(self):
        """Open gcloud login in browser."""
        subprocess.Popen("gcloud auth login", shell=True)
        messagebox.showinfo(
            "Login",
            "A browser window should open for GCP login.\n\n"
            "After logging in, click 'Check Again' to continue."
        )

    def validate(self) -> bool:
        """Validate that all prerequisites are met."""
        if not self.all_passed:
            messagebox.showwarning(
                "Prerequisites",
                "Please install all required tools before continuing."
            )
            return False
        return True

    def get_data(self) -> Dict[str, Any]:
        """Return prerequisite check results."""
        return {'prerequisites_passed': self.all_passed}
