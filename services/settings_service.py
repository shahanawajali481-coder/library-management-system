"""
Settings Service: Manages persistence of accessibility preferences (Dark Mode,
High Contrast, Font Size) and user authentication.
"""

from typing import Optional, Dict
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
    def verify_login(username: str, password: str) -> Optional[Dict]:
        """Validate user credentials against users table."""
        username = username.strip()
        pwd_hash = hash_password(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, username, role FROM users WHERE username = ? AND password = ?", (username, pwd_hash))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
