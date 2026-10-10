"""
Configuration and Theme Management for Library Management System.
Student: SHAHANAWAJ (Roll No: 2410302051)
"""

import os

# Optional GUI import for CustomTkinter (Desktop Mode)
try:
    import customtkinter as ctk
    HAS_GUI = True
except (ImportError, ModuleNotFoundError):
    ctk = None
    HAS_GUI = False

# Base Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(DB_DIR, "library.db"))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# Student Project Information
STUDENT_NAME = "SHAHANAWAJ"
STUDENT_ROLL = "2410302051"
APP_TITLE = "Library Management System"
APP_SUBTITLE = f"College Project | {STUDENT_NAME} (Roll No: {STUDENT_ROLL})"

# Business Logic Defaults
CURRENCY_SYMBOL = "₹"
FINE_PER_DAY = 5.0  # ₹5 per overdue day
DEFAULT_LOAN_DAYS = 14

# Supported Font Sizes for Accessibility (Q12)
AVAILABLE_FONT_SIZES = [12, 14, 16, 18, 20, 22, 24]
DEFAULT_FONT_SIZE = 14

# Color Palettes
PALETTES = {
    "dark": {
        "bg": "#0f172a",
        "card_bg": "#1e293b",
        "sidebar_bg": "#0b1120",
        "header_bg": "#111827",
        "accent": "#3b82f6",
        "accent_hover": "#2563eb",
        "accent_text": "#ffffff",
        "secondary_btn": "#334155",
        "secondary_hover": "#475569",
        "secondary_text": "#e2e8f0",
        "text": "#f8fafc",
        "subtext": "#94a3b8",
        "border": "#334155",
        "border_width": 1,
        "input_bg": "#0f172a",
        "input_border": "#475569",
        "success": "#10b981",
        "warning": "#f59e0b",
        "danger": "#ef4444",
        "info": "#06b6d4",
        "table_header": "#1e293b",
        "table_header_text": "#93c5fd",
        "table_row": "#1e293b",
        "table_row_alt": "#172033",
        "table_hover": "#2e3b52",
        "table_selected": "#2563eb",
        "focus_border": "#60a5fa",
        "chart_bg": "#1e293b",
        "chart_text": "#f8fafc",
    },
    "light": {
        "bg": "#f1f5f9",
        "card_bg": "#ffffff",
        "sidebar_bg": "#e2e8f0",
        "header_bg": "#ffffff",
        "accent": "#2563eb",
        "accent_hover": "#1d4ed8",
        "accent_text": "#ffffff",
        "secondary_btn": "#e2e8f0",
        "secondary_hover": "#cbd5e1",
        "secondary_text": "#1e293b",
        "text": "#0f172a",
        "subtext": "#64748b",
        "border": "#cbd5e1",
        "border_width": 1,
        "input_bg": "#ffffff",
        "input_border": "#94a3b8",
        "success": "#059669",
        "warning": "#d97706",
        "danger": "#dc2626",
        "info": "#0891b2",
        "table_header": "#e2e8f0",
        "table_header_text": "#1e40af",
        "table_row": "#ffffff",
        "table_row_alt": "#f8fafc",
        "table_hover": "#dbeafe",
        "table_selected": "#93c5fd",
        "focus_border": "#2563eb",
        "chart_bg": "#ffffff",
        "chart_text": "#0f172a",
    },
    "high_contrast": {
        "bg": "#000000",
        "card_bg": "#000000",
        "sidebar_bg": "#000000",
        "header_bg": "#000000",
        "accent": "#ffff00",
        "accent_hover": "#ffd700",
        "accent_text": "#000000",
        "secondary_btn": "#000000",
        "secondary_hover": "#1a1a00",
        "secondary_text": "#ffff00",
        "text": "#ffffff",
        "subtext": "#ffff00",
        "border": "#ffff00",
        "border_width": 2,
        "input_bg": "#000000",
        "input_border": "#ffff00",
        "success": "#00ff66",
        "warning": "#ffff00",
        "danger": "#ff3333",
        "info": "#00ffff",
        "table_header": "#ffff00",
        "table_header_text": "#000000",
        "table_row": "#000000",
        "table_row_alt": "#111111",
        "table_hover": "#333300",
        "table_selected": "#ffff00",
        "focus_border": "#ffffff",
        "chart_bg": "#000000",
        "chart_text": "#ffffff",
    }
}


class ThemeManager:
    """
    Central observer for App-wide Accessibility & Theming (Q12).
    Dispatches change notifications to all subscribed views when:
    - Dark Mode is toggled
    - High Contrast Mode is toggled
    - Font Size is adjusted (12 -> 24)
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance.dark_mode = True
            cls._instance.high_contrast = False
            cls._instance.font_size = DEFAULT_FONT_SIZE
            cls._instance._listeners = []
        return cls._instance

    @property
    def current_mode(self) -> str:
        if self.high_contrast:
            return "high_contrast"
        return "dark" if self.dark_mode else "light"

    @property
    def colors(self) -> dict:
        return PALETTES[self.current_mode]

    def register_listener(self, callback):
        """Register a view callback to be executed on theme/font change."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self):
        """Synchronize CustomTkinter appearance mode and invoke all listeners."""
        if HAS_GUI and ctk is not None:
            try:
                if self.high_contrast:
                    ctk.set_appearance_mode("Dark")
                elif self.dark_mode:
                    ctk.set_appearance_mode("Dark")
                else:
                    ctk.set_appearance_mode("Light")
            except Exception:
                pass

        for listener in list(self._listeners):
            try:
                listener()
            except Exception as e:
                print(f"[ThemeManager Error in listener]: {e}")

    def set_dark_mode(self, enabled: bool):
        self.dark_mode = enabled
        self.notify_listeners()

    def set_high_contrast(self, enabled: bool):
        self.high_contrast = enabled
        self.notify_listeners()

    def set_font_size(self, size: int):
        if size in AVAILABLE_FONT_SIZES:
            self.font_size = size
            self.notify_listeners()

    def increase_font(self) -> int:
        idx = AVAILABLE_FONT_SIZES.index(self.font_size)
        if idx < len(AVAILABLE_FONT_SIZES) - 1:
            self.set_font_size(AVAILABLE_FONT_SIZES[idx + 1])
        return self.font_size

    def decrease_font(self) -> int:
        idx = AVAILABLE_FONT_SIZES.index(self.font_size)
        if idx > 0:
            self.set_font_size(AVAILABLE_FONT_SIZES[idx - 1])
        return self.font_size

    def get_font(self, offset: int = 0, weight: str = "normal", slant: str = "roman"):
        """Dynamically compute font respecting current accessibility base font size."""
        target_size = max(10, self.font_size + offset)
        font_family = "Segoe UI" if os.name == "nt" else "Helvetica"
        if HAS_GUI and ctk is not None:
            try:
                return ctk.CTkFont(family=font_family, size=target_size, weight=weight, slant=slant)
            except Exception:
                pass
        return (font_family, target_size, weight)


# Global singleton instance
theme_mgr = ThemeManager()
