"""
Dashboard View: Overview KPI Metrics, Embedded Matplotlib Analytics Charts,
Quick Shortcuts, and Recent Activity Table.
"""

import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from typing import Callable, Optional
from config import theme_mgr, CURRENCY_SYMBOL
from services.transaction_service import TransactionService
from ui.components.stat_card import StatCard
from ui.components.table import ModernTable


class DashboardView(ctk.CTkScrollableFrame):
    def __init__(self, master, navigate_to: Optional[Callable[[str], None]] = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.navigate_to = navigate_to
        self.chart_canvas = None

        # Grid configuration
        self.grid_columnconfigure(0, weight=1)

        # 1. Top KPI Stat Cards Grid (2 rows x 3 cols or responsive flow)
        self.stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=16, pady=(16, 12))
        for col in range(3):
            self.stats_frame.grid_columnconfigure(col, weight=1, uniform="stat_col")

        colors = theme_mgr.colors

        self.card_books = StatCard(self.stats_frame, title="Total Books", value="0", icon="📚", accent_color=colors["info"])
        self.card_books.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.card_avail = StatCard(self.stats_frame, title="Available Books", value="0", icon="✅", accent_color=colors["success"])
        self.card_avail.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        self.card_issued = StatCard(self.stats_frame, title="Issued Copies", value="0", icon="📤", accent_color=colors["accent"])
        self.card_issued.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.card_overdue = StatCard(self.stats_frame, title="Overdue Loans", value="0", icon="⚠️", accent_color=colors["danger"])
        self.card_overdue.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

        self.card_fines = StatCard(self.stats_frame, title="Total Fines (₹5/day)", value="₹0.00", icon="💰", accent_color=colors["warning"])
        self.card_fines.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.card_members = StatCard(self.stats_frame, title="Registered Members", value="0", icon="👥", accent_color=colors["info"])
        self.card_members.grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        # 2. Middle Section: Charts + Quick Actions
        self.middle_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.middle_frame.pack(fill="x", padx=16, pady=8)
        self.middle_frame.grid_columnconfigure(0, weight=3)
        self.middle_frame.grid_columnconfigure(1, weight=1)

        # Left: Matplotlib Category Distribution Chart Box
        self.chart_card = ctk.CTkFrame(self.middle_frame, corner_radius=12)
        self.chart_card.grid(row=0, column=0, padx=(6, 8), pady=6, sticky="nsew")

        self.chart_header = ctk.CTkLabel(
            self.chart_card,
            text="📊 Book Inventory by Category",
            anchor="w"
        )
        self.chart_header.pack(anchor="w", padx=16, pady=(12, 4))

        self.chart_plot_container = ctk.CTkFrame(self.chart_card, fg_color="transparent", height=240)
        self.chart_plot_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Right: Quick Action Shortcuts
        self.actions_card = ctk.CTkFrame(self.middle_frame, corner_radius=12)
        self.actions_card.grid(row=0, column=1, padx=(8, 6), pady=6, sticky="nsew")

        self.actions_header = ctk.CTkLabel(
            self.actions_card,
            text="⚡ Quick Actions",
            anchor="w"
        )
        self.actions_header.pack(anchor="w", padx=16, pady=(14, 10))

        self.btn_issue = ctk.CTkButton(
            self.actions_card,
            text="📤  Issue Book",
            height=38,
            command=lambda: self._nav("Issue / Return")
        )
        self.btn_issue.pack(fill="x", padx=16, pady=5)

        self.btn_return = ctk.CTkButton(
            self.actions_card,
            text="📥  Return Book & Collect Fine",
            height=38,
            command=lambda: self._nav("Issue / Return")
        )
        self.btn_return.pack(fill="x", padx=16, pady=5)

        self.btn_add_book = ctk.CTkButton(
            self.actions_card,
            text="📚  Manage Books Catalog",
            height=38,
            command=lambda: self._nav("Books")
        )
        self.btn_add_book.pack(fill="x", padx=16, pady=5)

        self.btn_add_mem = ctk.CTkButton(
            self.actions_card,
            text="👥  Manage Members Directory",
            height=38,
            command=lambda: self._nav("Members")
        )
        self.btn_add_mem.pack(fill="x", padx=16, pady=5)

        self.btn_reports = ctk.CTkButton(
            self.actions_card,
            text="📈  View Reports & CSV Export",
            height=38,
            command=lambda: self._nav("Reports")
        )
        self.btn_reports.pack(fill="x", padx=16, pady=5)

        # 3. Bottom Section: Recent Activity Table
        self.recent_card = ctk.CTkFrame(self, corner_radius=12)
        self.recent_card.pack(fill="both", expand=True, padx=22, pady=(10, 24))

        self.recent_header_frame = ctk.CTkFrame(self.recent_card, fg_color="transparent")
        self.recent_header_frame.pack(fill="x", padx=16, pady=(14, 8))

        self.recent_header_lbl = ctk.CTkLabel(
            self.recent_header_frame,
            text="🕒 Recent Library Transactions",
            anchor="w"
        )
        self.recent_header_lbl.pack(side="left")

        self.btn_refresh = ctk.CTkButton(
            self.recent_header_frame,
            text="🔄 Refresh",
            width=90,
            height=30,
            command=self.refresh_data
        )
        self.btn_refresh.pack(side="right")

        table_cols = [
            ("id", "Tx ID", 70),
            ("book_title", "Book Title", 220),
            ("member_name", "Member Name", 160),
            ("issue_date", "Issue Date", 100),
            ("due_date", "Due Date", 100),
            ("return_date", "Return Date", 100),
            ("status", "Status", 100),
            ("fine", f"Fine ({CURRENCY_SYMBOL})", 90)
        ]
        self.recent_table = ModernTable(self.recent_card, columns=table_cols, height=220)
        self.recent_table.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.apply_theme()
        self.refresh_data()

    def _nav(self, destination: str):
        if self.navigate_to:
            self.navigate_to(destination)

    def refresh_data(self):
        """Fetch fresh stats from database and update KPI cards, charts, and table."""
        try:
            stats = TransactionService.get_dashboard_stats()

            # Update KPI Cards
            self.card_books.update_value(str(stats["total_books"]))
            self.card_avail.update_value(str(stats["available_books"]))
            self.card_issued.update_value(str(stats["issued_books"]))
            self.card_overdue.update_value(
                str(stats["overdue_books"]),
                subtitle="Requires attention" if stats["overdue_books"] > 0 else "All loans in order"
            )
            self.card_fines.update_value(f"{CURRENCY_SYMBOL}{stats['total_fine']:.2f}")
            self.card_members.update_value(str(stats["total_members"]))

            # Render Matplotlib Chart
            self._render_chart(stats["category_distribution"])

            # Update Recent Transactions Table
            recent_rows = []
            tags = []
            for tx in stats["recent_transactions"]:
                ret_date = tx.get("return_date") or "-"
                status = tx.get("status", "")
                fine_val = f"{CURRENCY_SYMBOL}{tx.get('fine', 0.0):.2f}"
                recent_rows.append([
                    tx["id"],
                    tx["book_title"],
                    tx["member_name"],
                    tx["issue_date"],
                    tx["due_date"],
                    ret_date,
                    status,
                    fine_val
                ])
                if status == "Returned":
                    tags.append("success")
                elif status == "Issued" and tx.get("due_date", "") < TransactionService.get_today_str():
                    tags.append("overdue")
                else:
                    tags.append("")

            self.recent_table.set_data(recent_rows, custom_tags=tags)
        except Exception as e:
            print(f"[Dashboard refresh error]: {e}")

    def _render_chart(self, category_data: dict):
        """Draw an embedded Matplotlib donut/bar chart matching current theme palette."""
        colors = theme_mgr.colors

        # Destroy old canvas if exists
        for child in self.chart_plot_container.winfo_children():
            child.destroy()

        if not category_data:
            empty_lbl = ctk.CTkLabel(
                self.chart_plot_container,
                text="No inventory data available for chart.",
                font=theme_mgr.get_font()
            )
            empty_lbl.pack(pady=40)
            return

        # Prepare data
        categories = list(category_data.keys())[:6]
        counts = [category_data[c] for c in categories]

        # Matplotlib Figure
        fig = Figure(figsize=(5.5, 2.4), dpi=90)
        fig.patch.set_facecolor(colors["card_bg"])

        ax = fig.add_subplot(111)
        ax.set_facecolor(colors["card_bg"])

        # Curated vibrant palette
        chart_colors = [
            colors["accent"],
            colors["info"],
            colors["success"],
            colors["warning"],
            "#a855f7",
            "#ec4899"
        ][:len(categories)]

        bars = ax.barh(categories, counts, color=chart_colors, height=0.55, edgecolor=colors["border"])
        ax.invert_yaxis()  # Labels read top-to-bottom

        # Styling
        ax.tick_params(colors=colors["subtext"], labelsize=9)
        for spine in ax.spines.values():
            spine.set_color(colors["border"])

        ax.grid(axis="x", linestyle="--", alpha=0.3, color=colors["subtext"])
        ax.set_axisbelow(True)

        # Value annotations on bars
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.15,
                bar.get_y() + bar.get_height() / 2,
                f"{int(width)}",
                va="center",
                ha="left",
                color=colors["text"],
                fontsize=9,
                fontweight="bold"
            )

        fig.tight_layout()

        # Canvas widget
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_plot_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)

    def apply_theme(self):
        """Update colors and fonts for all dashboard sub-elements."""
        colors = theme_mgr.colors

        # KPI cards
        self.card_books.apply_theme()
        self.card_avail.apply_theme()
        self.card_issued.apply_theme()
        self.card_overdue.apply_theme()
        self.card_fines.apply_theme()
        self.card_members.apply_theme()

        # Chart Card
        self.chart_card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.chart_header.configure(
            font=theme_mgr.get_font(offset=2, weight="bold"),
            text_color=colors["text"]
        )

        # Quick Actions Card
        self.actions_card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.actions_header.configure(
            font=theme_mgr.get_font(offset=2, weight="bold"),
            text_color=colors["text"]
        )

        action_buttons = [self.btn_issue, self.btn_return, self.btn_add_book, self.btn_add_mem, self.btn_reports]
        for btn in action_buttons:
            btn.configure(
                font=theme_mgr.get_font(offset=0),
                fg_color=colors["secondary_btn"],
                hover_color=colors["secondary_hover"],
                text_color=colors["secondary_text"]
            )

        # Recent Transactions Card
        self.recent_card.configure(
            fg_color=colors["card_bg"],
            border_color=colors["border"],
            border_width=colors["border_width"]
        )
        self.recent_header_lbl.configure(
            font=theme_mgr.get_font(offset=2, weight="bold"),
            text_color=colors["text"]
        )
        self.btn_refresh.configure(
            font=theme_mgr.get_font(offset=-1),
            fg_color=colors["secondary_btn"],
            hover_color=colors["secondary_hover"],
            text_color=colors["secondary_text"]
        )

        # Table
        self.recent_table.apply_theme()
