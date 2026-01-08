"""
Wizard Controller - Manages the multi-step deployment wizard.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional, Type


class WizardController:
    """
    Controls the wizard flow between steps.

    Each step is a Frame subclass that implements:
    - validate() -> bool: Check if step data is valid
    - get_data() -> dict: Return step data
    - on_enter(): Called when step becomes visible
    - on_leave(): Called when leaving step
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.steps: list[ttk.Frame] = []
        self.current_step = 0
        self.data: Dict[str, Any] = {}

        # Configure root window
        self.root.title("Orbu Deployer")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        self.root.minsize(600, 450)

        # Create main container
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with step indicator
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))

        self.title_label = ttk.Label(
            self.header_frame,
            text="Orbu Deployer",
            font=('Segoe UI', 16, 'bold')
        )
        self.title_label.pack(side=tk.LEFT)

        self.step_label = ttk.Label(
            self.header_frame,
            text="Step 1 of 7",
            font=('Segoe UI', 10)
        )
        self.step_label.pack(side=tk.RIGHT)

        # Content area (where step frames go)
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Navigation buttons
        self.nav_frame = ttk.Frame(self.main_frame)
        self.nav_frame.pack(fill=tk.X, pady=(10, 0))

        self.back_button = ttk.Button(
            self.nav_frame,
            text="< Back",
            command=self.go_back,
            state=tk.DISABLED
        )
        self.back_button.pack(side=tk.LEFT)

        self.next_button = ttk.Button(
            self.nav_frame,
            text="Next >",
            command=self.go_next
        )
        self.next_button.pack(side=tk.RIGHT)

        self.cancel_button = ttk.Button(
            self.nav_frame,
            text="Cancel",
            command=self.cancel
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))

    def add_step(self, step_class: Type[ttk.Frame], **kwargs):
        """Add a step to the wizard."""
        step = step_class(self.content_frame, self, **kwargs)
        self.steps.append(step)

    def show_step(self, index: int):
        """Show a specific step."""
        if 0 <= index < len(self.steps):
            # Hide current step
            if self.steps:
                current = self.steps[self.current_step]
                if hasattr(current, 'on_leave'):
                    current.on_leave()
                current.pack_forget()

            # Show new step
            self.current_step = index
            step = self.steps[index]
            step.pack(fill=tk.BOTH, expand=True)
            if hasattr(step, 'on_enter'):
                step.on_enter()

            # Update navigation
            self._update_navigation()

    def _update_navigation(self):
        """Update navigation button states."""
        # Update step label
        self.step_label.config(text=f"Step {self.current_step + 1} of {len(self.steps)}")

        # Back button
        if self.current_step == 0:
            self.back_button.config(state=tk.DISABLED)
        else:
            self.back_button.config(state=tk.NORMAL)

        # Next button - changes to "Deploy" on review step, "Finish" on complete
        if self.current_step == len(self.steps) - 2:  # Deploy step
            self.next_button.config(text="Deploy", state=tk.DISABLED)
        elif self.current_step == len(self.steps) - 1:  # Complete step
            self.next_button.config(text="Finish", state=tk.NORMAL)
        else:
            self.next_button.config(text="Next >", state=tk.NORMAL)

    def go_next(self):
        """Go to the next step."""
        if self.current_step < len(self.steps) - 1:
            current = self.steps[self.current_step]

            # Validate current step
            if hasattr(current, 'validate') and not current.validate():
                return

            # Get data from current step
            if hasattr(current, 'get_data'):
                self.data.update(current.get_data())

            self.show_step(self.current_step + 1)
        else:
            # Last step - close wizard
            self.root.quit()

    def go_back(self):
        """Go to the previous step."""
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def cancel(self):
        """Cancel the wizard."""
        if tk.messagebox.askyesno("Cancel", "Are you sure you want to cancel?"):
            self.root.quit()

    def start(self):
        """Start the wizard."""
        if self.steps:
            self.show_step(0)

    def set_next_enabled(self, enabled: bool):
        """Enable or disable the Next button."""
        self.next_button.config(state=tk.NORMAL if enabled else tk.DISABLED)

    def set_next_text(self, text: str):
        """Set the Next button text."""
        self.next_button.config(text=text)

    def hide_navigation(self):
        """Hide navigation buttons (for deployment step)."""
        self.back_button.pack_forget()
        self.next_button.pack_forget()
        self.cancel_button.pack_forget()

    def show_finish_button(self):
        """Show only the Finish button (for completion step)."""
        self.back_button.pack_forget()
        self.cancel_button.pack_forget()
        self.next_button.config(text="Finish", state=tk.NORMAL)
        self.next_button.pack(side=tk.RIGHT)


class WizardStep(ttk.Frame):
    """Base class for wizard steps."""

    def __init__(self, parent: ttk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent)
        self.wizard = wizard

    def validate(self) -> bool:
        """Validate step data. Override in subclass."""
        return True

    def get_data(self) -> Dict[str, Any]:
        """Get step data. Override in subclass."""
        return {}

    def on_enter(self):
        """Called when step becomes visible. Override in subclass."""
        pass

    def on_leave(self):
        """Called when leaving step. Override in subclass."""
        pass
