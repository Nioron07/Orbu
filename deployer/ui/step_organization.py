"""
Step 2: Organization Configuration

Collects the organization name for branding and resource naming.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, COLORS


def validate_org_name(name: str) -> tuple[bool, str]:
    """
    Validate organization name for use in resource naming.

    Requirements:
    - 2-20 characters
    - Letters, numbers, hyphens only
    - Must start with a letter
    - Will be converted to lowercase for resource naming

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(name) < 2:
        return False, "Organization name must be at least 2 characters"

    if len(name) > 20:
        return False, "Organization name must be 20 characters or less"

    if not re.match(r'^[a-zA-Z]', name):
        return False, "Organization name must start with a letter"

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9-]*$', name):
        return False, "Organization name can only contain letters, numbers, and hyphens"

    return True, ""


def slugify_org_name(name: str) -> str:
    """Convert organization name to a URL/resource-safe slug."""
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


class StepOrganization(WizardStep):
    """Organization configuration step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Title
        title = tk.Label(
            self,
            text="Organization",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(30, 10))

        subtitle = tk.Label(
            self,
            text="Enter your organization name for branding and resource naming",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 30))

        # Form container
        form_frame = tk.Frame(self, bg=COLORS['card_bg'])
        form_frame.pack(fill=tk.X, padx=100)

        # Organization Name
        org_label = tk.Label(
            form_frame,
            text="Organization Name",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        org_label.pack(anchor=tk.W, pady=(10, 5))

        self.org_name_var = tk.StringVar()
        self.org_name_var.trace_add('write', self._on_name_change)
        self.org_name_entry = ttk.Entry(
            form_frame,
            textvariable=self.org_name_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.org_name_entry.pack(fill=tk.X)

        org_hint = tk.Label(
            form_frame,
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        org_hint.pack(anchor=tk.W, pady=(2, 0))

        # Preview section
        preview_label = tk.Label(
            form_frame,
            text="Resource Naming Preview",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        preview_label.pack(anchor=tk.W, pady=(25, 10))

        # Preview frame
        preview_frame = tk.Frame(form_frame, bg='#f5f5f5', padx=15, pady=10)
        preview_frame.pack(fill=tk.X)

        # Cloud Project preview
        project_row = tk.Frame(preview_frame, bg='#f5f5f5')
        project_row.pack(fill=tk.X, pady=2)

        tk.Label(
            project_row,
            text="Cloud Project:",
            font=('Segoe UI', 9),
            bg='#f5f5f5',
            fg=COLORS['text_secondary'],
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT)

        self.project_preview = tk.Label(
            project_row,
            text="<org>-orbu",
            font=('Segoe UI', 9, 'bold'),
            bg='#f5f5f5',
            fg=COLORS['text']
        )
        self.project_preview.pack(side=tk.LEFT)

        # Service preview
        service_row = tk.Frame(preview_frame, bg='#f5f5f5')
        service_row.pack(fill=tk.X, pady=2)

        tk.Label(
            service_row,
            text="Cloud Run Service:",
            font=('Segoe UI', 9),
            bg='#f5f5f5',
            fg=COLORS['text_secondary'],
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT)

        self.service_preview = tk.Label(
            service_row,
            text="<org>-orbu",
            font=('Segoe UI', 9, 'bold'),
            bg='#f5f5f5',
            fg=COLORS['text']
        )
        self.service_preview.pack(side=tk.LEFT)

        # Header preview
        header_row = tk.Frame(preview_frame, bg='#f5f5f5')
        header_row.pack(fill=tk.X, pady=2)

        tk.Label(
            header_row,
            text="App Header:",
            font=('Segoe UI', 9),
            bg='#f5f5f5',
            fg=COLORS['text_secondary'],
            width=15,
            anchor='w'
        ).pack(side=tk.LEFT)

        self.header_preview = tk.Label(
            header_row,
            text="<Organization> - Orbu",
            font=('Segoe UI', 9, 'bold'),
            bg='#f5f5f5',
            fg=COLORS['text']
        )
        self.header_preview.pack(side=tk.LEFT)

        # Info
        info_frame = tk.Frame(form_frame, bg='#e3f2fd', padx=15, pady=10)
        info_frame.pack(fill=tk.X, pady=(20, 0))

        info_icon = tk.Label(
            info_frame,
            text="\u2139",
            font=('Segoe UI', 14),
            bg='#e3f2fd',
            fg='#1565c0'
        )
        info_icon.pack(side=tk.LEFT)

        info_text = tk.Label(
            info_frame,
            text="The organization name will be displayed in the app header\nand used to name cloud resources.",
            font=('Segoe UI', 9),
            bg='#e3f2fd',
            fg='#1565c0',
            justify='left'
        )
        info_text.pack(side=tk.LEFT, padx=10)

    def _on_name_change(self, *args):
        """Update preview when name changes."""
        name = self.org_name_var.get().strip()
        if name:
            slug = slugify_org_name(name)
            self.project_preview.config(text=f"{slug}-orbu")
            self.service_preview.config(text=f"{slug}-orbu")
            self.header_preview.config(text=f"{name} - Orbu")
        else:
            self.project_preview.config(text="<org>-orbu")
            self.service_preview.config(text="<org>-orbu")
            self.header_preview.config(text="<Organization> - Orbu")

    def validate(self) -> bool:
        """Validate organization name."""
        name = self.org_name_var.get().strip()

        if not name:
            messagebox.showwarning("Required", "Please enter an organization name.")
            return False

        is_valid, error_msg = validate_org_name(name)
        if not is_valid:
            messagebox.showwarning("Invalid Name", error_msg)
            return False

        return True

    def get_data(self) -> Dict[str, Any]:
        """Return organization data."""
        name = self.org_name_var.get().strip()
        return {
            'org_name': name,
            'org_slug': slugify_org_name(name),
        }
