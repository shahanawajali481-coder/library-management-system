"""
Member Service: Handles business logic, validation, and database operations for Library Members.
"""

import re
from typing import List, Dict, Tuple, Optional
from database import get_db_connection


class MemberService:
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number: 10 to 15 digits, allowing optional leading +."""
        clean = phone.strip().replace(" ", "").replace("-", "")
        return bool(re.match(r"^\+?\d{10,15}$", clean))

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        email_clean = email.strip()
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return bool(re.match(pattern, email_clean))

    @staticmethod
    def validate_member_data(member_id: str, name: str, phone: str, email: str) -> Tuple[bool, str]:
        if not member_id or not member_id.strip():
            return False, "Member ID cannot be empty."
        if not name or not name.strip():
            return False, "Member Name cannot be empty."
        if not phone or not phone.strip():
            return False, "Phone Number cannot be empty."
        if not MemberService.validate_phone(phone):
            return False, "Invalid phone number. Please enter a valid 10-15 digit mobile number."
        if not email or not email.strip():
            return False, "Email address cannot be empty."
        if not MemberService.validate_email(email):
            return False, "Invalid email address format (e.g., student@college.edu)."
        return True, ""

    @staticmethod
    def add_member(member_id: str, name: str, phone: str, email: str) -> Tuple[bool, str, Optional[int]]:
        member_id = member_id.strip()
        name = name.strip()
        phone = phone.strip()
        email = email.strip()

        valid, err = MemberService.validate_member_data(member_id, name, phone, email)
        if not valid:
            return False, err, None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM members WHERE member_id = ?", (member_id,))
            if cursor.fetchone():
                return False, f"A member with ID '{member_id}' already exists.", None

            cursor.execute(
                "INSERT INTO members (member_id, name, phone, email) VALUES (?, ?, ?, ?)",
                (member_id, name, phone, email)
            )
            conn.commit()
            m_id = cursor.lastrowid
            return True, f"Member '{name}' ({member_id}) registered successfully!", m_id
        except Exception as e:
            return False, f"Database error: {str(e)}", None
        finally:
            conn.close()

    @staticmethod
    def update_member(id: int, member_id: str, name: str, phone: str, email: str) -> Tuple[bool, str]:
        member_id = member_id.strip()
        name = name.strip()
        phone = phone.strip()
        email = email.strip()

        valid, err = MemberService.validate_member_data(member_id, name, phone, email)
        if not valid:
            return False, err

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM members WHERE id = ?", (id,))
            if not cursor.fetchone():
                return False, "Member not found."

            cursor.execute("SELECT id FROM members WHERE member_id = ? AND id != ?", (member_id, id))
            if cursor.fetchone():
                return False, f"Another member already has ID '{member_id}'."

            cursor.execute("""
                UPDATE members
                SET member_id = ?, name = ?, phone = ?, email = ?
                WHERE id = ?
            """, (member_id, name, phone, email, id))
            conn.commit()
            return True, f"Member '{name}' updated successfully!"
        except Exception as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def delete_member(id: int) -> Tuple[bool, str]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT member_id, name FROM members WHERE id = ?", (id,))
            member = cursor.fetchone()
            if not member:
                return False, "Member not found."

            cursor.execute("SELECT COUNT(*) FROM transactions WHERE member_id = ? AND status = 'Issued'", (id,))
            active_loans = cursor.fetchone()[0]
            if active_loans > 0:
                return False, f"Cannot delete '{member['name']}': Member currently has {active_loans} unreturned book(s)."

            cursor.execute("DELETE FROM members WHERE id = ?", (id,))
            conn.commit()
            return True, f"Member '{member['name']}' deleted successfully!"
        except Exception as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_all_members(search_query: str = "", sort_by: str = "name") -> List[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            sql = "SELECT * FROM members WHERE 1=1"
            params = []

            if search_query and search_query.strip():
                query = f"%{search_query.strip()}%"
                sql += " AND (member_id LIKE ? OR name LIKE ? OR phone LIKE ? OR email LIKE ?)"
                params.extend([query, query, query, query])

            valid_sort = {
                "id": "id ASC",
                "member_id": "member_id COLLATE NOCASE ASC",
                "name": "name COLLATE NOCASE ASC",
                "email": "email COLLATE NOCASE ASC"
            }
            sort_clause = valid_sort.get(sort_by, "name COLLATE NOCASE ASC")
            sql += f" ORDER BY {sort_clause}"

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_member_by_id(id: int) -> Optional[Dict]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM members WHERE id = ?", (id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
