"""
Reports & Analytics View:
Supports 7 standard library reports with live data, search, and CSV export.
1. All Books
2. Available Books
3. Issued Books
4. Returned Books
5. Overdue Books
6. All Members
7. Fine Collection
"""

import os
from tkinter import filedialog
import customtkinter as ctk
from typing import Optional, List, Dict
from config import theme_mgr, STUDENT_NAME, STUDENT_ROLL
from services.transaction_service import TransactionService
from ui.components.table import ModernTable
from ui.components.modal import AlertModal


REPORT_TYPES = [
    "All Books",
    "Available Books",
    "Issued Books",
    "Returned Books",
    "Overdue Books",
    "All Members",
    "Fine Collection"
]


class ReportsView(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.current_headers: List[str] = []
        self.current_rows: List[List] = []
        self.table_widget: Optional[ModernTable] = None

        # 1. Top Controls Bar
        self.toolbar = ctk.CTkFrame(self, corner_radius=12)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))

        # Report Type Selector
        self.lbl_select = ctk.CTkLabel(self.toolbar, text="Select Report:", font=theme_mgr.get_font(offset=0, weight="bold"))
        self.lbl_select.pack(side="left", padx=(16, 8), pady=12)

        self.report_var = ctk.StringVar(value=REPORT_TYPES[0])
        self.report_combo = ctk.CTkComboBox(
            self.toolbar,
            variable=self.report_var,
            values=REPORT_TYPES,
            width=200,
            height=36,
            command=lambda val: self.load_report()
        )
        self.report_combo.pack(side="left", padx=(0, 14), pady=12)

        # Quick Search inside report
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._filter_report())

        self.search_entry = ctk.CTkEntry(
            self.toolbar,
            textvariable=self.search_var,
            placeholder_text="🔍 Filter report rows...",
            width=220,
            height=36
        )
        self.search_entry.pack(side="left", padx=(0, 14), pady=12)

        # Export & Refresh Buttons
        self.btn_refresh = ctk.CTkButton(
            self.toolbar,
            text="🔄",
            width=40,
            height=36,
            command=self.load_report
        )
        self.btn_refresh.pack(side="right", padx=(0, 16), pady=12)

        self.btn_export = ctk.CTkButton(
            self.toolbar,
            text="💾  Export to CSV",
            height=36,
            command=self._handle_export_csv
        )
        self.btn_export.pack(side="right", padx=(0, 10), pady=12)

        # 2. Table Container Frame
        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(4, 12))
        self.table_container.grid_rowconfigure(0, weight=1)
        self.table_container.grid_columnconfigure(0, weight=1)

        # 3. Bottom Summary
        self.footer = ctk.CTkFrame(self, height=36, corner_radius=8)
        self.footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        self.footer.pack_propagate(False)

        self.footer_lbl = ctk.CTkLabel(self.footer, text="")
        self.footer_lbl.pack(side="left", padx=16, pady=6)

        self.apply_theme()
        self.load_report()

    def load_report(self):
        """Fetch headers and rows for the selected report type and rebuild table dynamically."""
        report_name = self.report_var.get()
        self.current_headers, self.current_rows = TransactionService.get_reports_data(report_name)
        self.search_var.set("")

        # Re-build ModernTable with appropriate column definitions
        if self.table_widget:
            self.table_widget.destroy()

        col_defs = []
        for h in self.current_headers:
            col_id = h.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("₹", "inr")
            width = 160
            if "id" in col_id:
                width = 80
            elif "title" in col_id:
                width = 240
            elif "author" in col_id or "name" in col_id:
                width = 200
            elif "date" in col_id:
                width = 110
            elif "fine" in col_id or "qty" in col_id or "copies" in col_id:
                width = 100
            col_defs.append((col_id, h, width))

        self.table_widget = ModernTable(self.table_container, columns=col_defs)
        self.table_widget.grid(row=0, column=0, sticky="nsew")

        self._populate_table(self.current_rows)

    def _populate_table(self, rows: List[List]):
        tags = []
        is_overdue_report = self.report_var.get() == "Overdue Books"
        for r in rows:
            if is_overdue_report:
                tags.append("overdue")
            elif "Returned" in [str(x) for x in r]:
                tags.append("success")
            else:
                tags.append("")

        if self.table_widget:
            self.table_widget.set_data(rows, custom_tags=tags)

        self.footer_lbl.configure(
            text=f"Report: '{self.report_var.get()}' | Total Records: {len(rows)} | Generated on: {TransactionService.get_today_str()}"
        )

    def _filter_report(self):
        query = self.search_var.get().strip().lower()
        if not query:
            self._populate_table(self.current_rows)
            return

        filtered = [
            row for row in self.current_rows
            if any(query in str(cell).lower() for cell in row)
        ]
        self._populate_table(filtered)

    def _handle_export_csv(self):
        if not self.current_rows:
            AlertModal(self.winfo_toplevel(), "No Data", "There are no records to export in the current report.", alert_type="warning")
            return

        report_name = self.report_var.get().replace(" ", "_").lower()
        filename_default = f"library_report_{report_name}_{TransactionService.get_today_str()}.csv"

        filepath = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(),
            defaultextension=".csv",
            filetypes=[("CSV (Comma delimited)", "*.csv"), ("All Files", "*.*")],
            initialfile=filename_default,
            title="Export Report to CSV"
        )

        if not filepath:
            return

        success, msg = TransactionService.export_to_csv(filepath, self.current_headers, self.current_rows)
        if success:
            AlertModal(self.winfo_toplevel(), "Export Successful", msg, alert_type="success")
        else:
            AlertModal(self.winfo_toplevel(), "Export Failed", msg, alert_type="error")

    def apply_theme(self):
        colors = theme_mgr.colors

        self.toolbar.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.lbl_select.configure(
            font=theme_mgr.get_font(weight="bold"),
            text_color=colors["text"]
        )
        self.report_combo.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            button_color=colors["secondary_btn"],
            text_color=colors["text"]
        )
        self.search_entry.configure(
            font=theme_mgr.get_font(),
            fg_color=colors["input_bg"],
            border_color=colors["input_border"],
            text_color=colors["text"]
        )
        self.btn_refresh.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )
        self.btn_export.configure(
            font=theme_mgr.get_font(weight="bold"),
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
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

        if self.table_widget:
            self.table_widget.apply_theme()
