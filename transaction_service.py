"""
Transaction Service: Handles book issues, returns, automatic overdue fine calculations (₹5/day),
dashboard analytics, and reports generation with CSV export.
"""

import csv
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from database import get_db_connection
from config import FINE_PER_DAY, DEFAULT_LOAN_DAYS


class TransactionService:
    @staticmethod
    def get_today_str() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @staticmethod
    def get_default_due_date_str(days: int = DEFAULT_LOAN_DAYS) -> str:
        return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    @staticmethod
    def calculate_fine(due_date_str: str, return_date_str: Optional[str] = None) -> Tuple[int, float]:
        """
        Calculate overdue days and fine amount based on ₹5 per day.
        Returns: (overdue_days, fine_amount)
        """
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            if return_date_str:
                ref_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
            else:
                ref_date = datetime.now().date()

            if ref_date > due_date:
                overdue_days = (ref_date - due_date).days
                fine = overdue_days * FINE_PER_DAY
                return overdue_days, fine
            return 0, 0.0
        except Exception:
            return 0, 0.0

    @staticmethod
    def issue_book(book_id: int, member_id: int, issue_date_str: Optional[str] = None, due_date_str: Optional[str] = None) -> Tuple[bool, str, Optional[int]]:
        issue_date_str = issue_date_str or TransactionService.get_today_str()
        due_date_str = due_date_str or TransactionService.get_default_due_date_str()

        # Validate dates
        try:
            i_date = datetime.strptime(issue_date_str, "%Y-%m-%d").date()
            d_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            if d_date < i_date:
                return False, "Due Date cannot be earlier than Issue Date.", None
        except ValueError:
            return False, "Invalid date format. Expected YYYY-MM-DD.", None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check book availability
            cursor.execute("SELECT title, available FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book:
                return False, "Selected book was not found in the database.", None
            if book["available"] <= 0:
                return False, f"Cannot issue '{book['title']}': No available copies left.", None

            # Check member exists
            cursor.execute("SELECT name FROM members WHERE id = ?", (member_id,))
            member = cursor.fetchone()
            if not member:
                return False, "Selected member was not found in the database.", None

            # Check if member already has an active copy of this same book
            cursor.execute(
                "SELECT id FROM transactions WHERE book_id = ? AND member_id = ? AND status = 'Issued'",
                (book_id, member_id)
            )
            if cursor.fetchone():
                return False, f"Member '{member['name']}' already has an active copy of '{book['title']}' checked out.", None

            # Deduct available count
            cursor.execute("UPDATE books SET available = available - 1 WHERE id = ?", (book_id,))

            # Insert transaction
            cursor.execute("""
                INSERT INTO transactions (book_id, member_id, issue_date, due_date, return_date, status, fine)
                VALUES (?, ?, ?, ?, NULL, 'Issued', 0.0)
            """, (book_id, member_id, issue_date_str, due_date_str))

            conn.commit()
            tx_id = cursor.lastrowid
            return True, f"Book '{book['title']}' successfully issued to '{member['name']}'!", tx_id
        except Exception as e:
            conn.rollback()
            return False, f"Database transaction error: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def return_book(transaction_id: int, return_date_str: Optional[str] = None) -> Tuple[bool, str, float, int]:
        """
        Processes book return, updates availability, calculates overdue fine (₹5/day).
        Returns: (success, message, fine, overdue_days)
        """
        return_date_str = return_date_str or TransactionService.get_today_str()

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT t.*, b.title as book_title, b.quantity, b.available, m.name as member_name
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                JOIN members m ON t.member_id = m.id
                WHERE t.id = ?
            """, (transaction_id,))
            tx = cursor.fetchone()
            if not tx:
                return False, "Transaction record not found.", 0.0, 0
            if tx["status"] == "Returned":
                return False, "This book has already been returned.", 0.0, 0

            # Validate return date
            try:
                ret_d = datetime.strptime(return_date_str, "%Y-%m-%d").date()
                iss_d = datetime.strptime(tx["issue_date"], "%Y-%m-%d").date()
                if ret_d < iss_d:
                    return False, "Return Date cannot be before Issue Date.", 0.0, 0
            except ValueError:
                return False, "Invalid return date format. Expected YYYY-MM-DD.", 0.0, 0

            # Calculate overdue fine
            overdue_days, fine = TransactionService.calculate_fine(tx["due_date"], return_date_str)

            # Update book available count (capped at total quantity)
            new_available = min(tx["quantity"], tx["available"] + 1)
            cursor.execute("UPDATE books SET available = ? WHERE id = ?", (new_available, tx["book_id"]))

            # Update transaction
            cursor.execute("""
                UPDATE transactions
                SET return_date = ?, status = 'Returned', fine = ?
                WHERE id = ?
            """, (return_date_str, fine, transaction_id))

            conn.commit()

            msg = f"Book '{tx['book_title']}' returned successfully by '{tx['member_name']}'."
            if fine > 0:
                msg += f" Overdue by {overdue_days} day(s). Fine due: ₹{fine:.2f}."
            else:
                msg += " Returned on time. No overdue fine."

            return True, msg, fine, overdue_days
        except Exception as e:
            conn.rollback()
            return False, f"Database error during return: {str(e)}", 0.0, 0
        finally:
            conn.close()

    @staticmethod
    def get_active_issued_transactions(search_query: str = "") -> List[Dict]:
        """Fetch all currently issued (unreturned) books with real-time fine calculation."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            today_str = TransactionService.get_today_str()
            sql = """
                SELECT t.id, t.book_id, t.member_id, t.issue_date, t.due_date, t.status,
                       b.title as book_title, b.isbn,
                       m.name as member_name, m.member_id as member_code, m.phone
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                JOIN members m ON t.member_id = m.id
                WHERE t.status = 'Issued'
            """
            params = []
            if search_query and search_query.strip():
                q = f"%{search_query.strip()}%"
                sql += " AND (b.title LIKE ? OR b.isbn LIKE ? OR m.name LIKE ? OR m.member_id LIKE ?)"
                params.extend([q, q, q, q])

            sql += " ORDER BY t.due_date ASC"
            cursor.execute(sql, params)
            rows = [dict(r) for r in cursor.fetchall()]

            # Calculate live overdue days and fines
            for row in rows:
                overdue_days, current_fine = TransactionService.calculate_fine(row["due_date"])
                row["overdue_days"] = overdue_days
                row["current_fine"] = current_fine
                row["is_overdue"] = overdue_days > 0

            return rows
        finally:
            conn.close()

    @staticmethod
    def get_all_transactions(search_query: str = "", status: str = "All") -> List[Dict]:
        """Fetch all transactions with optional search and status filtering ('All', 'Issued', 'Returned')."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = """
                SELECT t.id, t.book_id, t.member_id, t.issue_date, t.due_date, t.return_date, t.status, t.fine,
                       b.title as book_title, b.isbn,
                       m.name as member_name, m.member_id as member_code, m.phone
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                JOIN members m ON t.member_id = m.id
                WHERE 1=1
            """
            params = []
            if status and status != "All":
                sql += " AND t.status = ?"
                params.append(status)

            if search_query and search_query.strip():
                q = f"%{search_query.strip()}%"
                sql += " AND (b.title LIKE ? OR b.isbn LIKE ? OR m.name LIKE ? OR m.member_id LIKE ?)"
                params.extend([q, q, q, q])

            sql += " ORDER BY t.id DESC"
            cursor.execute(sql, params)
            rows = [dict(r) for r in cursor.fetchall()]

            for row in rows:
                if row["status"] == "Issued":
                    overdue_days, current_fine = TransactionService.calculate_fine(row["due_date"])
                    row["overdue_days"] = overdue_days
                    row["current_fine"] = current_fine
                    row["is_overdue"] = overdue_days > 0
                else:
                    row["overdue_days"] = 0
                    row["current_fine"] = row["fine"] or 0.0
                    row["is_overdue"] = False

            return rows
        finally:
            conn.close()

    @staticmethod
    def get_transaction_by_id(transaction_id: int) -> Optional[Dict]:
        """Fetch a single transaction record with book and member metadata."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT t.*, b.title as book_title, b.isbn, b.quantity, b.available,
                       m.name as member_name, m.member_id as member_code, m.phone, m.email
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                JOIN members m ON t.member_id = m.id
                WHERE t.id = ?
            """, (transaction_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            if data["status"] == "Issued":
                od, fine = TransactionService.calculate_fine(data["due_date"])
                data["overdue_days"] = od
                data["current_fine"] = fine
                data["is_overdue"] = od > 0
            else:
                data["overdue_days"] = 0
                data["current_fine"] = data["fine"] or 0.0
                data["is_overdue"] = False
            return data
        finally:
            conn.close()

    @staticmethod
    def get_dashboard_stats() -> Dict:
        """Calculate live summary counts and financial metrics for dashboard cards and charts."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 1. Total & Available Books
            cursor.execute("SELECT COALESCE(SUM(quantity), 0) as total_qty, COALESCE(SUM(available), 0) as total_avail FROM books")
            book_counts = cursor.fetchone()
            total_books = book_counts["total_qty"]
            available_books = book_counts["total_avail"]

            # 2. Total Members
            cursor.execute("SELECT COUNT(*) FROM members")
            total_members = cursor.fetchone()[0]

            # 3. Issued Books count
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Issued'")
            issued_books = cursor.fetchone()[0]

            # 4. Overdue Books and Total Fines
            today_str = TransactionService.get_today_str()
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE status = 'Issued' AND due_date < ?", (today_str,))
            overdue_books = cursor.fetchone()[0]

            # Total collected / accrued fine
            # Sum of returned fines
            cursor.execute("SELECT COALESCE(SUM(fine), 0) FROM transactions WHERE status = 'Returned'")
            collected_fine = cursor.fetchone()[0]

            # Sum of active unreturned fines
            cursor.execute("SELECT due_date FROM transactions WHERE status = 'Issued' AND due_date < ?", (today_str,))
            unreturned_overdue = cursor.fetchall()
            active_fine = 0.0
            for row in unreturned_overdue:
                _, fine = TransactionService.calculate_fine(row["due_date"])
                active_fine += fine

            total_fine = collected_fine + active_fine

            # 5. Category Distribution for Charts
            cursor.execute("SELECT category, SUM(quantity) as count FROM books GROUP BY category ORDER BY count DESC")
            cat_rows = cursor.fetchall()
            category_distribution = {r["category"]: r["count"] for r in cat_rows}

            # 6. Recent Activity (last 6 transactions)
            cursor.execute("""
                SELECT t.id, t.issue_date, t.due_date, t.return_date, t.status, t.fine,
                       b.title as book_title, m.name as member_name
                FROM transactions t
                JOIN books b ON t.book_id = b.id
                JOIN members m ON t.member_id = m.id
                ORDER BY t.id DESC LIMIT 6
            """)
            recent = [dict(r) for r in cursor.fetchall()]

            return {
                "total_books": total_books,
                "available_books": available_books,
                "issued_books": issued_books,
                "total_members": total_members,
                "overdue_books": overdue_books,
                "total_fine": total_fine,
                "category_distribution": category_distribution,
                "recent_transactions": recent
            }
        finally:
            conn.close()

    @staticmethod
    def get_reports_data(report_type: str) -> Tuple[List[str], List[List]]:
        """
        Generate headers and row data for the 7 requested reports:
        - All Books
        - Available Books
        - Issued Books
        - Returned Books
        - Overdue Books
        - All Members
        - Fine Collection
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        today_str = TransactionService.get_today_str()

        try:
            if report_type == "All Books":
                headers = ["ID", "ISBN", "Title", "Author", "Category", "Quantity", "Available"]
                cursor.execute("SELECT id, isbn, title, author, category, quantity, available FROM books ORDER BY title ASC")
                rows = [list(r) for r in cursor.fetchall()]

            elif report_type == "Available Books":
                headers = ["ID", "ISBN", "Title", "Author", "Category", "Available Copies", "Total Copies"]
                cursor.execute("SELECT id, isbn, title, author, category, available, quantity FROM books WHERE available > 0 ORDER BY available DESC")
                rows = [list(r) for r in cursor.fetchall()]

            elif report_type == "Issued Books":
                headers = ["Tx ID", "Book Title", "ISBN", "Member Name", "Member ID", "Issue Date", "Due Date", "Status"]
                cursor.execute("""
                    SELECT t.id, b.title, b.isbn, m.name, m.member_id, t.issue_date, t.due_date, t.status
                    FROM transactions t
                    JOIN books b ON t.book_id = b.id
                    JOIN members m ON t.member_id = m.id
                    WHERE t.status = 'Issued'
                    ORDER BY t.due_date ASC
                """)
                rows = [list(r) for r in cursor.fetchall()]

            elif report_type == "Returned Books":
                headers = ["Tx ID", "Book Title", "Member Name", "Issue Date", "Due Date", "Return Date", "Fine (₹)"]
                cursor.execute("""
                    SELECT t.id, b.title, m.name, t.issue_date, t.due_date, t.return_date, printf('₹%.2f', t.fine)
                    FROM transactions t
                    JOIN books b ON t.book_id = b.id
                    JOIN members m ON t.member_id = m.id
                    WHERE t.status = 'Returned'
                    ORDER BY t.return_date DESC
                """)
                rows = [list(r) for r in cursor.fetchall()]

            elif report_type == "Overdue Books":
                headers = ["Tx ID", "Book Title", "Member Name", "Phone", "Due Date", "Overdue Days", "Accrued Fine (₹)"]
                cursor.execute("""
                    SELECT t.id, b.title, m.name, m.phone, t.due_date
                    FROM transactions t
                    JOIN books b ON t.book_id = b.id
                    JOIN members m ON t.member_id = m.id
                    WHERE t.status = 'Issued' AND t.due_date < ?
                    ORDER BY t.due_date ASC
                """, (today_str,))
                base_rows = cursor.fetchall()
                rows = []
                for r in base_rows:
                    od, fine = TransactionService.calculate_fine(r["due_date"])
                    rows.append([r["id"], r["title"], r["name"], r["phone"], r["due_date"], f"{od} days", f"₹{fine:.2f}"])

            elif report_type == "All Members":
                headers = ["ID", "Member ID", "Full Name", "Phone Number", "Email Address"]
                cursor.execute("SELECT id, member_id, name, phone, email FROM members ORDER BY name ASC")
                rows = [list(r) for r in cursor.fetchall()]

            elif report_type == "Fine Collection":
                headers = ["Tx ID", "Book Title", "Member Name", "Due Date", "Return Date", "Status", "Fine (₹)"]
                cursor.execute("""
                    SELECT t.id, b.title, m.name, t.due_date, COALESCE(t.return_date, 'Not Returned'), t.status, t.fine
                    FROM transactions t
                    JOIN books b ON t.book_id = b.id
                    JOIN members m ON t.member_id = m.id
                    WHERE t.fine > 0 OR (t.status = 'Issued' AND t.due_date < ?)
                    ORDER BY t.due_date ASC
                """, (today_str,))
                raw_rows = cursor.fetchall()
                rows = []
                for r in raw_rows:
                    fine_val = r["fine"]
                    if r["status"] == "Issued":
                        _, live_fine = TransactionService.calculate_fine(r["due_date"])
                        fine_val = max(fine_val, live_fine)
                    rows.append([r["id"], r["title"], r["name"], r["due_date"], r[4], r["status"], f"₹{fine_val:.2f}"])
            else:
                headers = []
                rows = []

            return headers, rows
        finally:
            conn.close()

    @staticmethod
    def export_to_csv(filepath: str, headers: List[str], rows: List[List]) -> Tuple[bool, str]:
        """Export table report rows to a CSV file."""
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            return True, f"Successfully exported {len(rows)} records to {filepath}!"
        except Exception as e:
            return False, f"Failed to export CSV: {str(e)}"
