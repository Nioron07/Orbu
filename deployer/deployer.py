"""
Orbu Deployer - Standalone GUI application for deploying Orbu to cloud platforms.

This is the main entry point for the deployer wizard.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Add parent directory to path for imports when running from source
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = sys._MEIPASS
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from ui.wizard import WizardController
from ui.step_platform import StepPlatform
from ui.step_prerequisites import StepPrerequisites
from ui.step_project import StepProject
from ui.step_database import StepDatabase
from ui.step_review import StepReview
from ui.step_deploy import StepDeploy
from ui.step_complete import StepComplete


def configure_styles(root: tk.Tk):
    """Configure ttk styles for a modern look."""
    style = ttk.Style()

    # Try to use a modern theme
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'vista' in available_themes:
        style.theme_use('vista')

    # Configure custom styles
    style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'))
    style.configure('Subtitle.TLabel', font=('Segoe UI', 11), foreground='#666')
    style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'))
    style.configure('Info.TLabel', font=('Segoe UI', 10), foreground='#666')

    # Card style for platform selection
    style.configure('Card.TFrame', relief='solid', borderwidth=1)
    style.configure('CardTitle.TLabel', font=('Segoe UI', 14, 'bold'))
    style.configure('CardDesc.TLabel', font=('Segoe UI', 10), foreground='#666')

    # Status indicators
    style.configure('Success.TLabel', foreground='green')
    style.configure('Error.TLabel', foreground='red')
    style.configure('Warning.TLabel', foreground='orange')
    style.configure('Pending.TLabel', foreground='#999')

    # Buttons
    style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'))

    return style


def center_window(root: tk.Tk, width: int, height: int):
    """Center the window on the screen."""
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f'{width}x{height}+{x}+{y}')


def main():
    """Main entry point for the deployer."""
    # Create root window
    root = tk.Tk()
    root.title("Orbu Deployer")

    # Set window icon if available
    icon_path = os.path.join(BASE_DIR, 'assets', 'icon.ico')
    if os.path.exists(icon_path):
        try:
            root.iconbitmap(icon_path)
        except tk.TclError:
            pass  # Icon format not supported on this platform

    # Configure styles
    configure_styles(root)

    # Center and size window
    center_window(root, 700, 550)

    # Handle window close
    def on_closing():
        if messagebox.askyesno("Exit", "Are you sure you want to exit the deployer?"):
            root.quit()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Create wizard controller
    wizard = WizardController(root)

    # Add wizard steps
    wizard.add_step(StepPlatform)
    wizard.add_step(StepPrerequisites)
    wizard.add_step(StepProject)
    wizard.add_step(StepDatabase)
    wizard.add_step(StepReview)
    wizard.add_step(StepDeploy)
    wizard.add_step(StepComplete)

    # Start the wizard
    wizard.start()

    # Run the main loop
    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


if __name__ == '__main__':
    main()
