"""
Wizard Controller - Manages the multi-step deployment wizard.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional, Type


# Color scheme
COLORS = {
    'bg': '#f5f5f5',
    'card_bg': '#ffffff',
    'card_hover': '#e3f2fd',
    'card_selected': '#bbdefb',
    'card_disabled': '#eeeeee',
    'primary': '#1976d2',
    'success': '#388e3c',
    'error': '#d32f2f',
    'text': '#212121',
    'text_secondary': '#666666',
    'border': '#e0e0e0',
}


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
        self.steps: list[tk.Frame] = []
        self.current_step = 0
        self.data: Dict[str, Any] = {}

        # Configure root window
        self.root.title("Orbu Deployer")
        self.root.geometry("950x750")
        self.root.resizable(True, True)
        self.root.minsize(850, 650)
        self.root.configure(bg=COLORS['bg'])

        # Configure ttk styles
        self._configure_styles()

        # Create main container with background
        self.main_frame = tk.Frame(root, bg=COLORS['bg'], padx=15, pady=15)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Header with step indicator
        self.header_frame = tk.Frame(self.main_frame, bg=COLORS['bg'])
        self.header_frame.pack(fill=tk.X, pady=(0, 15))

        self.title_label = tk.Label(
            self.header_frame,
            text="Orbu Deployer",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['text']
        )
        self.title_label.pack(side=tk.LEFT)

        self.step_label = tk.Label(
            self.header_frame,
            text="Step 1 of 7",
            font=('Segoe UI', 11),
            bg=COLORS['bg'],
            fg=COLORS['text_secondary']
        )
        self.step_label.pack(side=tk.RIGHT)

        # Content area (where step frames go) - white card background
        self.content_container = tk.Frame(self.main_frame, bg=COLORS['card_bg'], relief='flat', bd=1)
        self.content_container.pack(fill=tk.BOTH, expand=True, pady=10)

        # Add a subtle border
        self.content_container.configure(highlightbackground=COLORS['border'], highlightthickness=1)

        self.content_frame = tk.Frame(self.content_container, bg=COLORS['card_bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Navigation buttons
        self.nav_frame = tk.Frame(self.main_frame, bg=COLORS['bg'])
        self.nav_frame.pack(fill=tk.X, pady=(15, 0))

        self.back_button = ttk.Button(
            self.nav_frame,
            text="< Back",
            command=self.go_back,
            state=tk.DISABLED,
            style='Nav.TButton'
        )
        self.back_button.pack(side=tk.LEFT)

        self.next_button = ttk.Button(
            self.nav_frame,
            text="Next >",
            command=self.go_next,
            style='Primary.TButton'
        )
        self.next_button.pack(side=tk.RIGHT)

        self.cancel_button = ttk.Button(
            self.nav_frame,
            text="Cancel",
            command=self.cancel,
            style='Nav.TButton'
        )
        self.cancel_button.pack(side=tk.RIGHT, padx=(0, 10))

    def _configure_styles(self):
        """Configure ttk styles for the wizard."""
        style = ttk.Style()

        # Try to use a modern theme
        try:
            style.theme_use('vista')
        except:
            try:
                style.theme_use('clam')
            except:
                pass

        # Primary button (blue)
        style.configure('Primary.TButton', font=('Segoe UI', 10), padding=(15, 8))

        # Navigation button
        style.configure('Nav.TButton', font=('Segoe UI', 10), padding=(15, 8))

        # Labels
        style.configure('Title.TLabel', font=('Segoe UI', 14, 'bold'), background=COLORS['card_bg'])
        style.configure('Subtitle.TLabel', font=('Segoe UI', 10), foreground=COLORS['text_secondary'], background=COLORS['card_bg'])

    def add_step(self, step_class: Type[tk.Frame], **kwargs):
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
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel?"):
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


class ScrollableFrame(tk.Frame):
    """A scrollable frame that properly handles mouse wheel events."""

    def __init__(self, parent, bg='white', **kwargs):
        super().__init__(parent, bg=bg)

        # Create canvas
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg)

        # Configure canvas scrolling
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Bind canvas resize to update scrollable frame width
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Pack widgets
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel
        self._bind_mousewheel()

    def _on_frame_configure(self, event):
        """Reset the scroll region to encompass the scrollable frame."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update the scrollable frame width when canvas resizes."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self):
        """Bind mouse wheel events for scrolling."""
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)

    def _on_enter(self, event):
        """Bind mousewheel when mouse enters."""
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_leave(self, event):
        """Unbind mousewheel when mouse leaves."""
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows/Mac
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class WizardStep(tk.Frame):
    """Base class for wizard steps."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, bg=COLORS['card_bg'])
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
