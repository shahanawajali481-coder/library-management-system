"""
Main Application Window:
Houses the modern sidebar navigation, dynamic view switcher,
top header bar, and global accessibility theme synchronization.
"""

import customtkinter as ctk
from typing import Dict, Optional, Callable
from config import theme_mgr, STUDENT_NAME, STUDENT_ROLL, APP_TITLE
from ui.components.navbar import Navbar
from ui.views.dashboard_view import DashboardView
from ui.views.books_view import BooksView
from ui.views.members_view import MembersView
from ui.views.issue_return_view import IssueReturnView
from ui.views.reports_view import ReportsView
from ui.views.settings_view import SettingsView


class MainWindow(ctk.CTkFrame):
    def __init__(self, master, current_user: Dict, on_logout: Callable[[], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.current_user = current_user
        self.on_logout_callback = on_logout

        self.current_view_name = "Dashboard"
        self.active_view_widget = None
        self.nav_buttons = {}

        # Layout: Col 0 = Sidebar (width ~240), Col 1 = Content (flexible)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # 1. Left Sidebar
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self._build_sidebar()

        # 2. Right Content Area (Row 0 = Navbar, Row 1 = Active View)
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew")
        self.content_area.grid_rowconfigure(1, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)

        # Top Navbar
        self.navbar = Navbar(
            self.content_area,
            current_user=self.current_user.get("username", "Admin"),
            on_theme_toggle=self.on_theme_updated
        )
        self.navbar.grid(row=0, column=0, sticky="ew")

        # Viewport Frame
        self.viewport = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.viewport.grid(row=1, column=0, sticky="nsew")
        self.viewport.grid_rowconfigure(0, weight=1)
        self.viewport.grid_columnconfigure(0, weight=1)

        # Register Theme Listener
        theme_mgr.register_listener(self.on_theme_updated)

        # Show initial Dashboard
        self.navigate("Dashboard")
        self.apply_theme()

    def _build_sidebar(self):
        # Branding Header
        self.brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=80)
        self.brand_frame.pack(fill="x", padx=16, pady=(20, 16))

        self.brand_icon = ctk.CTkLabel(self.brand_frame, text="📚", anchor="w")
        self.brand_icon.pack(side="left", padx=(4, 10))

        brand_text_box = ctk.CTkFrame(self.brand_frame, fg_color="transparent")
        brand_text_box.pack(side="left", fill="both")

        self.brand_title = ctk.CTkLabel(
            brand_text_box,
            text="LIBRARY PRO",
            anchor="w"
        )
        self.brand_title.pack(anchor="w")

        self.brand_subtitle = ctk.CTkLabel(
            brand_text_box,
            text=f"{STUDENT_NAME} ({STUDENT_ROLL})",
            anchor="w"
        )
        self.brand_subtitle.pack(anchor="w")

        # Divider
        self.sidebar_divider = ctk.CTkFrame(self.sidebar, height=1)
        self.sidebar_divider.pack(fill="x", padx=16, pady=(0, 16))

        # Nav Items
        nav_items = [
            ("Dashboard", "📊  Dashboard"),
            ("Books", "📚  Books Catalog"),
            ("Members", "👥  Members Directory"),
            ("Issue / Return", "🔄  Issue & Return"),
            ("Reports", "📈  Reports & Analytics"),
            ("Settings", "♿  Accessibility / Config")
        ]

        self.nav_container = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_container.pack(fill="x", padx=12)

        for key, label in nav_items:
            btn = ctk.CTkButton(
                self.nav_container,
                text=label,
                anchor="w",
                height=42,
                corner_radius=8,
                command=lambda k=key: self.navigate(k)
            )
            btn.pack(fill="x", pady=4)
            self.nav_buttons[key] = btn

        # Spacer to push logout & watermark to bottom
        self.spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.spacer.pack(fill="both", expand=True)

        # Bottom Sidebar Profile & Logout
        self.bottom_sidebar = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.bottom_sidebar.pack(fill="x", padx=12, pady=16)

        self.btn_logout = ctk.CTkButton(
            self.bottom_sidebar,
            text="🚪  Sign Out",
            height=38,
            corner_radius=8,
            command=self._handle_logout
        )
        self.btn_logout.pack(fill="x", pady=(0, 10))

        self.watermark_lbl = ctk.CTkLabel(
            self.bottom_sidebar,
            text=f"College Lab Project\nRoll: {STUDENT_ROLL}",
            justify="center"
        )
        self.watermark_lbl.pack(fill="x")

    def navigate(self, view_name: str):
        """Switch to chosen view dynamically."""
        self.current_view_name = view_name

        # Destroy old view
        if self.active_view_widget:
            self.active_view_widget.destroy()

        # Instantiate new view
        if view_name == "Dashboard":
            self.navbar.set_title("Dashboard Overview", "Real-time metrics, inventory breakdown, and transactions")
            self.active_view_widget = DashboardView(self.viewport, navigate_to=self.navigate)
        elif view_name == "Books":
            self.navbar.set_title("Books Management", "Browse, search, add, edit, and organize library book inventory")
            self.active_view_widget = BooksView(self.viewport)
        elif view_name == "Members":
            self.navbar.set_title("Members Directory", "Manage registered students, faculty, and verify active borrowings")
            self.active_view_widget = MembersView(self.viewport)
        elif view_name == "Issue / Return":
            self.navbar.set_title("Issue & Return Operations", "Issue books with due date calculator and process returns with live overdue fines")
            self.active_view_widget = IssueReturnView(self.viewport)
        elif view_name == "Reports":
            self.navbar.set_title("Reports & Export", "Generate 7 comprehensive library audit reports and export to CSV")
            self.active_view_widget = ReportsView(self.viewport)
        elif view_name == "Settings":
            self.navbar.set_title("Accessibility & Settings (Q12)", "Configure appearance mode, high contrast, and dynamic font scale")
            self.active_view_widget = SettingsView(self.viewport, on_theme_change=self.on_theme_updated)

        self.active_view_widget.grid(row=0, column=0, sticky="nsew")
        self._highlight_active_nav()

    def _highlight_active_nav(self):
        colors = theme_mgr.colors
        for key, btn in self.nav_buttons.items():
            if key == self.current_view_name:
                btn.configure(
                    fg_color=colors["accent"],
                    text_color=colors["accent_text"],
                    hover_color=colors["accent_hover"],
                    font=theme_mgr.get_font(offset=0, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=colors["text"],
                    hover_color=colors["secondary_hover"],
                    font=theme_mgr.get_font(offset=0)
                )

    def _handle_logout(self):
        theme_mgr.unregister_listener(self.on_theme_updated)
        self.destroy()
        if self.on_logout_callback:
            self.on_logout_callback()

    def on_theme_updated(self):
        """Called automatically by ThemeManager when font size or color theme changes."""
        self.apply_theme()
        if self.active_view_widget and hasattr(self.active_view_widget, "apply_theme"):
            try:
                self.active_view_widget.apply_theme()
            except Exception as e:
                print(f"[Error in active view apply_theme]: {e}")

    def apply_theme(self):
        colors = theme_mgr.colors

        # Sidebar
        self.sidebar.configure(
            fg_color=colors["sidebar_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )

        self.brand_icon.configure(
            font=theme_mgr.get_font(offset=8),
            text_color=colors["accent"]
        )
        self.brand_title.configure(
            font=theme_mgr.get_font(offset=2, weight="bold"),
            text_color=colors["text"]
        )
        self.brand_subtitle.configure(
            font=theme_mgr.get_font(offset=-3),
            text_color=colors["subtext"]
        )
        self.sidebar_divider.configure(fg_color=colors["border"])

        self.btn_logout.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
        self.watermark_lbl.configure(
            font=theme_mgr.get_font(offset=-4),
            text_color=colors["subtext"]
        )

        # Highlight active nav button
        self._highlight_active_nav()

        # Navbar
        self.navbar.apply_theme()
