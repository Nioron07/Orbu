"""
Step 1: Platform Selection

Allows user to choose between GCP, Azure, and AWS.
Azure and AWS are marked as "Coming Soon" and disabled.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from .wizard import WizardStep, WizardController


class PlatformCard(ttk.Frame):
    """A clickable card for platform selection."""

    def __init__(self, parent, name: str, description: str, enabled: bool = True,
                 badge: str = None, on_click=None):
        super().__init__(parent, padding=15)

        self.enabled = enabled
        self.on_click = on_click
        self.selected = False

        # Style based on enabled state
        if enabled:
            self.configure(style='Card.TFrame')
        else:
            self.configure(style='DisabledCard.TFrame')

        # Platform name
        name_label = ttk.Label(
            self,
            text=name,
            font=('Segoe UI', 12, 'bold'),
            foreground='#333' if enabled else '#999'
        )
        name_label.pack(anchor=tk.W)

        # Badge (Coming Soon)
        if badge:
            badge_label = ttk.Label(
                self,
                text=badge,
                font=('Segoe UI', 9),
                foreground='#ff6600',
                background='#fff3e0',
                padding=(5, 2)
            )
            badge_label.pack(anchor=tk.W, pady=(5, 0))

        # Description
        desc_label = ttk.Label(
            self,
            text=description,
            font=('Segoe UI', 9),
            foreground='#666' if enabled else '#aaa',
            wraplength=180
        )
        desc_label.pack(anchor=tk.W, pady=(5, 0))

        # Bind click events
        if enabled:
            self.bind('<Button-1>', self._on_click)
            name_label.bind('<Button-1>', self._on_click)
            desc_label.bind('<Button-1>', self._on_click)
            self.bind('<Enter>', self._on_enter)
            self.bind('<Leave>', self._on_leave)
        else:
            self.bind('<Button-1>', self._on_disabled_click)
            name_label.bind('<Button-1>', self._on_disabled_click)
            desc_label.bind('<Button-1>', self._on_disabled_click)

    def _on_click(self, event):
        if self.on_click:
            self.on_click()

    def _on_disabled_click(self, event):
        messagebox.showinfo(
            "Coming Soon",
            "This platform is not yet supported.\n\n"
            "Please use Google Cloud Platform for now."
        )

    def _on_enter(self, event):
        if self.enabled and not self.selected:
            self.configure(style='HoverCard.TFrame')

    def _on_leave(self, event):
        if self.enabled and not self.selected:
            self.configure(style='Card.TFrame')

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self.configure(style='SelectedCard.TFrame')
        else:
            self.configure(style='Card.TFrame')


class StepPlatform(WizardStep):
    """Platform selection step."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.selected_platform = None
        self.cards = []

        # Create custom styles
        self._create_styles()

        # Title
        title = ttk.Label(
            self,
            text="Choose Your Cloud Platform",
            font=('Segoe UI', 14, 'bold')
        )
        title.pack(pady=(20, 10))

        subtitle = ttk.Label(
            self,
            text="Select the cloud platform where you want to deploy Orbu",
            font=('Segoe UI', 10),
            foreground='#666'
        )
        subtitle.pack(pady=(0, 30))

        # Cards container
        cards_frame = ttk.Frame(self)
        cards_frame.pack(expand=True)

        # GCP Card
        self.gcp_card = PlatformCard(
            cards_frame,
            name="Google Cloud Platform",
            description="Deploy to Cloud Run with Cloud SQL database",
            enabled=True,
            on_click=lambda: self._select_platform('gcp', self.gcp_card)
        )
        self.gcp_card.pack(side=tk.LEFT, padx=10)
        self.cards.append(self.gcp_card)

        # Azure Card
        self.azure_card = PlatformCard(
            cards_frame,
            name="Microsoft Azure",
            description="Deploy to Container Apps with Azure Database",
            enabled=False,
            badge="Coming Soon"
        )
        self.azure_card.pack(side=tk.LEFT, padx=10)
        self.cards.append(self.azure_card)

        # AWS Card
        self.aws_card = PlatformCard(
            cards_frame,
            name="Amazon Web Services",
            description="Deploy to App Runner with RDS database",
            enabled=False,
            badge="Coming Soon"
        )
        self.aws_card.pack(side=tk.LEFT, padx=10)
        self.cards.append(self.aws_card)

    def _create_styles(self):
        """Create custom styles for cards."""
        style = ttk.Style()

        # Normal card
        style.configure('Card.TFrame', background='#ffffff', relief='solid', borderwidth=1)

        # Disabled card
        style.configure('DisabledCard.TFrame', background='#f5f5f5', relief='solid', borderwidth=1)

        # Hover card
        style.configure('HoverCard.TFrame', background='#e3f2fd', relief='solid', borderwidth=1)

        # Selected card
        style.configure('SelectedCard.TFrame', background='#bbdefb', relief='solid', borderwidth=2)

    def _select_platform(self, platform: str, card: PlatformCard):
        """Handle platform selection."""
        self.selected_platform = platform

        # Update card styles
        for c in self.cards:
            c.set_selected(False)
        card.set_selected(True)

        # Enable next button
        self.wizard.set_next_enabled(True)

    def on_enter(self):
        """Called when step becomes visible."""
        # Disable next until platform selected
        if not self.selected_platform:
            self.wizard.set_next_enabled(False)

    def validate(self) -> bool:
        """Validate that a platform is selected."""
        if not self.selected_platform:
            messagebox.showwarning(
                "Select Platform",
                "Please select a cloud platform to continue."
            )
            return False
        return True

    def get_data(self) -> Dict[str, Any]:
        """Return selected platform."""
        return {'platform': self.selected_platform}
