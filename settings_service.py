"""
Settings Service: Manages persistence of accessibility preferences (Dark Mode,
High Contrast, Font Size) and user authentication.
"""

import re
from typing import Optional, Dict, Tuple
from database import get_db_connection, hash_password
from config import theme_mgr, DEFAULT_FONT_SIZE


class SettingsService:
    @staticmethod
    def load_settings() -> Dict:
        """Load settings from SQLite database and apply them to theme_mgr."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT dark_mode, high_contrast, font_size FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                dark_mode = bool(row["dark_mode"])
                high_contrast = bool(row["high_contrast"])
                font_size = int(row["font_size"])
            else:
                dark_mode = True
                high_contrast = False
                font_size = DEFAULT_FONT_SIZE

            theme_mgr.dark_mode = dark_mode
            theme_mgr.high_contrast = high_contrast
            theme_mgr.font_size = font_size
            return {
                "dark_mode": dark_mode,
                "high_contrast": high_contrast,
                "font_size": font_size
            }
        finally:
            conn.close()

    @staticmethod
    def save_settings(dark_mode: bool, high_contrast: bool, font_size: int) -> bool:
        """Persist settings to SQLite and update theme_mgr."""
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    UPDATE settings
                    SET dark_mode = ?, high_contrast = ?, font_size = ?
                    WHERE id = ?
                """, (1 if dark_mode else 0, 1 if high_contrast else 0, font_size, row["id"]))
            else:
                cursor.execute("""
                    INSERT INTO settings (dark_mode, high_contrast, font_size)
                    VALUES (?, ?, ?)
                """, (1 if dark_mode else 0, 1 if high_contrast else 0, font_size))

            conn.commit()

            # Apply to memory
            theme_mgr.dark_mode = dark_mode
            theme_mgr.high_contrast = high_contrast
            theme_mgr.font_size = font_size
            theme_mgr.notify_listeners()
            return True
        except Exception as e:
            print(f"[SettingsService] Error saving settings: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def verify_login(identifier: str, password: str) -> Optional[Dict]:
        """Validate user credentials against users table (supports username or email)."""
        identifier = identifier.strip()
        pwd_hash = hash_password(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, username, role, name, email 
                FROM users 
                WHERE (LOWER(username) = LOWER(?) OR LOWER(COALESCE(email, '')) = LOWER(?)) 
                  AND password = ?
            """, (identifier, identifier, pwd_hash))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    @staticmethod
    def register_user(name: str, username: str, email: str, password: str, role: str = "Staff") -> Tuple[bool, str, Optional[int]]:
        """Validate and securely register a new user with hashed password."""
        name = name.strip()
        username = username.strip()
        email = email.strip()

        # 1. Validation
        if not name:
            return False, "Full Name is required.", None
        if not username:
            return False, "Username is required.", None
        if len(username) < 3:
            return False, "Username must be at least 3 characters long.", None
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            return False, "Username can only contain letters, numbers, dots, hyphens, and underscores.", None
        if not email:
            return False, "Email address is required.", None
        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            return False, "Invalid email address format (e.g. name@college.edu).", None
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # 2. Check if username already exists
            cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            if cursor.fetchone():
                return False, f"Username '{username}' is already registered. Please choose a different username.", None

            # 3. Check if email already exists
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            if cursor.fetchone():
                return False, f"An account with email '{email}' already exists. Please log in or use another email.", None

            # 4. Hash password securely
            pwd_hash = hash_password(password)

            # 5. Insert new user
            cursor.execute("""
                INSERT INTO users (username, password, role, name, email)
                VALUES (?, ?, ?, ?, ?)
            """, (username, pwd_hash, role, name, email))
            conn.commit()
            new_id = cursor.lastrowid
            return True, f"Account created successfully for '{username}'! Please sign in with your credentials.", new_id
        except Exception as e:
            return False, f"Database error during registration: {str(e)}", None
        finally:
            conn.close()

