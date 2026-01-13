"""
Step 3: Project Configuration

Collects GCP project ID and region.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from typing import Dict, Any, List

from ui.wizard import WizardStep, WizardController, COLORS


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

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.projects: List[str] = []

        # Title
        title = tk.Label(
            self,
            text="GCP Project Configuration",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(30, 10))

        subtitle = tk.Label(
            self,
            text="Select your Google Cloud project and deployment region",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 30))

        # Form container
        form_frame = tk.Frame(self, bg=COLORS['card_bg'])
        form_frame.pack(fill=tk.X, padx=100)

        # Project ID
        project_label = tk.Label(
            form_frame,
            text="GCP Project ID",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        project_label.pack(anchor=tk.W, pady=(10, 5))

        project_container = tk.Frame(form_frame, bg=COLORS['card_bg'])
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
            text="\u21bb",
            width=3,
            command=self._load_projects
        )
        self.refresh_button.pack(side=tk.LEFT, padx=(5, 0))

        project_hint = tk.Label(
            form_frame,
            text="Select from your available projects or enter a project ID",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        project_hint.pack(anchor=tk.W, pady=(2, 0))

        # Region
        region_label = tk.Label(
            form_frame,
            text="Region",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        region_label.pack(anchor=tk.W, pady=(25, 5))

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

        region_hint = tk.Label(
            form_frame,
            text="Choose a region close to your users for best performance",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        region_hint.pack(anchor=tk.W, pady=(2, 0))

        # Status label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        self.status_label.pack(pady=25)

    def on_enter(self):
        """Load projects when step becomes visible."""
        self._load_projects()

    def _load_projects(self):
        """Load available GCP projects."""
        self.status_label.config(text="Loading projects...", fg=COLORS['text_secondary'])
        self.update()

        try:
            # Get current project (use shell=True for Windows compatibility)
            current = subprocess.run(
                "gcloud config get-value project",
                shell=True, capture_output=True, text=True
            )
            current_project = current.stdout.strip()
            if current_project and current_project != "(unset)":
                self.project_var.set(current_project)

            # Get list of projects
            result = subprocess.run(
                "gcloud projects list --format=value(projectId)",
                shell=True, capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout:
                self.projects = [p.strip() for p in result.stdout.split('\n') if p.strip()]
                self.project_combo['values'] = self.projects
                self.status_label.config(
                    text=f"Found {len(self.projects)} project(s)",
                    fg=COLORS['success']
                )
            else:
                error_hint = result.stderr[:100] if result.stderr else "Unknown error"
                self.status_label.config(
                    text=f"Could not load projects: {error_hint}",
                    fg='#e65100'
                )
        except FileNotFoundError:
            self.status_label.config(
                text="gcloud not found. Is Google Cloud SDK installed?",
                fg=COLORS['error']
            )
        except Exception as e:
            self.status_label.config(
                text=f"Error: {str(e)}",
                fg=COLORS['error']
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
        self.status_label.config(text="Validating project...", fg=COLORS['text_secondary'])
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

            self.status_label.config(text="Project validated", fg=COLORS['success'])
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
