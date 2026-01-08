"""
Step 5: Review & Confirm

Shows a summary of all settings before deployment.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from .wizard import WizardStep, WizardController


class StepReview(WizardStep):
    """Review and confirm step."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Title
        title = ttk.Label(
            self,
            text="Review Configuration",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(pady=(20, 10))

        subtitle = ttk.Label(
            self,
            text="Please review your settings before deploying",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 20))

        # Scrollable review area
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.review_frame = ttk.Frame(canvas)

        self.review_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.review_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=50)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Will be populated on_enter
        self.confirm_var = tk.BooleanVar(value=False)

    def on_enter(self):
        """Populate review when step becomes visible."""
        # Clear existing content
        for widget in self.review_frame.winfo_children():
            widget.destroy()

        data = self.wizard.data

        # Platform section
        self._add_section("Platform", [
            ("Cloud Provider", "Google Cloud Platform"),
            ("Project ID", data.get('project_id', 'Not set')),
            ("Region", data.get('region', 'Not set')),
        ])

        # Database section
        db_type = data.get('db_connection_method', 'unknown')
        db_type_display = {
            'unix_socket': 'Cloud SQL (Same Project)',
            'python_connector': 'Cloud SQL (Cross-Project)',
            'external': 'External PostgreSQL'
        }.get(db_type, db_type)

        db_items = [
            ("Connection Type", db_type_display),
            ("Database Name", data.get('db_name', 'Not set')),
            ("Username", data.get('db_user', 'Not set')),
            ("Password", "••••••••"),  # Never show password
        ]

        if data.get('cloud_sql_connection'):
            db_items.insert(1, ("Cloud SQL Instance", data.get('cloud_sql_connection')))
        elif data.get('db_host'):
            db_items.insert(1, ("Host", data.get('db_host')))

        self._add_section("Database", db_items)

        # Resources section
        self._add_section("Resources to Create", [
            ("Secret Manager Secrets", "4 secrets (host, db, user, password)"),
            ("Service Account", f"orbu-sa@{data.get('project_id', 'PROJECT')}.iam.gserviceaccount.com"),
            ("Container Image", f"gcr.io/{data.get('project_id', 'PROJECT')}/orbu:latest"),
            ("Cloud Run Service", "orbu"),
        ])

        # Warning
        warning_frame = ttk.Frame(self.review_frame)
        warning_frame.pack(fill=tk.X, pady=20)

        warning_icon = ttk.Label(
            warning_frame,
            text="⚠️",
            font=('Segoe UI', 14)
        )
        warning_icon.pack(side=tk.LEFT)

        warning_text = ttk.Label(
            warning_frame,
            text="Deploying will create GCP resources that may incur charges.",
            font=('Segoe UI', 10),
            foreground='#cc6600'
        )
        warning_text.pack(side=tk.LEFT, padx=10)

        # Confirmation checkbox
        self.confirm_var.set(False)
        confirm_check = ttk.Checkbutton(
            self.review_frame,
            text="I understand and want to proceed with deployment",
            variable=self.confirm_var,
            command=self._on_confirm_change
        )
        confirm_check.pack(anchor=tk.W, pady=10)

        # Update button state
        self.wizard.set_next_text("Deploy")
        self.wizard.set_next_enabled(False)

    def _add_section(self, title: str, items: list):
        """Add a section to the review."""
        # Section header
        header = ttk.Label(
            self.review_frame,
            text=title,
            font=('Segoe UI', 11, 'bold')
        )
        header.pack(anchor=tk.W, pady=(15, 10))

        # Items
        for label, value in items:
            item_frame = ttk.Frame(self.review_frame)
            item_frame.pack(fill=tk.X, pady=2)

            label_widget = ttk.Label(
                item_frame,
                text=f"{label}:",
                font=('Segoe UI', 10),
                foreground='#666',
                width=25
            )
            label_widget.pack(side=tk.LEFT)

            value_widget = ttk.Label(
                item_frame,
                text=value,
                font=('Segoe UI', 10, 'bold')
            )
            value_widget.pack(side=tk.LEFT)

        # Separator
        sep = ttk.Separator(self.review_frame, orient='horizontal')
        sep.pack(fill=tk.X, pady=10)

    def _on_confirm_change(self):
        """Handle confirmation checkbox change."""
        self.wizard.set_next_enabled(self.confirm_var.get())

    def validate(self) -> bool:
        """Validate confirmation."""
        if not self.confirm_var.get():
            messagebox.showwarning(
                "Confirmation Required",
                "Please check the confirmation box to continue."
            )
            return False
        return True

    def get_data(self) -> Dict[str, Any]:
        """Return confirmation status."""
        return {'confirmed': self.confirm_var.get()}
