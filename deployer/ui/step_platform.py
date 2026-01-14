"""
Step 1: Platform Selection

Allows user to choose between GCP, Azure, and AWS.
Azure and AWS are marked as "Coming Soon" and disabled.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, COLORS


class PlatformCard(tk.Frame):
    """A clickable card for platform selection."""

    CARD_WIDTH = 260
    CARD_HEIGHT = 160

    def __init__(self, parent, name: str, description: str, enabled: bool = True,
                 badge: str = None, on_click=None):
        super().__init__(
            parent,
            bg=COLORS['card_bg'] if enabled else COLORS['card_disabled'],
            highlightbackground=COLORS['border'],
            highlightthickness=1,
            width=self.CARD_WIDTH,
            height=self.CARD_HEIGHT
        )
        self.pack_propagate(False)  # Fixed size

        self.enabled = enabled
        self.on_click = on_click
        self.selected = False
        self._bg_color = COLORS['card_bg'] if enabled else COLORS['card_disabled']

        # Inner padding frame
        inner = tk.Frame(self, bg=self._bg_color, padx=15, pady=15)
        inner.pack(fill=tk.BOTH, expand=True)

        # Platform name
        self.name_label = tk.Label(
            inner,
            text=name,
            font=('Segoe UI', 12, 'bold'),
            fg=COLORS['text'] if enabled else '#999999',
            bg=self._bg_color,
            anchor='w'
        )
        self.name_label.pack(anchor=tk.W)

        # Badge (Coming Soon)
        if badge:
            badge_frame = tk.Frame(inner, bg='#fff3e0', padx=6, pady=2)
            badge_frame.pack(anchor=tk.W, pady=(8, 0))
            badge_label = tk.Label(
                badge_frame,
                text=badge,
                font=('Segoe UI', 9),
                fg='#e65100',
                bg='#fff3e0'
            )
            badge_label.pack()

        # Description
        self.desc_label = tk.Label(
            inner,
            text=description,
            font=('Segoe UI', 9),
            fg=COLORS['text_secondary'] if enabled else '#aaaaaa',
            bg=self._bg_color,
            wraplength=220,
            justify='left',
            anchor='w'
        )
        self.desc_label.pack(anchor=tk.W, pady=(10, 0))

        # Bind click events to all widgets
        if enabled:
            for widget in [self, inner, self.name_label, self.desc_label]:
                widget.bind('<Button-1>', self._on_click)
                widget.bind('<Enter>', self._on_enter)
                widget.bind('<Leave>', self._on_leave)
        else:
            for widget in [self, inner, self.name_label, self.desc_label]:
                widget.bind('<Button-1>', self._on_disabled_click)

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
            self._set_bg(COLORS['card_hover'])

    def _on_leave(self, event):
        if self.enabled and not self.selected:
            self._set_bg(COLORS['card_bg'])

    def _set_bg(self, color):
        """Set background color for all widgets."""
        self._bg_color = color
        self.configure(bg=color)
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.configure(bg=color)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.configure(bg=color)

    def set_selected(self, selected: bool):
        self.selected = selected
        if selected:
            self._set_bg(COLORS['card_selected'])
            self.configure(highlightbackground=COLORS['primary'], highlightthickness=2)
        else:
            self._set_bg(COLORS['card_bg'])
            self.configure(highlightbackground=COLORS['border'], highlightthickness=1)


class StepPlatform(WizardStep):
    """Platform selection step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        self.selected_platform = None
        self.cards = []

        # Title
        title = tk.Label(
            self,
            text="Choose Your Cloud Platform",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(30, 10))

        subtitle = tk.Label(
            self,
            text="Select the cloud platform where you want to deploy Orbu",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 40))

        # Cards container - centered
        cards_frame = tk.Frame(self, bg=COLORS['card_bg'])
        cards_frame.pack(expand=True)

        # GCP Card
        self.gcp_card = PlatformCard(
            cards_frame,
            name="Google Cloud Platform",
            description="Deploy to Cloud Run with Cloud SQL database",
            enabled=True,
            on_click=lambda: self._select_platform('gcp', self.gcp_card)
        )
        self.gcp_card.pack(side=tk.LEFT, padx=15, pady=10)
        self.cards.append(self.gcp_card)

        # Azure Card
        self.azure_card = PlatformCard(
            cards_frame,
            name="Microsoft Azure",
            description="Deploy to Container Apps with Azure Database",
            enabled=False,
            badge="Coming Soon"
        )
        self.azure_card.pack(side=tk.LEFT, padx=15, pady=10)
        self.cards.append(self.azure_card)

        # AWS Card
        self.aws_card = PlatformCard(
            cards_frame,
            name="Amazon Web Services",
            description="Deploy to App Runner with RDS database",
            enabled=False,
            badge="Coming Soon"
        )
        self.aws_card.pack(side=tk.LEFT, padx=15, pady=10)
        self.cards.append(self.aws_card)

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
