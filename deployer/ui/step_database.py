"""
Step 4: Database Configuration

Collects database connection details and credentials.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any

from ui.wizard import WizardStep, WizardController, ScrollableFrame, COLORS


class StepDatabase(WizardStep):
    """Database configuration step."""

    def __init__(self, parent: tk.Frame, wizard: WizardController, **kwargs):
        super().__init__(parent, wizard)

        # Title
        title = tk.Label(
            self,
            text="Database Configuration",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        title.pack(pady=(20, 10))

        subtitle = tk.Label(
            self,
            text="Configure your PostgreSQL database connection",
            font=('Segoe UI', 10),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        subtitle.pack(pady=(0, 15))

        # Scrollable form
        scroll_container = ScrollableFrame(self, bg=COLORS['card_bg'])
        scroll_container.pack(fill=tk.BOTH, expand=True, padx=30)

        form_frame = scroll_container.scrollable_frame

        # Connection Type
        type_label = tk.Label(
            form_frame,
            text="Connection Type",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        type_label.pack(anchor=tk.W, pady=(10, 8))

        self.connection_type = tk.StringVar(value="unix_socket")

        types_frame = tk.Frame(form_frame, bg=COLORS['card_bg'])
        types_frame.pack(fill=tk.X, pady=5)

        self.type_unix = ttk.Radiobutton(
            types_frame,
            text="Cloud SQL (Same Project) - Recommended",
            variable=self.connection_type,
            value="unix_socket",
            command=self._on_type_change
        )
        self.type_unix.pack(anchor=tk.W, pady=2)

        self.type_connector = ttk.Radiobutton(
            types_frame,
            text="Cloud SQL (Different Project)",
            variable=self.connection_type,
            value="python_connector",
            command=self._on_type_change
        )
        self.type_connector.pack(anchor=tk.W, pady=2)

        self.type_external = ttk.Radiobutton(
            types_frame,
            text="External PostgreSQL",
            variable=self.connection_type,
            value="external",
            command=self._on_type_change
        )
        self.type_external.pack(anchor=tk.W, pady=2)

        # Dynamic fields container
        self.dynamic_frame = tk.Frame(form_frame, bg=COLORS['card_bg'])
        self.dynamic_frame.pack(fill=tk.X, pady=10)

        # Cloud SQL Instance (for unix_socket)
        self.instance_frame = tk.Frame(self.dynamic_frame, bg=COLORS['card_bg'])

        instance_label = tk.Label(
            self.instance_frame,
            text="Cloud SQL Instance Name",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        instance_label.pack(anchor=tk.W, pady=(10, 5))

        self.instance_var = tk.StringVar(value="orbu-db")
        self.instance_entry = ttk.Entry(
            self.instance_frame,
            textvariable=self.instance_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.instance_entry.pack(fill=tk.X)

        instance_hint = tk.Label(
            self.instance_frame,
            text="The Cloud SQL instance must already exist",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        instance_hint.pack(anchor=tk.W, pady=(2, 0))

        # Cloud SQL Connection String (for python_connector)
        self.connection_frame = tk.Frame(self.dynamic_frame, bg=COLORS['card_bg'])

        connection_label = tk.Label(
            self.connection_frame,
            text="Cloud SQL Connection String",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        connection_label.pack(anchor=tk.W, pady=(10, 5))

        self.connection_var = tk.StringVar()
        self.connection_entry = ttk.Entry(
            self.connection_frame,
            textvariable=self.connection_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.connection_entry.pack(fill=tk.X)

        connection_hint = tk.Label(
            self.connection_frame,
            text="Format: PROJECT:REGION:INSTANCE",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        connection_hint.pack(anchor=tk.W, pady=(2, 0))

        # External PostgreSQL Host/Port (for external)
        self.external_frame = tk.Frame(self.dynamic_frame, bg=COLORS['card_bg'])

        host_label = tk.Label(
            self.external_frame,
            text="PostgreSQL Host",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        host_label.pack(anchor=tk.W, pady=(10, 5))

        self.host_var = tk.StringVar()
        self.host_entry = ttk.Entry(
            self.external_frame,
            textvariable=self.host_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.host_entry.pack(fill=tk.X)

        port_label = tk.Label(
            self.external_frame,
            text="Port",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        port_label.pack(anchor=tk.W, pady=(10, 5))

        self.port_var = tk.StringVar(value="5432")
        self.port_entry = ttk.Entry(
            self.external_frame,
            textvariable=self.port_var,
            font=('Segoe UI', 10),
            width=10
        )
        self.port_entry.pack(anchor=tk.W)

        # Credentials section (always visible)
        creds_separator = ttk.Separator(form_frame, orient='horizontal')
        creds_separator.pack(fill=tk.X, pady=20)

        creds_label = tk.Label(
            form_frame,
            text="PostgreSQL Credentials",
            font=('Segoe UI', 12, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        creds_label.pack(anchor=tk.W)

        creds_hint = tk.Label(
            form_frame,
            text="These must match the credentials configured in your database",
            font=('Segoe UI', 9),
            bg=COLORS['card_bg'],
            fg=COLORS['text_secondary']
        )
        creds_hint.pack(anchor=tk.W, pady=(2, 10))

        # Username
        user_label = tk.Label(
            form_frame,
            text="Username",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        user_label.pack(anchor=tk.W, pady=(10, 5))

        self.user_var = tk.StringVar(value="orbu")
        self.user_entry = ttk.Entry(
            form_frame,
            textvariable=self.user_var,
            font=('Segoe UI', 10),
            width=30
        )
        self.user_entry.pack(anchor=tk.W)

        # Password
        password_label = tk.Label(
            form_frame,
            text="Password",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        password_label.pack(anchor=tk.W, pady=(10, 5))

        password_container = tk.Frame(form_frame, bg=COLORS['card_bg'])
        password_container.pack(anchor=tk.W)

        self.password_var = tk.StringVar()
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

        # Database name
        db_label = tk.Label(
            form_frame,
            text="Database Name",
            font=('Segoe UI', 10, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['text']
        )
        db_label.pack(anchor=tk.W, pady=(10, 5))

        self.db_var = tk.StringVar(value="orbu")
        self.db_entry = ttk.Entry(
            form_frame,
            textvariable=self.db_var,
            font=('Segoe UI', 10),
            width=30
        )
        self.db_entry.pack(anchor=tk.W)

        # Add some bottom padding
        spacer = tk.Frame(form_frame, height=20, bg=COLORS['card_bg'])
        spacer.pack()

        # Show initial dynamic fields
        self._on_type_change()

    def _on_type_change(self):
        """Handle connection type change."""
        conn_type = self.connection_type.get()

        # Hide all dynamic frames
        self.instance_frame.pack_forget()
        self.connection_frame.pack_forget()
        self.external_frame.pack_forget()

        # Show relevant frame
        if conn_type == 'unix_socket':
            self.instance_frame.pack(fill=tk.X)
        elif conn_type == 'python_connector':
            self.connection_frame.pack(fill=tk.X)
        elif conn_type == 'external':
            self.external_frame.pack(fill=tk.X)

    def _toggle_password(self):
        """Toggle password visibility."""
        if self.show_password.get():
            self.password_entry.config(show='')
        else:
            self.password_entry.config(show='\u2022')

    def validate(self) -> bool:
        """Validate database configuration."""
        conn_type = self.connection_type.get()

        # Validate connection-specific fields
        if conn_type == 'unix_socket':
            if not self.instance_var.get().strip():
                messagebox.showwarning("Required", "Please enter the Cloud SQL instance name.")
                return False
        elif conn_type == 'python_connector':
            if not self.connection_var.get().strip():
                messagebox.showwarning("Required", "Please enter the Cloud SQL connection string.")
                return False
            if ':' not in self.connection_var.get():
                messagebox.showwarning(
                    "Invalid Format",
                    "Connection string must be in format: PROJECT:REGION:INSTANCE"
                )
                return False
        elif conn_type == 'external':
            if not self.host_var.get().strip():
                messagebox.showwarning("Required", "Please enter the PostgreSQL host.")
                return False

        # Validate credentials
        if not self.user_var.get().strip():
            messagebox.showwarning("Required", "Please enter the database username.")
            return False

        if not self.password_var.get():
            messagebox.showwarning("Required", "Please enter the database password.")
            return False

        if not self.db_var.get().strip():
            messagebox.showwarning("Required", "Please enter the database name.")
            return False

        return True

    def get_data(self) -> Dict[str, Any]:
        """Return database configuration."""
        conn_type = self.connection_type.get()
        project_id = self.wizard.data.get('project_id', '')
        region = self.wizard.data.get('region', 'us-central1')

        # Build database host based on connection type
        if conn_type == 'unix_socket':
            instance = self.instance_var.get().strip()
            cloud_sql_connection = f"{project_id}:{region}:{instance}"
            db_host = f"/cloudsql/{cloud_sql_connection}"
        elif conn_type == 'python_connector':
            cloud_sql_connection = self.connection_var.get().strip()
            db_host = ""  # Not used with Python Connector
        else:
            cloud_sql_connection = None
            db_host = self.host_var.get().strip()

        return {
            'db_connection_method': conn_type,
            'db_host': db_host,
            'db_port': self.port_var.get().strip() if conn_type == 'external' else '5432',
            'db_name': self.db_var.get().strip(),
            'db_user': self.user_var.get().strip(),
            'db_password': self.password_var.get(),
            'cloud_sql_connection': cloud_sql_connection,
        }
