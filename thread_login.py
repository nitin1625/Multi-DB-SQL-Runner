import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import pyodbc
import json
import os
from config import get_config_path
import queue
import threading

CREDENTIALS_FILE = get_config_path()

class CustomTheme:
    """Custom color theme for the application"""
    BG_COLOR = "#f0f4f8"           # Light blue background
    PRIMARY = "#1a73e8"            # Primary blue
    ACCENT = "#4285f4"             # Accent blue
    DANGER = "#ea4335"             # Red for delete/warning
    TEXT_DARK = "#202124"          # Dark text
    TEXT_LIGHT = "#ffffff"         # Light text
    FIELD_BG = "#ffffff"           # Input field background
    HOVER = "#d2e3fc"              # Hover state
    BORDER = "#dadce0"             # Border color

class LoginDialog:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent)
        self.top.title("🔐 SQL Server Login")
        self.top.geometry("480x450")
        self.top.resizable(True, True)
        self.top.configure(bg=CustomTheme.BG_COLOR)
        self.top.grab_set()  # Modal
        self.queue = queue.Queue()
        
        # Center the window on screen
        self.center_window()
        
        # Set minimum window size
        self.top.minsize(400, 400)
        
        # Apply custom styles
        self.setup_styles()
        
        self.result = None
        self.profiles = self.load_profiles()
        
        # Main container with padding
        main_frame = tk.Frame(self.top, bg=CustomTheme.BG_COLOR, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="SQL Server Login", 
            font=("Helvetica", 16, "bold"),
            fg=CustomTheme.PRIMARY,
            bg=CustomTheme.BG_COLOR
        )
        title_label.pack(pady=(0, 15))
        
        # === Profile Selection ===
        profile_frame = tk.Frame(main_frame, bg=CustomTheme.BG_COLOR)
        profile_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            profile_frame, 
            text="Profile:", 
            anchor="w",
            bg=CustomTheme.BG_COLOR,
            fg=CustomTheme.TEXT_DARK,
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT)
        
        self.profile_var = tk.StringVar()
        self.profile_selector = ttk.Combobox(
            profile_frame, 
            textvariable=self.profile_var, 
            state="readonly",
            style="Custom.TCombobox",
            width=30
        )
        self.profile_selector["values"] = list(self.profiles.keys())
        self.profile_selector.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.profile_selector.bind("<<ComboboxSelected>>", self.fill_profile_fields)
        
        # === Delete Profile Button ===
        btn_frame = tk.Frame(main_frame, bg=CustomTheme.BG_COLOR)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        delete_btn = tk.Button(
            btn_frame, 
            text="Delete Profile", 
            command=self.delete_profile,
            bg=CustomTheme.DANGER,
            fg=CustomTheme.TEXT_LIGHT,
            activebackground=CustomTheme.DANGER,
            activeforeground=CustomTheme.TEXT_LIGHT,
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        )
        delete_btn.pack(side=tk.RIGHT)
        
        # === Form Fields Container ===
        form_frame = tk.Frame(main_frame, bg=CustomTheme.BG_COLOR)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # === Credentials Fields ===
        self.create_form_field(form_frame, "SQL Server:", "server_entry")
        self.create_form_field(form_frame, "Username:", "user_entry", default_value="sa")
        self.create_form_field(form_frame, "Password:", "pass_entry", show="*")
        self.create_form_field(form_frame, "ODBC Driver:", "driver_entry", 
                              default_value="ODBC Driver 17 for SQL Server")
        
        # === Remember Option & Login Button ===
        bottom_frame = tk.Frame(main_frame, bg=CustomTheme.BG_COLOR)
        bottom_frame.pack(fill=tk.X, pady=(15, 0))
        
        self.remember_var = tk.BooleanVar()
        remember_check = tk.Checkbutton(
            bottom_frame, 
            text="Remember Me", 
            variable=self.remember_var,
            bg=CustomTheme.BG_COLOR,
            fg=CustomTheme.TEXT_DARK,
            selectcolor=CustomTheme.BG_COLOR,
            activebackground=CustomTheme.BG_COLOR
        )
        remember_check.pack(side=tk.LEFT, pady=5)
        
        login_btn = tk.Button(
            bottom_frame, 
            text="Login", 
            command=self.handle_login,
            bg=CustomTheme.PRIMARY,
            fg=CustomTheme.TEXT_LIGHT,
            activebackground=CustomTheme.ACCENT,
            activeforeground=CustomTheme.TEXT_LIGHT,
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            font=("Helvetica", 10, "bold")
        )
        login_btn.pack(side=tk.RIGHT, pady=5)
        
        # Add event bindings for better interactivity
        self.add_button_hover_effects(login_btn, CustomTheme.PRIMARY, CustomTheme.ACCENT)
        self.add_button_hover_effects(delete_btn, CustomTheme.DANGER, "#d32f2f")  # Darker red on hover
        
        # Auto-load last used profile if available
        if self.profiles:
            self.profile_selector.current(0)
            self.fill_profile_fields()
            
        # Bind Enter key to login button
        self.top.bind("<Return>", lambda event: self.handle_login())
    
    def center_window(self):
        """Center the window on the screen"""
        self.top.update_idletasks()
        width = self.top.winfo_width()
        height = self.top.winfo_height()
        x = (self.top.winfo_screenwidth() // 2) - (width // 2)
        y = (self.top.winfo_screenheight() // 2) - (height // 2)
        self.top.geometry(f"{width}x{height}+{x}+{y}")
            
    def setup_styles(self):
        """Setup custom ttk styles"""
        style = ttk.Style()
        style.configure(
            "Custom.TCombobox",
            fieldbackground=CustomTheme.FIELD_BG,
            background=CustomTheme.FIELD_BG,
            selectbackground=CustomTheme.PRIMARY
        )
        style.configure(
            "Custom.Horizontal.TProgressbar",
            troughcolor=CustomTheme.BORDER,
            background=CustomTheme.PRIMARY,
            thickness=6
        )

    def toggle_password_visibility(self, entry):
        """Toggle password visibility between hidden and shown"""
        if self.pass_shown:
            entry.config(show="*")
            self.pass_shown = False
        else:
            entry.config(show="")
            self.pass_shown = True
    
    def create_form_field(self, parent, label_text, entry_name, default_value="", show=""):
        """Create a form field with label and entry"""
        field_frame = tk.Frame(parent, bg=CustomTheme.BG_COLOR)
        field_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            field_frame, 
            text=label_text, 
            anchor="w",
            width=12,
            bg=CustomTheme.BG_COLOR,
            fg=CustomTheme.TEXT_DARK,
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT)
        
        if entry_name == "pass_entry":
            entry_container = tk.Frame(field_frame, bg=CustomTheme.FIELD_BG,bd=1, relief=tk.SOLID)
            entry_container.pack(side=tk.RIGHT, fill=tk.X, expand=True)
            
            entry = tk.Entry(
                entry_container, 
                width=40,
                bg=CustomTheme.FIELD_BG,
                fg=CustomTheme.TEXT_DARK,
                insertbackground=CustomTheme.PRIMARY,
                relief=tk.FLAT,
                bd=0,
                font=("Helvetica", 10),
                show="*" if show else ""
            )
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(2, 0))
            
            # Add toggle button for password visibility
            self.pass_shown = False
            toggle_btn = tk.Button(
                entry_container,
                text="👁️",
                bg=CustomTheme.FIELD_BG,
                activebackground=CustomTheme.HOVER,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda: self.toggle_password_visibility(entry)
            )
            toggle_btn.pack(side=tk.RIGHT, padx=2, fill=tk.Y)

        else :
            entry = tk.Entry(
            field_frame, 
            width=40,
            bg=CustomTheme.FIELD_BG,
            fg=CustomTheme.TEXT_DARK,
            insertbackground=CustomTheme.PRIMARY,
            relief=tk.SOLID,
            bd=1,
            font=("Helvetica", 10)
        )
        
        if show:
            entry.configure(show=show)
            
        if default_value:
            entry.insert(0, default_value)
            
        entry.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=5)
        
        # Highlight entry on focus
        entry.bind("<FocusIn>", lambda e: entry.configure(
            highlightbackground=CustomTheme.PRIMARY, 
            highlightthickness=2,
            bd=0
        ))
        entry.bind("<FocusOut>", lambda e: entry.configure(
            highlightbackground=CustomTheme.BORDER, 
            highlightthickness=1,
            bd=0
        ))
        
        setattr(self, entry_name, entry)
        return entry
    
    def add_button_hover_effects(self, button, default_color, hover_color):
        """Add hover effects to buttons"""
        button.bind("<Enter>", lambda e: button.configure(bg=hover_color))
        button.bind("<Leave>", lambda e: button.configure(bg=default_color))

    def load_profiles(self):
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_profiles(self):
        with open(CREDENTIALS_FILE, "w") as f:
            json.dump(self.profiles, f, indent=4)

    def delete_profile(self):
        profile = self.profile_var.get().strip()

        if not profile:
            self.show_message("Select Profile", "Please select a profile to delete.", "info")
            return

        if profile not in self.profiles:
            self.show_message("Error", f"No saved profile named '{profile}'.", "error")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete profile '{profile}'?")
        if not confirm:
            return

        del self.profiles[profile]
        self.save_profiles()

        # Clear UI
        self.profile_selector["values"] = list(self.profiles.keys())
        self.profile_var.set("")
        self.server_entry.delete(0, tk.END)
        self.user_entry.delete(0, tk.END)
        self.pass_entry.delete(0, tk.END)
        self.driver_entry.delete(0, tk.END)

        self.show_message("Deleted", f"Profile '{profile}' deleted.", "info")

    def fill_profile_fields(self, event=None):
        profile_name = self.profile_var.get()
        profile = self.profiles.get(profile_name, {})
        self.server_entry.delete(0, tk.END)
        self.server_entry.insert(0, profile.get("SQL_SERVER", ""))
        self.user_entry.delete(0, tk.END)
        self.user_entry.insert(0, profile.get("USERNAME", ""))
        self.pass_entry.delete(0, tk.END)
        self.pass_entry.insert(0, profile.get("PASSWORD", ""))
        self.driver_entry.delete(0, tk.END)
        self.driver_entry.insert(0, profile.get("DRIVER", ""))

    def get_connection_string(self, server, user, password, driver, db="master"):
        return f"DRIVER={driver};SERVER={server};UID={user};PWD={password};DATABASE={db}"

    def show_message(self, title, message, type_="info"):
        """Show a styled message box"""
        if type_ == "error":
            messagebox.showerror(title, message)
        elif type_ == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showinfo(title, message)

    def handle_login(self):
            server = self.server_entry.get().strip()
            user = self.user_entry.get().strip()
            password = self.pass_entry.get().strip()
            driver = self.driver_entry.get().strip()
            profile_name = self.profile_var.get().strip()

            if not all([server, user, password, driver]):
                self.show_message("Missing Info", "Please fill in all fields.", "error")
                return

            # Disable login button
            login_btn = self.top.nametowidget(
                self.top.winfo_children()[0].winfo_children()[-1].winfo_children()[-1]
            )
            login_btn_text = login_btn.cget("text")
            login_btn.config(text="Connecting...", state=tk.DISABLED)

            # Create progress bar
            progress_frame = tk.Frame(self.top, bg=CustomTheme.BG_COLOR)
            progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=10)

            status_label = tk.Label(
                progress_frame,
                text="Connecting to SQL Server...",
                bg=CustomTheme.BG_COLOR,
                fg=CustomTheme.PRIMARY,
            )
            status_label.pack(anchor=tk.W, pady=(0, 5))

            progress = ttk.Progressbar(
                progress_frame,
                style="Custom.Horizontal.TProgressbar",
                mode="indeterminate",
                length=440,
            )
            progress.pack(fill=tk.X)
            progress.start(15)

            # Change cursor
            self.top.config(cursor="watch")

            # Start connection in a separate thread
            thread = threading.Thread(
                target=self.attempt_connection_thread,
                args=(server, user, password, driver, profile_name, login_btn, login_btn_text, progress_frame),
            )
            thread.daemon = True  # Ensure thread terminates when app closes
            thread.start()

            # Check queue for results periodically
            self.top.after(100, self.check_connection_result)

    def attempt_connection_thread(self, server, user, password, driver, profile_name, login_btn, original_text, progress_frame):
        try:
            conn_str = self.get_connection_string(server, user, password, driver)
            conn = pyodbc.connect(conn_str)
            conn.close()
            self.queue.put(("success", server, user, password, driver, profile_name, login_btn, original_text, progress_frame))
        except pyodbc.Error as e:
            self.queue.put(("error", str(e), login_btn, original_text, progress_frame))

    def check_connection_result(self):
        try:
            result = self.queue.get_nowait()
            if result[0] == "success":
                self.handle_successful_connection(*result[1:])
            else:
                self.handle_failed_connection(*result[1:])
        except queue.Empty:
            self.top.after(100, self.check_connection_result)

    def handle_successful_connection(self, server, user, password, driver, profile_name, login_btn, original_text, progress_frame):
        # Stop progress bar
        for widget in progress_frame.winfo_children():
            if isinstance(widget, ttk.Progressbar):
                widget.stop()

        # Reset cursor
        self.top.config(cursor="")

        if self.remember_var.get():
            if not profile_name:
                profile_name = simpledialog.askstring("Profile Name", "Enter a name for this profile:", parent=self.top)
                if not profile_name:
                    self.cleanup_ui(login_btn, original_text, progress_frame)
                    return
                self.profile_var.set(profile_name)

            if profile_name in self.profiles:
                confirm = messagebox.askyesno(
                    "Profile Exists",
                    f"Profile '{profile_name}' already exists.\nDo you want to overwrite it?",
                    parent=self.top,
                )
                if not confirm:
                    new_name = simpledialog.askstring("New Profile Name", "Enter a new profile name:", parent=self.top)
                    if not new_name:
                        self.cleanup_ui(login_btn, original_text, progress_frame)
                        return
                    profile_name = new_name
                    self.profile_var.set(profile_name)

            self.profiles[profile_name] = {
                "SQL_SERVER": server,
                "USERNAME": user,
                "PASSWORD": password,
                "DRIVER": driver,
            }
            self.save_profiles()
            self.profile_selector["values"] = list(self.profiles.keys())

        # Store result and close window
        self.result = {
            "SQL_SERVER": server,
            "USERNAME": user,
            "PASSWORD": password,
            "DRIVER": driver,
        }
        progress_frame.destroy()
        self.top.destroy()

    def handle_failed_connection(self, error_msg, login_btn, original_text, progress_frame):
        # Reset UI
        for widget in progress_frame.winfo_children():
            if isinstance(widget, ttk.Progressbar):
                widget.stop()
        login_btn.config(text=original_text, state=tk.NORMAL)
        progress_frame.destroy()
        self.top.config(cursor="")

        self.show_message("Login Failed", f"Could not connect to SQL Server:\n{error_msg}", "error")

    def cleanup_ui(self, login_btn, original_text, progress_frame):
        for widget in progress_frame.winfo_children():
            if isinstance(widget, ttk.Progressbar):
                widget.stop()
        login_btn.config(text=original_text, state=tk.NORMAL)
        progress_frame.destroy()
        self.top.config(cursor="")

    def show_message(self, title, message, icon):
        messagebox.showinfo(title, message, icon=icon, parent=self.top)