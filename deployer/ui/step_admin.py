"""
Step 5: Admin Account Configuration

Collects admin email and password for the initial admin user.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, ScrollableFrame, COLORS


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password meets requirements.

    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    return True, ""


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


class StepAdmin(WizardStep):
    """Admin account configuration step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Title
        title = tk.Label(
            self,
            text="Admin Account",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(20, 10))

        subtitle = tk.Label(
            self,
            text="Create the initial administrator account for Orbu",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 15))

        # Scrollable form
        scroll_container = ScrollableFrame(self, bg=COLORS['card_bg'])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=30)

        form_frame = scroll_container.scrollable_frame

        # Info box
        info_frame = tk.Frame(form_frame, bg='#e3f2fd', padx=15, pady=10)
        info_frame.pack(fill=tk.X, pady=(10, 20))

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
            text="This account will be the initial admin for the Orbu management UI.\nYou can add more users after deployment.",
            font=('Segoe UI', 9),
            bg='#e3f2fd',
            fg='#1565c0',
            justify='left'
        )
        info_text.pack(side=tk.LEFT, padx=10)

        # Email
        email_label = tk.Label(
            form_frame,
            text="Admin Email",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        email_label.pack(anchor=tk.W, pady=(10, 5))

        self.email_var = tk.StringVar()
        self.email_entry = ttk.Entry(
            form_frame,
            textvariable=self.email_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.email_entry.pack(anchor=tk.W)

        email_hint = tk.Label(
            form_frame,
            text="This email will be used to log in",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        email_hint.pack(anchor=tk.W, pady=(2, 0))

        # Password
        password_label = tk.Label(
            form_frame,
            text="Password",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        password_label.pack(anchor=tk.W, pady=(20, 5))

        password_container = tk.Frame(form_frame, bg=COLORS['card_bg'])
        password_container.pack(anchor=tk.W)

        self.password_var = tk.StringVar()
        self.password_var.trace_add('write', self._on_password_change)
        self.password_entry = ttk.Entry(
            password_container,
            textvariable=self.password_var,
            font=('Segoe UI', 10),
            width=30,
            show='\u2022'
        )
        self.password_entry.pack(side=tk.LEFT)

        self.show_password = tk.BooleanVar(value=False)
        self.show_password_check = ttk.Checkbutton(
            password_container,
            text="Show",
            variable=self.show_password,
            command=self._toggle_password
        )
        self.show_password_check.pack(side=tk.LEFT, padx=(10, 0))

        # Password requirements
        req_frame = tk.Frame(form_frame, bg=COLORS['card_bg'])
        req_frame.pack(anchor=tk.W, pady=(5, 0))

        req_label = tk.Label(
            req_frame,
            text="Password requirements:",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        req_label.pack(anchor=tk.W)

        self.req_labels = {}
        requirements = [
            ('length', 'At least 8 characters'),
            ('upper', 'At least one uppercase letter'),
            ('lower', 'At least one lowercase letter'),
            ('number', 'At least one number'),
        ]

        for req_id, req_text in requirements:
            label = tk.Label(
                req_frame,
                text=f"  \u2022 {req_text}",
                font=('Segoe UI', 9),
                bg=COLORS['card_bg'],
                fg=COLORS['text_secondary']
            )
            label.pack(anchor=tk.W)
            self.req_labels[req_id] = label

        # Confirm Password
        confirm_label = tk.Label(
            form_frame,
            text="Confirm Password",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        confirm_label.pack(anchor=tk.W, pady=(20, 5))

        self.confirm_var = tk.StringVar()
        self.confirm_var.trace_add('write', self._on_confirm_change)
        self.confirm_entry = ttk.Entry(
            form_frame,
            textvariable=self.confirm_var,
            font=('Segoe UI', 10),
            width=30,
            show='\u2022'
        )
        self.confirm_entry.pack(anchor=tk.W)

        self.match_label = tk.Label(
            form_frame,
            text="",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        self.match_label.pack(anchor=tk.W, pady=(2, 0))

        # Add some bottom padding
        spacer = tk.Frame(form_frame, height=20, bg=COLORS['card_bg'])
        spacer.pack()

    def _toggle_password(self):
        """Toggle password visibility."""
        if self.show_password.get():
            self.password_entry.config(show='')
            self.confirm_entry.config(show='')
        else:
            self.password_entry.config(show='\u2022')
            self.confirm_entry.config(show='\u2022')

    def _on_password_change(self, *args):
        """Update password requirement indicators."""
        password = self.password_var.get()

        # Check each requirement
        checks = {
            'length': len(password) >= 8,
            'upper': bool(re.search(r'[A-Z]', password)),
            'lower': bool(re.search(r'[a-z]', password)),
            'number': bool(re.search(r'\d', password)),
        }

        for req_id, met in checks.items():
            if met:
                self.req_labels[req_id].config(fg=COLORS['success'])
            else:
                self.req_labels[req_id].config(fg=COLORS['text_secondary'])

        # Also update match indicator
        self._on_confirm_change()

    def _on_confirm_change(self, *args):
        """Update password match indicator."""
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not confirm:
            self.match_label.config(text="")
        elif password == confirm:
            self.match_label.config(text="\u2713 Passwords match", fg=COLORS['success'])
        else:
            self.match_label.config(text="\u2717 Passwords do not match", fg=COLORS['error'])

    def validate(self) -> bool:
        """Validate admin credentials."""
        email = self.email_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        # Validate email
        if not email:
            messagebox.showwarning("Required", "Please enter an admin email.")
            return False

        if not validate_email(email):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return False

        # Validate password
        if not password:
            messagebox.showwarning("Required", "Please enter a password.")
            return False

        is_valid, error_msg = validate_password(password)
        if not is_valid:
            messagebox.showwarning("Invalid Password", error_msg)
            return False

        # Check passwords match
        if password != confirm:
            messagebox.showwarning("Password Mismatch", "Passwords do not match.")
            return False

        return True

    def get_data(self) -> Dict[str, Any]:
        """Return admin credentials."""
        return {
            'admin_email': self.email_var.get().strip().lower(),
            'admin_password': self.password_var.get(),
        }
