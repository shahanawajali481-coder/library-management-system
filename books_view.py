"""
Books Management View: Catalog search, category filters, sorting,
and complete CRUD operations (Add, Edit, Delete) with validation.
"""

import customtkinter as ctk
from typing import Optional, Dict, Any
from config import theme_mgr
from services.book_service import BookService
from ui.components.table import ModernTable
from ui.components.modal import BookFormModal, ConfirmModal, AlertModal


class BooksView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # 1. Action & Toolbar Header
        self.toolbar = ctk.CTkFrame(self, corner_radius=12)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        # Search box
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.load_books())

        self.search_entry = ctk.CTkEntry(
            self.toolbar,
            textvariable=self.search_var,
            placeholder_text="🔍 Search books by title, author, or ISBN...",
            width=280,
            height=36
        )
        self.search_entry.pack(side="left", padx=14, pady=12)

        # Category Filter
        self.cat_var = ctk.StringVar(value="All")
        self.cat_menu = ctk.CTkComboBox(
            self.toolbar,
            variable=self.cat_var,
            values=["All"],
            width=160,
            height=36,
            command=lambda val: self.load_books()
        )
        self.cat_menu.pack(side="left", padx=(0, 10), pady=12)

        # Sort Filter
        self.sort_options = {
            "Title (A-Z)": "title",
            "Author (A-Z)": "author",
            "Category": "category",
            "Most Available": "available",
            "Total Quantity": "quantity"
        }
        self.sort_var = ctk.StringVar(value="Title (A-Z)")
        self.sort_menu = ctk.CTkComboBox(
            self.toolbar,
            variable=self.sort_var,
            values=list(self.sort_options.keys()),
            width=150,
            height=36,
            command=lambda val: self.load_books()
        )
        self.sort_menu.pack(side="left", padx=(0, 14), pady=12)

        # Action Buttons on Right
        self.btn_refresh = ctk.CTkButton(
            self.toolbar,
            text="🔄",
            width=40,
            height=36,
            command=self.load_books
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
            text="➕ Add Book",
            height=36,
            command=self._handle_add
        )
        self.btn_add.pack(side="right", padx=(0, 8), pady=12)

        # 2. Main Data Table
        table_cols = [
            ("id", "ID", 60),
            ("isbn", "ISBN", 130),
            ("title", "Book Title", 240),
            ("author", "Author(s)", 200),
            ("category", "Category", 140),
            ("quantity", "Total Qty", 80),
            ("available", "Available", 80),
            ("status", "Availability Status", 130)
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

        self.footer_lbl = ctk.CTkLabel(self.footer, text="Loading inventory...")
        self.footer_lbl.pack(side="left", padx=16, pady=6)

        self.apply_theme()
        self._refresh_categories()
        self.load_books()

    def _refresh_categories(self):
        cats = ["All"] + BookService.get_categories()
        self.cat_menu.configure(values=cats)

    def load_books(self):
        """Fetch books according to current search, filter, and sort options."""
        search = self.search_var.get().strip()
        category = self.cat_var.get()
        sort_by = self.sort_options.get(self.sort_var.get(), "title")

        books = BookService.get_all_books(search_query=search, category=category, sort_by=sort_by)

        rows = []
        tags = []
        total_copies = 0
        total_available = 0

        for b in books:
            qty = b["quantity"]
            avail = b["available"]
            total_copies += qty
            total_available += avail

            if avail == 0:
                status_str = "❌ Out of Stock"
                tag = "overdue"
            elif avail <= 2:
                status_str = f"⚠️ Low ({avail} left)"
                tag = "odd"
            else:
                status_str = "✅ Available"
                tag = "success"

            rows.append([
                b["id"],
                b["isbn"],
                b["title"],
                b["author"],
                b["category"],
                qty,
                avail,
                status_str
            ])
            tags.append(tag)

        self.table.set_data(rows, custom_tags=tags)

        # Update footer
        self.footer_lbl.configure(
            text=f"Showing {len(books)} book title(s) | {total_available} available copies of {total_copies} total inventory"
        )

    def _handle_add(self):
        def on_save(payload: dict, modal_instance):
            success, msg, book_id = BookService.add_book(
                isbn=payload["isbn"],
                title=payload["title"],
                author=payload["author"],
                category=payload["category"],
                quantity=payload["quantity"]
            )
            if success:
                modal_instance.destroy()
                self._refresh_categories()
                self.load_books()
                AlertModal(self.winfo_toplevel(), "Success", msg, alert_type="success")
            else:
                modal_instance.err_lbl.configure(text=msg)

        BookFormModal(self.winfo_toplevel(), "➕ Add New Book", on_save=on_save)

    def _handle_edit(self):
        selected_id = self.table.get_selected_id()
        if not selected_id:
            AlertModal(self.winfo_toplevel(), "Selection Required", "Please select a book from the table to edit.", alert_type="warning")
            return

        book = BookService.get_book_by_id(selected_id)
        if not book:
            AlertModal(self.winfo_toplevel(), "Error", "Selected book record could not be found.", alert_type="error")
            return

        def on_save(payload: dict, modal_instance):
            success, msg = BookService.update_book(
                book_id=selected_id,
                isbn=payload["isbn"],
                title=payload["title"],
                author=payload["author"],
                category=payload["category"],
                quantity=payload["quantity"],
                available=payload["available"]
            )
            if success:
                modal_instance.destroy()
                self._refresh_categories()
                self.load_books()
                AlertModal(self.winfo_toplevel(), "Updated", msg, alert_type="success")
            else:
                modal_instance.err_lbl.configure(text=msg)

        BookFormModal(self.winfo_toplevel(), f"✏️ Edit Book: {book['title']}", on_save=on_save, book_data=book)

    def _handle_delete(self):
        selected_id = self.table.get_selected_id()
        if not selected_id:
            AlertModal(self.winfo_toplevel(), "Selection Required", "Please select a book from the table to delete.", alert_type="warning")
            return

        book = BookService.get_book_by_id(selected_id)
        if not book:
            return

        def confirm_deletion():
            success, msg = BookService.delete_book(selected_id)
            if success:
                self._refresh_categories()
                self.load_books()
                AlertModal(self.winfo_toplevel(), "Deleted", msg, alert_type="success")
            else:
                AlertModal(self.winfo_toplevel(), "Cannot Delete", msg, alert_type="error")

        ConfirmModal(
            self.winfo_toplevel(),
            title="Delete Book",
            message=f"Are you sure you want to permanently delete '{book['title']}'?\n(Total copies: {book['quantity']})",
            on_confirm=confirm_deletion,
            confirm_text="Delete Book",
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

        self.cat_menu.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            button_color=colors["secondary_btn"],
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
