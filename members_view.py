"""
Members Management View: Student & Faculty Directory, search,
and complete CRUD operations with Phone & Email validation.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
from config import theme_mgr
from services.member_service import MemberService
from database import get_db_connection
from ui.components.table import ModernTable
from ui.components.modal import MemberFormModal, ConfirmModal, AlertModal


class MembersView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Action & Toolbar Header
        self.toolbar = ctk.CTkFrame(self, corner_radius=12)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_members())

        self.search_entry = ctk.CTkEntry(
            self.toolbar,
            textvariable=self.search_var,
            placeholder_text="🔍 Search members by ID, name, phone, or email...",
            width=320,
            height=36
        )
        self.search_entry.pack(side="left", padx=14, pady=12)

        # Sort Filter
        self.sort_options = {
            "Name (A-Z)": "name",
            "Member ID": "member_id",
            "Email Address": "email",
            "Registration Date": "id"
        }
        self.sort_var = ctk.StringVar(value="Name (A-Z)")
        self.sort_menu = ctk.CTkComboBox(
            self.toolbar,
            variable=self.sort_var,
            values=list(self.sort_options.keys()),
            width=160,
            height=36,
            command=lambda val: self.load_members()
        )
        self.sort_menu.pack(side="left", padx=(0, 14), pady=12)

        # Action Buttons on Right
        self.btn_refresh = ctk.CTkButton(
            self.toolbar,
            text="🔄",
            width=40,
            height=36,
            command=self.load_members
        )
        self.btn_refresh.pack(side="right", padx=(0, 14), pady=12)

        self.btn_delete = ctk.CTkButton(
            self.toolbar,
            text="🗑️ Delete",
            height=36,
            command=self._handle_delete
        )
        self.btn_delete.pack(side="right", padx=(0, 8), pady=12)

        self.btn_edit = ctk.CTkButton(
            self.toolbar,
            text="✏️ Edit",
            height=36,
            command=self._handle_edit
        )
        self.btn_edit.pack(side="right", padx=(0, 8), pady=12)

        self.btn_add = ctk.CTkButton(
            self.toolbar,
            text="➕ Register Member",
            height=36,
            command=self._handle_add
        )
        self.btn_add.pack(side="right", padx=(0, 8), pady=12)

        # 2. Main Data Table
        table_cols = [
            ("id", "ID", 60),
            ("member_id", "Member Code", 130),
            ("name", "Full Name", 240),
            ("phone", "Phone Number", 150),
            ("email", "Email Address", 240),
            ("active_loans", "Active Loans", 110)
        ]
        self.table = ModernTable(
            self,
            columns=table_cols,
            on_double_click=lambda row: self._handle_edit()
        )
        self.table.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 12))

        # 3. Bottom Footer Summary Bar
        self.footer = ctk.CTkFrame(self, height=36, corner_radius=8)
        self.footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        self.footer.pack_propagate(False)

        self.footer_lbl = ctk.CTkLabel(self.footer, text="Loading directory...")
        self.footer_lbl.pack(side="left", padx=16, pady=6)

        self.apply_theme()
        self.load_members()

    def _get_active_loans_count(self, member_id: int) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE member_id = ? AND status = 'Issued'", (member_id,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def load_members(self):
        """Fetch members from database with active loan counts."""
        search = self.search_var.get().strip()
        sort_by = self.sort_options.get(self.sort_var.get(), "name")

        members = MemberService.get_all_members(search_query=search, sort_by=sort_by)

        rows = []
        tags = []
        for m in members:
            loans = self._get_active_loans_count(m["id"])
            loan_str = f"{loans} book(s)" if loans > 0 else "None"
            tag = "odd" if loans > 0 else "even"

            rows.append([
                m["id"],
                m["member_id"],
                m["name"],
                m["phone"],
                m["email"],
                loan_str
            ])
            tags.append(tag)

        self.table.set_data(rows, custom_tags=tags)

        # Update footer
        self.footer_lbl.configure(text=f"Total Registered Members: {len(members)} enrolled students and faculty members")

    def _handle_add(self):
        def on_save(payload: dict, modal_instance):
            success, msg, m_id = MemberService.add_member(
                member_id=payload["member_id"],
                name=payload["name"],
                phone=payload["phone"],
                email=payload["email"]
            )
            if success:
                modal_instance.destroy()
                self.load_members()
                AlertModal(self.winfo_toplevel(), "Success", msg, alert_type="success")
            else:
                modal_instance.err_lbl.configure(text=msg)

        MemberFormModal(self.winfo_toplevel(), "➕ Register New Member", on_save=on_save)

    def _handle_edit(self):
        selected_id = self.table.get_selected_id()
        if not selected_id:
            AlertModal(self.winfo_toplevel(), "Selection Required", "Please select a member from the directory to edit.", alert_type="warning")
            return

        member = MemberService.get_member_by_id(selected_id)
        if not member:
            AlertModal(self.winfo_toplevel(), "Error", "Selected member record could not be found.", alert_type="error")
            return

        def on_save(payload: dict, modal_instance):
            success, msg = MemberService.update_member(
                id=selected_id,
                member_id=payload["member_id"],
                name=payload["name"],
                phone=payload["phone"],
                email=payload["email"]
            )
            if success:
                modal_instance.destroy()
                self.load_members()
                AlertModal(self.winfo_toplevel(), "Updated", msg, alert_type="success")
            else:
                modal_instance.err_lbl.configure(text=msg)

        MemberFormModal(self.winfo_toplevel(), f"✏️ Edit Member: {member['name']}", on_save=on_save, member_data=member)

    def _handle_delete(self):
        selected_id = self.table.get_selected_id()
        if not selected_id:
            AlertModal(self.winfo_toplevel(), "Selection Required", "Please select a member from the directory to delete.", alert_type="warning")
            return

        member = MemberService.get_member_by_id(selected_id)
        if not member:
            return

        def confirm_deletion():
            success, msg = MemberService.delete_member(selected_id)
            if success:
                self.load_members()
                AlertModal(self.winfo_toplevel(), "Deleted", msg, alert_type="success")
            else:
                AlertModal(self.winfo_toplevel(), "Cannot Delete", msg, alert_type="error")

        ConfirmModal(
            self.winfo_toplevel(),
            title="Delete Member",
            message=f"Are you sure you want to permanently delete member '{member['name']}' ({member['member_id']})?",
            on_confirm=confirm_deletion,
            confirm_text="Delete Member",
            is_danger=True
        )

    def apply_theme(self):
        colors = theme_mgr.colors

        self.toolbar.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )

        self.search_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )

        self.sort_menu.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            button_color=colors["secondary_btn"],
            text_color=colors["text"]
        )

        self.btn_refresh.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )

        self.btn_add.configure(
            font=theme_mgr.get_font(offset=0, weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["accent_text"]
        )

        self.btn_edit.configure(
            font=theme_mgr.get_font(offset=0),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )

        self.btn_delete.configure(
            font=theme_mgr.get_font(offset=0),
            fg_color=colors["danger"],
            hover_color="#b91c1c",
            text_color=colors["accent_text"]
        )

        self.footer.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.footer_lbl.configure(
            font=theme_mgr.get_font(offset=-2),
            text_color=colors["subtext"]
        )

        self.table.apply_theme()
