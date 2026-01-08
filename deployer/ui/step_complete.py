"""
Step 7: Completion

Shows deployment success/failure and service URL.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Dict, Any

from .wizard import WizardStep, WizardController


class StepComplete(WizardStep):
    """Completion step."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Container for dynamic content
        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill=tk.BOTH, expand=True)

    def on_enter(self):
        """Populate content based on deployment result."""
        # Clear existing content
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Show finish button only
        self.wizard.show_finish_button()

        success = self.wizard.data.get('deployment_success', False)
        url = self.wizard.data.get('service_url')

        if success:
            self._show_success(url)
        else:
            self._show_failure()

    def _show_success(self, url: str):
        """Show success message and URL."""
        # Success icon
        icon = ttk.Label(
            self.content_frame,
            text="✓",
            font=('Segoe UI', 48),
            foreground='green'
        )
        icon.pack(pady=(50, 20))

        # Title
        title = ttk.Label(
            self.content_frame,
            text="Deployment Successful!",
            font=('Segoe UI', 18, 'bold'),
            foreground='green'
        )
        title.pack(pady=(0, 10))

        # Subtitle
        subtitle = ttk.Label(
            self.content_frame,
            text="Your Orbu instance is now running on Google Cloud Run",
            font=('Segoe UI', 11),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 30))

        if url:
            # URL section
            url_label = ttk.Label(
                self.content_frame,
                text="Service URL:",
                font=('Segoe UI', 10, 'bold')
            )
            url_label.pack()

            url_frame = ttk.Frame(self.content_frame)
            url_frame.pack(pady=10)

            url_entry = ttk.Entry(
                url_frame,
                font=('Consolas', 11),
                width=50,
                justify='center'
            )
            url_entry.insert(0, url)
            url_entry.config(state='readonly')
            url_entry.pack(side=tk.LEFT)

            # Copy button
            def copy_url():
                self.content_frame.clipboard_clear()
                self.content_frame.clipboard_append(url)
                copy_button.config(text="Copied!")
                self.after(2000, lambda: copy_button.config(text="Copy"))

            copy_button = ttk.Button(
                url_frame,
                text="Copy",
                command=copy_url,
                width=8
            )
            copy_button.pack(side=tk.LEFT, padx=(10, 0))

            # Buttons
            buttons_frame = ttk.Frame(self.content_frame)
            buttons_frame.pack(pady=30)

            open_button = ttk.Button(
                buttons_frame,
                text="Open in Browser",
                command=lambda: webbrowser.open(url)
            )
            open_button.pack(side=tk.LEFT, padx=10)

        # Info section
        info_frame = ttk.Frame(self.content_frame)
        info_frame.pack(pady=20)

        info_label = ttk.Label(
            info_frame,
            text="Next Steps:",
            font=('Segoe UI', 10, 'bold')
        )
        info_label.pack(anchor=tk.W)

        steps = [
            "1. Open the URL above to access your Orbu instance",
            "2. Create a client with your Acumatica credentials",
            "3. Deploy endpoints for your Acumatica services",
        ]

        for step in steps:
            step_label = ttk.Label(
                info_frame,
                text=step,
                font=('Segoe UI', 10),
                foreground='#666'
            )
            step_label.pack(anchor=tk.W, pady=2)

    def _show_failure(self):
        """Show failure message."""
        # Failure icon
        icon = ttk.Label(
            self.content_frame,
            text="✗",
            font=('Segoe UI', 48),
            foreground='red'
        )
        icon.pack(pady=(50, 20))

        # Title
        title = ttk.Label(
            self.content_frame,
            text="Deployment Failed",
            font=('Segoe UI', 18, 'bold'),
            foreground='red'
        )
        title.pack(pady=(0, 10))

        # Subtitle
        subtitle = ttk.Label(
            self.content_frame,
            text="There was an error during deployment",
            font=('Segoe UI', 11),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 30))

        # Help text
        help_frame = ttk.Frame(self.content_frame)
        help_frame.pack(pady=20)

        help_label = ttk.Label(
            help_frame,
            text="Troubleshooting:",
            font=('Segoe UI', 10, 'bold')
        )
        help_label.pack(anchor=tk.W)

        tips = [
            "• Check the deployment log for error details",
            "• Verify your GCP project has billing enabled",
            "• Ensure Cloud SQL instance exists and is accessible",
            "• Confirm your database credentials are correct",
            "• Make sure you have sufficient GCP permissions",
        ]

        for tip in tips:
            tip_label = ttk.Label(
                help_frame,
                text=tip,
                font=('Segoe UI', 10),
                foreground='#666'
            )
            tip_label.pack(anchor=tk.W, pady=2)

    def get_data(self) -> Dict[str, Any]:
        """Return completion data."""
        return {}
