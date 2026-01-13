"""
Step 7: Completion

Shows deployment success/failure and service URL.
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, COLORS


class StepComplete(WizardStep):
    """Completion step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Container for dynamic content
        self.content_frame = tk.Frame(self, bg=COLORS['card_bg'])
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
        icon = tk.Label(
            self.content_frame,
            text="\u2713",
            font=('Segoe UI', 48),
            bg=COLORS['card_bg'],
            fg=COLORS['success']
        )
        icon.pack(pady=(40, 15))

        # Title
        title = tk.Label(
            self.content_frame,
            text="Deployment Successful!",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['success']
        )
        title.pack(pady=(0, 8))

        # Subtitle
        subtitle = tk.Label(
            self.content_frame,
            text="Your Orbu instance is now running on Google Cloud Run",
            font=('Segoe UI', 11),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 25))

        if url:
            # URL section
            url_label = tk.Label(
                self.content_frame,
                text="Service URL:",
                font=('Segoe UI', 10, 'bold'),
                bg=COLORS['card_bg'],
                fg=COLORS['text']
            )
            url_label.pack()

            url_frame = tk.Frame(self.content_frame, bg=COLORS['card_bg'])
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
            buttons_frame = tk.Frame(self.content_frame, bg=COLORS['card_bg'])
            buttons_frame.pack(pady=25)

            open_button = ttk.Button(
                buttons_frame,
                text="Open in Browser",
                command=lambda: webbrowser.open(url)
            )
            open_button.pack(side=tk.LEFT, padx=10)

        # Info section
        info_frame = tk.Frame(self.content_frame, bg=COLORS['card_bg'])
        info_frame.pack(pady=15, padx=80)

        info_label = tk.Label(
            info_frame,
            text="Next Steps:",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        info_label.pack(anchor=tk.W)

        steps = [
            "1. Open the URL above to access your Orbu instance",
            "2. Create a client with your Acumatica credentials",
            "3. Deploy endpoints for your Acumatica services",
        ]

        for step in steps:
            step_label = tk.Label(
                info_frame,
                text=step,
                font=('Segoe UI', 10),
                bg=COLORS['card_bg'],
                fg=COLORS['text_secondary']
            )
            step_label.pack(anchor=tk.W, pady=3)

    def _show_failure(self):
        """Show failure message."""
        # Failure icon
        icon = tk.Label(
            self.content_frame,
            text="\u2717",
            font=('Segoe UI', 48),
            bg=COLORS['card_bg'],
            fg=COLORS['error']
        )
        icon.pack(pady=(40, 15))

        # Title
        title = tk.Label(
            self.content_frame,
            text="Deployment Failed",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['error']
        )
        title.pack(pady=(0, 8))

        # Subtitle
        subtitle = tk.Label(
            self.content_frame,
            text="There was an error during deployment",
            font=('Segoe UI', 11),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 25))

        # Help text
        help_frame = tk.Frame(self.content_frame, bg=COLORS['card_bg'])
        help_frame.pack(pady=15, padx=80)

        help_label = tk.Label(
            help_frame,
            text="Troubleshooting:",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        help_label.pack(anchor=tk.W)

        tips = [
            "\u2022 Check the deployment log for error details",
            "\u2022 Verify your GCP project has billing enabled",
            "\u2022 Ensure Cloud SQL instance exists and is accessible",
            "\u2022 Confirm your database credentials are correct",
            "\u2022 Make sure you have sufficient GCP permissions",
        ]

        for tip in tips:
            tip_label = tk.Label(
                help_frame,
                text=tip,
                font=('Segoe UI', 10),
                bg=COLORS['card_bg'],
                fg=COLORS['text_secondary']
            )
            tip_label.pack(anchor=tk.W, pady=3)

    def get_data(self) -> Dict[str, Any]:
        """Return completion data."""
        return {}
