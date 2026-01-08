"""
Step 3: Project Configuration

Collects GCP project ID and region.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from typing import Dict, Any, List

from ui.wizard import WizardStep, WizardController


class StepProject(WizardStep):
    """Project configuration step."""

    # Common GCP regions
    REGIONS = [
        "us-central1",
        "us-east1",
        "us-east4",
        "us-west1",
        "us-west2",
        "europe-west1",
        "europe-west2",
        "europe-west3",
        "asia-east1",
        "asia-northeast1",
        "asia-southeast1",
        "australia-southeast1",
    ]

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.projects: List[str] = []

        # Title
        title = ttk.Label(
            self,
            text="GCP Project Configuration",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(pady=(20, 10))

        subtitle = ttk.Label(
            self,
            text="Select your Google Cloud project and deployment region",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 30))

        # Form container
        form_frame = ttk.Frame(self)
        form_frame.pack(fill=tk.X, padx=100)

        # Project ID
        project_label = ttk.Label(
            form_frame,
            text="GCP Project ID",
            font=('Segoe UI', 10, 'bold')
        )
        project_label.pack(anchor=tk.W, pady=(10, 5))

        project_container = ttk.Frame(form_frame)
        project_container.pack(fill=tk.X)

        self.project_var = tk.StringVar()
        self.project_combo = ttk.Combobox(
            project_container,
            textvariable=self.project_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.project_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.refresh_button = ttk.Button(
            project_container,
            text="↻",
            width=3,
            command=self._load_projects
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(5, 0))

        project_hint = ttk.Label(
            form_frame,
            text="Select from your available projects or enter a project ID",
            font=('Segoe UI', 9),
            foreground='#888'
        )
        project_hint.pack(anchor=tk.W, pady=(2, 0))

        # Region
        region_label = ttk.Label(
            form_frame,
            text="Region",
            font=('Segoe UI', 10, 'bold')
        )
        region_label.pack(anchor=tk.W, pady=(20, 5))

        self.region_var = tk.StringVar(value="us-central1")
        self.region_combo = ttk.Combobox(
            form_frame,
            textvariable=self.region_var,
            values=self.REGIONS,
            font=('Segoe UI', 10),
            width=40,
            state='readonly'
        )
        self.region_combo.pack(fill=tk.X)

        region_hint = ttk.Label(
            form_frame,
            text="Choose a region close to your users for best performance",
            font=('Segoe UI', 9),
            foreground='#888'
        )
        region_hint.pack(anchor=tk.W, pady=(2, 0))

        # Status label
        self.status_label = ttk.Label(
            self,
            text="",
            font=('Segoe UI', 10)
        )
        self.status_label.pack(pady=20)

    def on_enter(self):
        """Load projects when step becomes visible."""
        self._load_projects()

    def _load_projects(self):
        """Load available GCP projects."""
        self.status_label.config(text="Loading projects...", foreground='#666')
        self.update()

        try:
            # Get current project
            null_redirect = "2>nul" if __import__('os').name == 'nt' else "2>/dev/null"
            current = subprocess.run(
                f"gcloud config get-value project {null_redirect}",
                shell=True, capture_output=True, text=True
            )
            current_project = current.stdout.strip()
            if current_project and current_project != "(unset)":
                self.project_var.set(current_project)

            # Get list of projects
            result = subprocess.run(
                "gcloud projects list --format='value(projectId)'",
                shell=True, capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout:
                self.projects = [p.strip() for p in result.stdout.split('\n') if p.strip()]
                self.project_combo['values'] = self.projects
                self.status_label.config(
                    text=f"Found {len(self.projects)} project(s)",
                    foreground='green'
                )
            else:
                self.status_label.config(
                    text="Could not load projects. Enter project ID manually.",
                    foreground='orange'
                )
        except Exception as e:
            self.status_label.config(
                text=f"Error loading projects: {str(e)}",
                foreground='red'
            )

    def validate(self) -> bool:
        """Validate project configuration."""
        project = self.project_var.get().strip()
        region = self.region_var.get().strip()

        if not project:
            messagebox.showwarning("Required", "Please enter a GCP Project ID.")
            return False

        if not region:
            messagebox.showwarning("Required", "Please select a region.")
            return False

        # Validate project exists (optional check)
        self.status_label.config(text="Validating project...", foreground='#666')
        self.update()

        try:
            result = subprocess.run(
                f"gcloud projects describe {project}",
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                if messagebox.askyesno(
                    "Project Not Found",
                    f"Could not verify project '{project}'.\n\n"
                    "This might be a permissions issue. Continue anyway?"
                ):
                    return True
                return False

            # Set the project in gcloud config
            subprocess.run(
                f"gcloud config set project {project}",
                shell=True, capture_output=True
            )

            self.status_label.config(text="Project validated", foreground='green')
            return True

        except Exception as e:
            messagebox.showerror("Error", f"Failed to validate project: {str(e)}")
            return False

    def get_data(self) -> Dict[str, Any]:
        """Return project configuration."""
        return {
            'project_id': self.project_var.get().strip(),
            'region': self.region_var.get().strip()
        }
