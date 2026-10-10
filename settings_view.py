"""
Accessibility & Settings View:
- Full accessibility controls (Q12): Dark Mode, High Contrast Mode, Dynamic Font Scaling (12-24pt).
- Live Font Size Preview.
- System information, Database metrics, and Re-seeding option.
- Academic Project Information for SHAHANAWAJ (Roll No: 2410302051).
"""

import os
import customtkinter as ctk
from config import (
    theme_mgr,
    DB_PATH,
    STUDENT_NAME,
    STUDENT_ROLL,
    APP_TITLE,
    AVAILABLE_FONT_SIZES,
    DEFAULT_FONT_SIZE,
    FINE_PER_DAY,
    DEFAULT_LOAN_DAYS,
    CURRENCY_SYMBOL
)
from services.settings_service import SettingsService
from database import init_db
from ui.components.modal import AlertModal, ConfirmModal


class SettingsView(ctk.CTkScrollableFrame):
    def __init__(self, master, on_theme_change=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.on_theme_change_callback = on_theme_change

        self.grid_columnconfigure(0, weight=1)

        # 1. Accessibility Card (Q12)
        self.access_card = ctk.CTkFrame(self, corner_radius=12)
        self.access_card.pack(fill="x", padx=20, pady=(16, 12))
        self.access_card.grid_columnconfigure(0, weight=1)

        self.access_title = ctk.CTkLabel(self.access_card, text="♿ Accessibility & Visual Comfort (Q12)", anchor="w")
        self.access_title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        self.access_desc = ctk.CTkLabel(
            self.access_card,
            text="Adjust theme modes and application font scale. Changes apply instantly across all screens and persist in SQLite.",
            anchor="w",
            wraplength=680,
            justify="left"
        )
        self.access_desc.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 14))

        # Toggles Row
        toggles_box = ctk.CTkFrame(self.access_card, fg_color="transparent")
        toggles_box.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 12))

        # Dark Mode Switch
        self.dark_mode_var = ctk.BooleanVar(value=theme_mgr.dark_mode)
        self.dark_switch = ctk.CTkSwitch(
            toggles_box,
            text="🌙  Dark Mode Appearance",
            variable=self.dark_mode_var,
            command=self._handle_dark_toggle
        )
        self.dark_switch.pack(side="left", padx=(0, 32))

        # High Contrast Switch
        self.high_c_var = ctk.BooleanVar(value=theme_mgr.high_contrast)
        self.high_c_switch = ctk.CTkSwitch(
            toggles_box,
            text="⚡  High Contrast Mode (Pure Black & Gold)",
            variable=self.high_c_var,
            command=self._handle_high_contrast_toggle
        )
        self.high_c_switch.pack(side="left")

        # Font Scale Slider Box
        font_box = ctk.CTkFrame(self.access_card, fg_color="transparent")
        font_box.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 16))
        font_box.grid_columnconfigure(1, weight=1)

        self.lbl_slider = ctk.CTkLabel(font_box, text=f"Text Scaling ({theme_mgr.font_size} pt):", width=160, anchor="w")
        self.lbl_slider.grid(row=0, column=0, sticky="w")

        self.font_slider = ctk.CTkSlider(
            font_box,
            from_=AVAILABLE_FONT_SIZES[0],
            to=AVAILABLE_FONT_SIZES[-1],
            number_of_steps=len(AVAILABLE_FONT_SIZES) - 1,
            command=self._handle_font_slider
        )
        self.font_slider.set(theme_mgr.font_size)
        self.font_slider.grid(row=0, column=1, sticky="ew", padx=16)

        self.lbl_slider_val = ctk.CTkLabel(font_box, text=f"{theme_mgr.font_size} pt", width=60)
        self.lbl_slider_val.grid(row=0, column=2, sticky="e")

        # Live Font Preview Card
        self.preview_card = ctk.CTkFrame(self.access_card, corner_radius=8)
        self.preview_card.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 16))

        self.preview_lbl = ctk.CTkLabel(
            self.preview_card,
            text="Accessibility Preview: The quick brown fox jumps over the lazy dog. 1234567890",
            anchor="w",
            wraplength=660,
            justify="left"
        )
        self.preview_lbl.pack(padx=16, pady=12, fill="x")

        # 2. System Rules & Database Info Card
        self.db_card = ctk.CTkFrame(self, corner_radius=12)
        self.db_card.pack(fill="x", padx=20, pady=6)
        self.db_card.grid_columnconfigure(0, weight=1)

        self.db_title = ctk.CTkLabel(self.db_card, text="⚙️ Library System Rules & Database Status", anchor="w")
        self.db_title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        db_size_kb = 0
        if os.path.exists(DB_PATH):
            db_size_kb = round(os.path.getsize(DB_PATH) / 1024, 1)

        info_text = (
            f"• Standard Loan Period: {DEFAULT_LOAN_DAYS} Days\n"
            f"• Overdue Fine Rate: {CURRENCY_SYMBOL}{FINE_PER_DAY:.2f} per day past the due date\n"
            f"• Database Storage: SQLite3 Relational Database with Foreign Key Enforcement\n"
            f"• Database File: {DB_PATH} ({db_size_kb} KB)"
        )
        self.db_info_lbl = ctk.CTkLabel(
            self.db_card,
            text=info_text,
            anchor="w",
            justify="left"
        )
        self.db_info_lbl.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 14))

        db_btn_box = ctk.CTkFrame(self.db_card, fg_color="transparent")
        db_btn_box.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 16))

        self.btn_reseed = ctk.CTkButton(
            db_btn_box,
            text="🔄 Re-seed Sample Data",
            height=34,
            command=self._handle_reseed
        )
        self.btn_reseed.pack(side="left", padx=(0, 10))

        self.btn_reset_defaults = ctk.CTkButton(
            db_btn_box,
            text="↺ Reset Theme to Defaults",
            height=34,
            command=self._handle_reset_defaults
        )
        self.btn_reset_defaults.pack(side="left")

        # 3. Project & Student Information Card
        self.project_card = ctk.CTkFrame(self, corner_radius=12)
        self.project_card.pack(fill="x", padx=20, pady=(6, 24))
        self.project_card.grid_columnconfigure(0, weight=1)

        self.project_title = ctk.CTkLabel(self.project_card, text="🎓 College Project Accreditation", anchor="w")
        self.project_title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 8))

        student_info = (
            f"• Project Title: {APP_TITLE}\n"
            f"• Developer: {STUDENT_NAME}\n"
            f"• College Roll Number: {STUDENT_ROLL}\n"
            f"• Architecture: Modern Modular Layered Architecture (UI / Business Services / Database SQLite)\n"
            f"• Built with: CustomTkinter 5.2+, Matplotlib 3.8+, Python 3.14"
        )
        self.project_desc_lbl = ctk.CTkLabel(
            self.project_card,
            text=student_info,
            anchor="w",
            justify="left"
        )
        self.project_desc_lbl.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 16))

        self.apply_theme()

    def _handle_dark_toggle(self):
        enabled = self.dark_mode_var.get()
        if self.high_c_var.get():
            self.high_c_var.set(False)
            theme_mgr.set_high_contrast(False)

        theme_mgr.set_dark_mode(enabled)
        SettingsService.save_settings(theme_mgr.dark_mode, theme_mgr.high_contrast, theme_mgr.font_size)
        if self.on_theme_change_callback:
            self.on_theme_change_callback()

    def _handle_high_contrast_toggle(self):
        enabled = self.high_c_var.get()
        theme_mgr.set_high_contrast(enabled)
        SettingsService.save_settings(theme_mgr.dark_mode, theme_mgr.high_contrast, theme_mgr.font_size)
        if self.on_theme_change_callback:
            self.on_theme_change_callback()

    def _handle_font_slider(self, val):
        nearest = min(AVAILABLE_FONT_SIZES, key=lambda x: abs(x - val))
        self.lbl_slider.configure(text=f"Text Scaling ({nearest} pt):")
        self.lbl_slider_val.configure(text=f"{nearest} pt")
        theme_mgr.set_font_size(nearest)
        SettingsService.save_settings(theme_mgr.dark_mode, theme_mgr.high_contrast, nearest)
        if self.on_theme_change_callback:
            self.on_theme_change_callback()

    def _handle_reset_defaults(self):
        self.dark_mode_var.set(True)
        self.high_c_var.set(False)
        self.font_slider.set(DEFAULT_FONT_SIZE)
        self.lbl_slider.configure(text=f"Text Scaling ({DEFAULT_FONT_SIZE} pt):")
        self.lbl_slider_val.configure(text=f"{DEFAULT_FONT_SIZE} pt")

        theme_mgr.set_dark_mode(True)
        theme_mgr.set_high_contrast(False)
        theme_mgr.set_font_size(DEFAULT_FONT_SIZE)
        SettingsService.save_settings(True, False, DEFAULT_FONT_SIZE)
        if self.on_theme_change_callback:
            self.on_theme_change_callback()
        AlertModal(self.winfo_toplevel(), "Reset Complete", "Theme settings have been restored to defaults.", alert_type="info")

    def _handle_reseed(self):
        def do_reseed():
            init_db()
            AlertModal(self.winfo_toplevel(), "Database Initialized", "Database seeded with initial sample books, members, and transactions.", alert_type="success")

        ConfirmModal(
            self.winfo_toplevel(),
            title="Re-seed Database",
            message="This will ensure all default sample tables, books, and members are present in SQLite.\nContinue?",
            on_confirm=do_reseed,
            confirm_text="Re-seed Data"
        )

    def apply_theme(self):
        colors = theme_mgr.colors

        # Cards
        cards = [self.access_card, self.db_card, self.project_card]
        for c in cards:
            c.configure(
                fg_color=colors["card_bg"],
                border_color=colors["border"],
                border_width=colors["border_width"]
            )

        # Headers
        headers = [self.access_title, self.db_title, self.project_title]
        for h in headers:
            h.configure(
                font=theme_mgr.get_font(offset=2, weight="bold"),
                text_color=colors["text"]
            )

        # Body texts
        self.access_desc.configure(
            font=theme_mgr.get_font(offset=-1),
            text_color=colors["subtext"]
        )
        self.db_info_lbl.configure(
            font=theme_mgr.get_font(offset=-1),
            text_color=colors["text"]
        )
        self.project_desc_lbl.configure(
            font=theme_mgr.get_font(offset=-1),
            text_color=colors["text"]
        )

        # Switches
        self.dark_switch.configure(
            font=theme_mgr.get_font(offset=0),
            text_color=colors["text"],
            progress_color=colors["accent"]
        )
        self.high_c_switch.configure(
            font=theme_mgr.get_font(offset=0),
            text_color=colors["text"],
            progress_color=colors["warning"]
        )

        # Slider & Preview
        self.lbl_slider.configure(font=theme_mgr.get_font(offset=0, weight="bold"), text_color=colors["text"])
        self.lbl_slider_val.configure(font=theme_mgr.get_font(offset=0, weight="bold"), text_color=colors["accent"])
        self.font_slider.configure(
            button_color=colors["accent"],
            button_hover_color=colors["accent_hover"],
            progress_color=colors["accent"]
        )

        self.preview_card.configure(
            fg_color=colors["bg"],
            border_color=colors["border"],
            border_width=1
        )
        self.preview_lbl.configure(
            font=theme_mgr.get_font(offset=1),
            text_color=colors["accent"]
        )

        # Buttons
        self.btn_reseed.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
        self.btn_reset_defaults.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
