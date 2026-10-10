"""
Modern Login View for the Library Management System.
Features credentials authentication, 1-click Demo Login, password reveal,
and prominent student project accreditation (SHAHANAWAJ, Roll: 2410302051).
"""

import customtkinter as ctk
from typing import Callable, Dict
from config import theme_mgr, STUDENT_NAME, STUDENT_ROLL, APP_TITLE
from services.settings_service import SettingsService


class LoginView(ctk.CTkFrame):
    def __init__(self, master, on_login_success: Callable[[Dict], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_login_success = on_login_success
        self.show_password = False

        # Center layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Card container
        self.card = ctk.CTkFrame(self, width=440, corner_radius=16)
        self.card.grid(row=0, column=0, padx=20, pady=20)
        self.card.grid_columnconfigure(0, weight=1)

        # Header Icon & Branding
        self.icon_lbl = ctk.CTkLabel(self.card, text="📚")
        self.icon_lbl.grid(row=0, column=0, pady=(32, 6))

        self.title_lbl = ctk.CTkLabel(
            self.card,
            text=APP_TITLE,
            font=theme_mgr.get_font(offset=6, weight="bold")
        )
        self.title_lbl.grid(row=1, column=0, pady=(0, 4))

        self.student_lbl = ctk.CTkLabel(
            self.card,
            text=f"College Project by {STUDENT_NAME}\nRoll No: {STUDENT_ROLL}",
            justify="center"
        )
        self.student_lbl.grid(row=2, column=0, pady=(0, 24))

        # Form fields container
        form_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        form_frame.grid(row=3, column=0, sticky="ew", padx=36)
        form_frame.grid_columnconfigure(0, weight=1)

        # Username
        self.user_title = ctk.CTkLabel(form_frame, text="Username", anchor="w")
        self.user_title.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.user_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter username (e.g. admin)",
            height=40
        )
        self.user_entry.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        self.user_entry.insert(0, "admin")

        # Password
        pwd_box = ctk.CTkFrame(form_frame, fg_color="transparent")
        pwd_box.grid(row=2, column=0, sticky="ew", pady=(0, 4))
        pwd_box.grid_columnconfigure(0, weight=1)

        self.pwd_title = ctk.CTkLabel(pwd_box, text="Password", anchor="w")
        self.pwd_title.grid(row=0, column=0, sticky="w")

        self.toggle_pwd_btn = ctk.CTkButton(
            pwd_box,
            text="👁️ Show",
            width=50,
            height=20,
            fg_color="gray",
            hover_color="darkgray",
            command=self._toggle_password_visibility
        )
        self.toggle_pwd_btn.grid(row=0, column=1, sticky="e")

        self.pwd_entry = ctk.CTkEntry(
            form_frame,
            placeholder_text="Enter password (e.g. admin123)",
            show="•",
            height=40
        )
        self.pwd_entry.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.pwd_entry.insert(0, "admin123")
        self.pwd_entry.bind("<Return>", lambda e: self._handle_login())

        # Error label
        self.err_lbl = ctk.CTkLabel(
            form_frame,
            text="",
            wraplength=340,
            justify="center"
        )
        self.err_lbl.grid(row=4, column=0, pady=(0, 10))

        # Sign In Button
        self.login_btn = ctk.CTkButton(
            form_frame,
            text="Sign In to System",
            height=42,
            command=self._handle_login
        )
        self.login_btn.grid(row=5, column=0, sticky="ew", pady=(0, 10))

        # Demo Login Quick Button
        self.demo_btn = ctk.CTkButton(
            form_frame,
            text="⚡ Quick Demo Login (Admin)",
            height=36,
            command=self._handle_demo_login
        )
        self.demo_btn.grid(row=6, column=0, sticky="ew", pady=(0, 28))

        self.apply_theme()

    def _toggle_password_visibility(self):
        self.show_password = not self.show_password
        if self.show_password:
            self.pwd_entry.configure(show="")
            self.toggle_pwd_btn.configure(text="🔒 Hide")
        else:
            self.pwd_entry.configure(show="•")
            self.toggle_pwd_btn.configure(text="👁️ Show")

    def _handle_login(self):
        username = self.user_entry.get().strip()
        password = self.pwd_entry.get().strip()

        if not username or not password:
            self.err_lbl.configure(text="Please enter both username and password.")
            return

        user = SettingsService.verify_login(username, password)
        if user:
            self.err_lbl.configure(text="")
            self.on_login_success(user)
        else:
            self.err_lbl.configure(text="Invalid username or password. Default is admin / admin123.")

    def _handle_demo_login(self):
        self.user_entry.delete(0, "end")
        self.user_entry.insert(0, "admin")
        self.pwd_entry.delete(0, "end")
        self.pwd_entry.insert(0, "admin123")
        self._handle_login()

    def apply_theme(self):
        colors = theme_mgr.colors

        self.card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )

        self.icon_lbl.configure(
            font=theme_mgr.get_font(offset=18),
            text_color=colors["accent"]
        )
        self.title_lbl.configure(
            font=theme_mgr.get_font(offset=6, weight="bold"),
            text_color=colors["text"]
        )
        self.student_lbl.configure(
            font=theme_mgr.get_font(offset=-2),
            text_color=colors["subtext"]
        )

        self.user_title.configure(
            font=theme_mgr.get_font(offset=-1, weight="bold"),
            text_color=colors["text"]
        )
        self.pwd_title.configure(
            font=theme_mgr.get_font(offset=-1, weight="bold"),
            text_color=colors["text"]
        )
        self.toggle_pwd_btn.configure(
            font=theme_mgr.get_font(offset=-3),
            text_color=colors["accent"]
        )

        self.user_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )
        self.pwd_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )

        self.err_lbl.configure(
            font=theme_mgr.get_font(offset=-1),
            text_color=colors["danger"]
        )

        self.login_btn.configure(
            font=theme_mgr.get_font(offset=1, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["accent_text"]
        )

        self.demo_btn.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
