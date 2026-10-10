"""
Issue & Return Book View:
Tab 1: Issue Book (Book selection, Member selection, Due Date calculator).
Tab 2: Return Book (Active loans directory, live overdue fine calculator at ₹5/day, fine collection).
"""

from datetime import datetime, timedelta
import customtkinter as ctk
from typing import Optional, Dict, List
from config import theme_mgr, FINE_PER_DAY, DEFAULT_LOAN_DAYS, CURRENCY_SYMBOL
from services.book_service import BookService
from services.member_service import MemberService
from services.transaction_service import TransactionService
from ui.components.table import ModernTable
from ui.components.modal import AlertModal, ConfirmModal


class IssueReturnView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Tabview
        self.tabview = ctk.CTkTabview(self, corner_radius=12)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=(12, 16))

        self.tab_issue = self.tabview.add("📤  Issue Book")
        self.tab_return = self.tabview.add("📥  Return Book & Fine Management")

        # Book & Member cache for Issue tab
        self.books_cache = []
        self.members_cache = []

        self._build_issue_tab()
        self._build_return_tab()

        self.apply_theme()
        self.load_issue_dropdowns()
        self.load_active_loans()

    # =========================================================================
    # TAB 1: ISSUE BOOK
    # =========================================================================
    def _build_issue_tab(self):
        container = ctk.CTkScrollableFrame(self.tab_issue, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=16)

        # Section Title
        self.issue_header = ctk.CTkLabel(
            container,
            text="Issue a Book to a Library Member",
            anchor="w"
        )
        self.issue_header.pack(anchor="w", pady=(0, 4))

        self.issue_sub = ctk.CTkLabel(
            container,
            text=f"Standard loan duration: {DEFAULT_LOAN_DAYS} days. Overdue fine rate: {CURRENCY_SYMBOL}{FINE_PER_DAY:.2f} per day.",
            anchor="w"
        )
        self.issue_sub.pack(anchor="w", pady=(0, 16))

        # Form Box
        self.form_card = ctk.CTkFrame(container, corner_radius=12)
        self.form_card.pack(fill="x", pady=(0, 16))
        self.form_card.grid_columnconfigure(0, weight=1)
        self.form_card.grid_columnconfigure(1, weight=1)

        # 1. Select Book
        self.lbl_book = ctk.CTkLabel(self.form_card, text="1. Select Book (Available Copies Only) *", anchor="w")
        self.lbl_book.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        self.book_select_var = ctk.StringVar()
        self.book_combo = ctk.CTkComboBox(
            self.form_card,
            variable=self.book_select_var,
            values=["Loading books..."],
            height=38,
            command=self._on_book_selected
        )
        self.book_combo.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 14))

        # 2. Select Member
        self.lbl_member = ctk.CTkLabel(self.form_card, text="2. Select Member (Student / Faculty) *", anchor="w")
        self.lbl_member.grid(row=0, column=1, sticky="w", padx=20, pady=(16, 4))

        self.member_select_var = ctk.StringVar()
        self.member_combo = ctk.CTkComboBox(
            self.form_card,
            variable=self.member_select_var,
            values=["Loading members..."],
            height=38,
            command=self._on_member_selected
        )
        self.member_combo.grid(row=1, column=1, sticky="ew", padx=20, pady=(0, 14))

        # 3. Dates
        self.lbl_issue_date = ctk.CTkLabel(self.form_card, text="3. Issue Date (YYYY-MM-DD) *", anchor="w")
        self.lbl_issue_date.grid(row=2, column=0, sticky="w", padx=20, pady=(4, 4))

        self.issue_date_var = ctk.StringVar(value=TransactionService.get_today_str())
        self.issue_date_entry = ctk.CTkEntry(self.form_card, textvariable=self.issue_date_var, height=38)
        self.issue_date_entry.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 14))
        self.issue_date_var.trace_add("write", lambda *args: self._auto_calculate_due_date())

        self.lbl_due_date = ctk.CTkLabel(self.form_card, text=f"4. Due Date (Auto +{DEFAULT_LOAN_DAYS} Days) *", anchor="w")
        self.lbl_due_date.grid(row=2, column=1, sticky="w", padx=20, pady=(4, 4))

        self.due_date_var = ctk.StringVar(value=TransactionService.get_default_due_date_str())
        self.due_date_entry = ctk.CTkEntry(self.form_card, textvariable=self.due_date_var, height=38)
        self.due_date_entry.grid(row=3, column=1, sticky="ew", padx=20, pady=(0, 14))

        # Preview Badges
        self.preview_box = ctk.CTkFrame(self.form_card, fg_color="transparent")
        self.preview_box.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 16))

        self.book_preview_lbl = ctk.CTkLabel(self.preview_box, text="📖 Book details will appear here upon selection.", anchor="w")
        self.book_preview_lbl.pack(anchor="w", pady=(0, 4))

        self.member_preview_lbl = ctk.CTkLabel(self.preview_box, text="👤 Member details will appear here upon selection.", anchor="w")
        self.member_preview_lbl.pack(anchor="w")

        # Submit Button Box
        self.btn_issue_submit = ctk.CTkButton(
            container,
            text="📤 Confirm & Issue Book",
            height=44,
            command=self._handle_issue_submit
        )
        self.btn_issue_submit.pack(anchor="e", pady=(0, 10))

    def _auto_calculate_due_date(self):
        try:
            curr = datetime.strptime(self.issue_date_var.get().strip(), "%Y-%m-%d").date()
            due = curr + timedelta(days=DEFAULT_LOAN_DAYS)
            self.due_date_var.set(due.strftime("%Y-%m-%d"))
        except Exception:
            pass

    def load_issue_dropdowns(self):
        """Populate book and member dropdowns with available data."""
        self.books_cache = BookService.get_available_books()
        self.members_cache = MemberService.get_all_members()

        if self.books_cache:
            book_vals = [f"ID {b['id']} | {b['title']} (Avail: {b['available']})" for b in self.books_cache]
            self.book_combo.configure(values=book_vals)
            self.book_combo.set(book_vals[0])
            self._on_book_selected(book_vals[0])
        else:
            self.book_combo.configure(values=["No books currently available in library"])
            self.book_combo.set("No books currently available in library")
            self.book_preview_lbl.configure(text="⚠️ No books have available copies to issue.")

        if self.members_cache:
            mem_vals = [f"{m['name']} ({m['member_id']})" for m in self.members_cache]
            self.member_combo.configure(values=mem_vals)
            self.member_combo.set(mem_vals[0])
            self._on_member_selected(mem_vals[0])
        else:
            self.member_combo.configure(values=["No members registered"])
            self.member_combo.set("No members registered")
            self.member_preview_lbl.configure(text="⚠️ No registered members found.")

    def _on_book_selected(self, choice: str):
        if not self.books_cache:
            return
        idx = self.book_combo._values.index(choice) if choice in self.book_combo._values else 0
        if idx < len(self.books_cache):
            b = self.books_cache[idx]
            self.book_preview_lbl.configure(
                text=f"📖 Book: {b['title']} | Author: {b['author']} | Category: {b['category']} | Available: {b['available']}/{b['quantity']}"
            )

    def _on_member_selected(self, choice: str):
        if not self.members_cache:
            return
        idx = self.member_combo._values.index(choice) if choice in self.member_combo._values else 0
        if idx < len(self.members_cache):
            m = self.members_cache[idx]
            self.member_preview_lbl.configure(
                text=f"👤 Member: {m['name']} | ID: {m['member_id']} | Phone: {m['phone']} | Email: {m['email']}"
            )

    def _handle_issue_submit(self):
        if not self.books_cache:
            AlertModal(self.winfo_toplevel(), "Error", "No available books to issue.", alert_type="error")
            return
        if not self.members_cache:
            AlertModal(self.winfo_toplevel(), "Error", "No registered members found.", alert_type="error")
            return

        # Get selected book
        book_idx = self.book_combo._values.index(self.book_select_var.get())
        selected_book = self.books_cache[book_idx]

        # Get selected member
        mem_idx = self.member_combo._values.index(self.member_select_var.get())
        selected_member = self.members_cache[mem_idx]

        issue_date = self.issue_date_var.get().strip()
        due_date = self.due_date_var.get().strip()

        success, msg, tx_id = TransactionService.issue_book(
            book_id=selected_book["id"],
            member_id=selected_member["id"],
            issue_date_str=issue_date,
            due_date_str=due_date
        )

        if success:
            AlertModal(self.winfo_toplevel(), "Book Issued", msg, alert_type="success")
            self.load_issue_dropdowns()
            self.load_active_loans()
        else:
            AlertModal(self.winfo_toplevel(), "Issue Failed", msg, alert_type="error")

    # =========================================================================
    # TAB 2: RETURN BOOK & FINE MANAGEMENT
    # =========================================================================
    def _build_return_tab(self):
        self.tab_return.grid_rowconfigure(1, weight=1)
        self.tab_return.grid_columnconfigure(0, weight=1)

        # Top Bar
        self.ret_toolbar = ctk.CTkFrame(self.tab_return, corner_radius=10)
        self.ret_toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))

        self.ret_search_var = ctk.StringVar()
        self.ret_search_var.trace_add("write", lambda *args: self.load_active_loans())

        self.ret_search_entry = ctk.CTkEntry(
            self.ret_toolbar,
            textvariable=self.ret_search_var,
            placeholder_text="🔍 Filter issued books by title, member, or ISBN...",
            width=360,
            height=36
        )
        self.ret_search_entry.pack(side="left", padx=14, pady=10)

        self.btn_ret_refresh = ctk.CTkButton(
            self.ret_toolbar,
            text="🔄 Refresh",
            width=90,
            height=36,
            command=self.load_active_loans
        )
        self.btn_ret_refresh.pack(side="right", padx=14, pady=10)

        # Main Table of Active Loans
        ret_cols = [
            ("id", "Tx ID", 60),
            ("book_title", "Book Title", 220),
            ("isbn", "ISBN", 130),
            ("member_name", "Borrower Name", 180),
            ("member_code", "Member ID", 110),
            ("issue_date", "Issue Date", 100),
            ("due_date", "Due Date", 100),
            ("overdue_days", "Overdue", 100),
            ("current_fine", f"Fine ({CURRENCY_SYMBOL})", 100)
        ]
        self.ret_table = ModernTable(
            self.tab_return,
            columns=ret_cols,
            on_select=self._on_loan_selected
        )
        self.ret_table.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 10))

        # Bottom Return Action Panel
        self.ret_action_card = ctk.CTkFrame(self.tab_return, corner_radius=12)
        self.ret_action_card.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 14))
        self.ret_action_card.grid_columnconfigure(0, weight=1)
        self.ret_action_card.grid_columnconfigure(1, weight=0)

        self.ret_summary_lbl = ctk.CTkLabel(
            self.ret_action_card,
            text="Select an issued book above to calculate overdue fines and process return.",
            anchor="w"
        )
        self.ret_summary_lbl.grid(row=0, column=0, sticky="w", padx=20, pady=14)

        self.btn_process_return = ctk.CTkButton(
            self.ret_action_card,
            text="📥 Return Selected Book",
            height=40,
            command=self._handle_return_submit
        )
        self.btn_process_return.grid(row=0, column=1, sticky="e", padx=20, pady=14)

    def load_active_loans(self):
        """Fetch unreturned books with live overdue fine calculations."""
        search = self.ret_search_var.get().strip()
        loans = TransactionService.get_active_issued_transactions(search_query=search)

        rows = []
        tags = []
        for l in loans:
            od = l["overdue_days"]
            fine = l["current_fine"]
            od_str = f"{od} days" if od > 0 else "On Time"
            fine_str = f"{CURRENCY_SYMBOL}{fine:.2f}"
            tag = "overdue" if od > 0 else "even"

            rows.append([
                l["id"],
                l["book_title"],
                l["isbn"],
                l["member_name"],
                l["member_code"],
                l["issue_date"],
                l["due_date"],
                od_str,
                fine_str
            ])
            tags.append(tag)

        self.ret_table.set_data(rows, custom_tags=tags)

    def _on_loan_selected(self, selected_row: dict):
        tx_id = selected_row.get("id")
        title = selected_row.get("book_title")
        member = selected_row.get("member_name")
        due = selected_row.get("due_date")

        overdue_days, fine = TransactionService.calculate_fine(due)
        if overdue_days > 0:
            summary = (
                f"⚠️ Selected: '{title}' issued to {member} | Due: {due} | "
                f"OVERDUE by {overdue_days} day(s) | Fine Due: {CURRENCY_SYMBOL}{fine:.2f} (at {CURRENCY_SYMBOL}{FINE_PER_DAY:.2f}/day)"
            )
            self.btn_process_return.configure(text=f"📥 Return & Collect {CURRENCY_SYMBOL}{fine:.2f} Fine")
        else:
            summary = f"✅ Selected: '{title}' issued to {member} | Due: {due} | Returned on time (No Fine)"
            self.btn_process_return.configure(text="📥 Return Book (No Fine)")

        self.ret_summary_lbl.configure(text=summary)

    def _handle_return_submit(self):
        selected_id = self.ret_table.get_selected_id()
        if not selected_id:
            AlertModal(self.winfo_toplevel(), "Selection Required", "Please select a loan record from the table above to return.", alert_type="warning")
            return

        def confirm_return():
            today_str = TransactionService.get_today_str()
            success, msg, fine, overdue_days = TransactionService.return_book(selected_id, today_str)
            if success:
                self.load_active_loans()
                self.load_issue_dropdowns()
                AlertModal(self.winfo_toplevel(), "Book Returned", msg, alert_type="success")
                self.ret_summary_lbl.configure(text="Book returned successfully. Inventory stock restored.")
                self.btn_process_return.configure(text="📥 Return Selected Book")
            else:
                AlertModal(self.winfo_toplevel(), "Return Error", msg, alert_type="error")

        ConfirmModal(
            self.winfo_toplevel(),
            title="Confirm Book Return",
            message=f"Process return for Transaction #{selected_id} today ({TransactionService.get_today_str()})?",
            on_confirm=confirm_return,
            confirm_text="Confirm Return"
        )

    def apply_theme(self):
        colors = theme_mgr.colors

        # Tabview
        self.tabview.configure(
            fg_color=colors["card_bg"],
            segmented_button_fg_color=colors["bg"],
            segmented_button_selected_color=colors["accent"],
            segmented_button_selected_hover_color=colors["accent_hover"],
            segmented_button_unselected_color=colors["secondary_btn"],
            segmented_button_unselected_hover_color=colors["secondary_hover"],
            text_color=colors["text"]
        )

        # Issue Tab
        self.issue_header.configure(
            font=theme_mgr.get_font(offset=4, weight="bold"),
            text_color=colors["text"]
        )
        self.issue_sub.configure(
            font=theme_mgr.get_font(offset=-2),
            text_color=colors["subtext"]
        )

        self.form_card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )

        labels = [self.lbl_book, self.lbl_member, self.lbl_issue_date, self.lbl_due_date]
        for l in labels:
            l.configure(font=theme_mgr.get_font(offset=-1, weight="bold"), text_color=colors["text"])

        self.book_combo.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            button_color=colors["secondary_btn"],
            text_color=colors["text"]
        )
        self.member_combo.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            button_color=colors["secondary_btn"],
            text_color=colors["text"]
        )
        self.issue_date_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )
        self.due_date_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )

        self.book_preview_lbl.configure(font=theme_mgr.get_font(offset=-1), text_color=colors["accent"])
        self.member_preview_lbl.configure(font=theme_mgr.get_font(offset=-1), text_color=colors["subtext"])

        self.btn_issue_submit.configure(
            font=theme_mgr.get_font(weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["accent_text"]
        )

        # Return Tab
        self.ret_toolbar.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.ret_search_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )
        self.btn_ret_refresh.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
        self.ret_action_card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.ret_summary_lbl.configure(
            font=theme_mgr.get_font(offset=0),
            text_color=colors["text"]
        )
        self.btn_process_return.configure(
            font=theme_mgr.get_font(weight="bold"),
            fg_color=colors["success"],
            hover_color="#047857",
            text_color=colors["accent_text"]
        )

        self.ret_table.apply_theme()
