"""
Step 5: Review & Confirm

Shows a summary of all settings before deployment.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, ScrollableFrame, COLORS


class StepReview(WizardStep):
    """Review and confirm step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Title
        title = tk.Label(
            self,
            text="Review Configuration",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(20, 10))

        subtitle = tk.Label(
            self,
            text="Please review your settings before deploying",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 15))

        # Scrollable review area
        self.scroll_container = ScrollableFrame(self, bg=COLORS['card_bg'])
        self.scroll_container.pack(fill=tk.BOTH, expand=True, padx=30)

        self.review_frame = self.scroll_container.scrollable_frame

        # Will be populated on_enter
        self.confirm_var = tk.BooleanVar(value=False)

    def on_enter(self):
        """Populate review when step becomes visible."""
        # Clear existing content
        for widget in self.review_frame.winfo_children():
            widget.destroy()

        data = self.wizard.data

        # Organization section
        org_name = data.get('org_name', 'Not set')
        org_slug = data.get('org_slug', 'orbu')
        self._add_section("Organization", [
            ("Name", org_name),
            ("Resource Prefix", f"{org_slug}-orbu"),
        ])

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
            ("Password", "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"),  # Never show password
        ]

        if data.get('cloud_sql_connection'):
            db_items.insert(1, ("Cloud SQL Instance", data.get('cloud_sql_connection')))
        elif data.get('db_host'):
            db_items.insert(1, ("Host", data.get('db_host')))

        self._add_section("Database", db_items)

        # Admin section
        self._add_section("Admin Account", [
            ("Email", data.get('admin_email', 'Not set')),
            ("Password", "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"),  # Never show password
        ])

        # Resources section
        service_name = f"{org_slug}-orbu"
        sa_name = f"{org_slug}-orbu-sa"
        self._add_section("Resources to Create", [
            ("Secret Manager Secrets", f"7 secrets ({org_slug}-orbu-postgres-*, admin-*, org-name)"),
            ("Service Account", f"{sa_name}@{data.get('project_id', 'PROJECT')}.iam.gserviceaccount.com"),
            ("Container Image", f"gcr.io/{data.get('project_id', 'PROJECT')}/{service_name}:latest"),
            ("Cloud Run Service", service_name),
        ])

        # Warning
        warning_frame = tk.Frame(self.review_frame, bg='#fff3e0', padx=15, pady=10)
        warning_frame.pack(fill=tk.X, pady=20)

        warning_icon = tk.Label(
            warning_frame,
            text="\u26a0",
            font=('Segoe UI', 14),
            bg='#fff3e0',
            fg='#e65100'
        )
        warning_icon.pack(side=tk.LEFT)

        warning_text = tk.Label(
            warning_frame,
            text="Deploying will create GCP resources that may incur charges.",
            font=('Segoe UI', 10),
            bg='#fff3e0',
            fg='#e65100'
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
        confirm_check.pack(anchor=tk.W, pady=15)

        # Add some bottom padding
        spacer = tk.Frame(self.review_frame, height=20, bg=COLORS['card_bg'])
        spacer.pack()

        # Update button state
        self.wizard.set_next_text("Deploy")
        self.wizard.set_next_enabled(False)

    def _add_section(self, title: str, items: list):
        """Add a section to the review."""
        # Section header
        header = tk.Label(
            self.review_frame,
            text=title,
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        header.pack(anchor=tk.W, pady=(15, 10))

        # Items
        for label, value in items:
            item_frame = tk.Frame(self.review_frame, bg=COLORS['card_bg'])
            item_frame.pack(fill=tk.X, pady=3)

            label_widget = tk.Label(
                item_frame,
                text=f"{label}:",
                font=('Segoe UI', 10),
                bg=COLORS['card_bg'],
                fg=COLORS['text_secondary'],
                width=22,
                anchor='w'
            )
            label_widget.pack(side=tk.LEFT)

            value_widget = tk.Label(
                item_frame,
                text=value,
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'],
                fg=COLORS['text']
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
