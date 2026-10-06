"""
Library Management System (LMS)
College Project by SHAHANAWAJ (Roll No: 2410302051)

Main Application Entry Point:
- Initializes SQLite database schema & seeds.
- Restores persisted accessibility preferences.
- Manages High-DPI Windows scaling.
- Orchestrates LoginView and MainWindow transitions.
"""

import sys
import ctypes
import customtkinter as ctk
from config import theme_mgr, APP_TITLE, DB_PATH
from database import init_db
from services.settings_service import SettingsService
from ui.views.login_view import LoginView
from ui.main_window import MainWindow


# Enable High-DPI Awareness on Windows
if sys.platform == "win32":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class LibraryApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Metadata & Geometry
        self.title(APP_TITLE)
        self.geometry("1240x780")
        self.minsize(1040, 640)

        # Center Window on Primary Display
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        pos_x = max(0, (screen_width - 1240) // 2)
        pos_y = max(0, (screen_height - 780) // 2)
        self.geometry(f"1240x780+{pos_x}+{pos_y}")

        # Grid configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Initialize Services & Settings
        init_db()
        SettingsService.load_settings()

        # Appearance configuration
        if theme_mgr.high_contrast:
            ctk.set_appearance_mode("Dark")
        elif theme_mgr.dark_mode:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

        ctk.set_default_color_theme("blue")

        self.current_frame = None

        # Register Theme Listener on root window
        theme_mgr.register_listener(self._on_theme_changed)
        self._on_theme_changed()

        # Display Login View initially
        self.show_login()

    def _on_theme_changed(self):
        colors = theme_mgr.colors
        self.configure(fg_color=colors["bg"])

    def show_login(self):
        """Display authentication screen."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = LoginView(self, on_login_success=self.show_main_app)
        self.current_frame.grid(row=0, column=0, sticky="nsew")

    def show_main_app(self, user_dict: dict):
        """Display main dashboard and navigation view."""
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = MainWindow(self, current_user=user_dict, on_logout=self.show_login)
        self.current_frame.grid(row=0, column=0, sticky="nsew")


def main():
    app = LibraryApp()
    app.mainloop()


if __name__ == "__main__":
    main()
