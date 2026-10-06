"""
Book Service: Handles business logic, validation, and database operations for Books.
"""

from typing import List, Dict, Tuple, Optional
from database import get_db_connection


class BookService:
    @staticmethod
    def validate_book_data(isbn: str, title: str, author: str, category: str, quantity: int, available: int) -> Tuple[bool, str]:
        if not isbn or not isbn.strip():
            return False, "ISBN cannot be empty."
        if not title or not title.strip():
            return False, "Book Title cannot be empty."
        if not author or not author.strip():
            return False, "Author cannot be empty."
        if not category or not category.strip():
            return False, "Category cannot be empty."
        if quantity < 0:
            return False, "Quantity cannot be negative."
        if available < 0:
            return False, "Available copies cannot be negative."
        if available > quantity:
            return False, "Available copies cannot exceed Total Quantity."
        return True, ""

    @staticmethod
    def add_book(isbn: str, title: str, author: str, category: str, quantity: int) -> Tuple[bool, str, Optional[int]]:
        isbn = isbn.strip()
        title = title.strip()
        author = author.strip()
        category = category.strip()
        available = quantity

        valid, err = BookService.validate_book_data(isbn, title, author, category, quantity, available)
        if not valid:
            return False, err, None

        if quantity <= 0:
            return False, "Quantity must be a positive integer greater than 0.", None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Check unique ISBN
            cursor.execute("SELECT id FROM books WHERE isbn = ?", (isbn,))
            if cursor.fetchone():
                return False, f"A book with ISBN '{isbn}' already exists.", None

            cursor.execute(
                "INSERT INTO books (isbn, title, author, category, quantity, available) VALUES (?, ?, ?, ?, ?, ?)",
                (isbn, title, author, category, quantity, available)
            )
            conn.commit()
            book_id = cursor.lastrowid
            return True, f"Book '{title}' added successfully!", book_id
        except Exception as e:
            return False, f"Database error: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def update_book(book_id: int, isbn: str, title: str, author: str, category: str, quantity: int, available: int) -> Tuple[bool, str]:
        isbn = isbn.strip()
        title = title.strip()
        author = author.strip()
        category = category.strip()

        valid, err = BookService.validate_book_data(isbn, title, author, category, quantity, available)
        if not valid:
            return False, err

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Verify book exists
            cursor.execute("SELECT quantity, available FROM books WHERE id = ?", (book_id,))
            current = cursor.fetchone()
            if not current:
                return False, "Book not found."

            # Check ISBN uniqueness if changed
            cursor.execute("SELECT id FROM books WHERE isbn = ? AND id != ?", (isbn, book_id))
            if cursor.fetchone():
                return False, f"Another book with ISBN '{isbn}' already exists."

            # Verify that currently issued copies do not exceed new quantity
            # Issued copies = current quantity - current available
            currently_issued = current["quantity"] - current["available"]
            if quantity < currently_issued:
                return False, f"Cannot reduce quantity below currently issued copies ({currently_issued} copies currently loaned out)."

            cursor.execute("""
                UPDATE books
                SET isbn = ?, title = ?, author = ?, category = ?, quantity = ?, available = ?
                WHERE id = ?
            """, (isbn, title, author, category, quantity, available, book_id))
            conn.commit()
            return True, f"Book '{title}' updated successfully!"
        except Exception as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def delete_book(book_id: int) -> Tuple[bool, str]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT title, quantity, available FROM books WHERE id = ?", (book_id,))
            book = cursor.fetchone()
            if not book:
                return False, "Book not found."

            # Check if active loans exist
            cursor.execute("SELECT COUNT(*) FROM transactions WHERE book_id = ? AND status = 'Issued'", (book_id,))
            active_loans = cursor.fetchone()[0]
            if active_loans > 0:
                return False, f"Cannot delete '{book['title']}': There are {active_loans} active issued copy/copies. Please return them first."

            cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            conn.commit()
            return True, f"Book '{book['title']}' deleted successfully!"
        except Exception as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_all_books(search_query: str = "", category: str = "All", sort_by: str = "title") -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT * FROM books WHERE 1=1"
            params = []

            if category and category != "All":
                sql += " AND category = ?"
                params.append(category)

            if search_query and search_query.strip():
                query = f"%{search_query.strip()}%"
                sql += " AND (isbn LIKE ? OR title LIKE ? OR author LIKE ? OR category LIKE ?)"
                params.extend([query, query, query, query])

            valid_sort = {
                "id": "id ASC",
                "title": "title COLLATE NOCASE ASC",
                "author": "author COLLATE NOCASE ASC",
                "category": "category COLLATE NOCASE ASC",
                "available": "available DESC",
                "quantity": "quantity DESC"
            }
            sort_clause = valid_sort.get(sort_by, "title COLLATE NOCASE ASC")
            sql += f" ORDER BY {sort_clause}"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_available_books() -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM books WHERE available > 0 ORDER BY title COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_categories() -> List[str]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT category FROM books ORDER BY category COLLATE NOCASE ASC")
            rows = cursor.fetchall()
            return [row["category"] for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_book_by_id(book_id: int) -> Optional[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
