"""
Database management and SQLite schema initialization for Library Management System.
Includes automatic seeding of default admin, settings, and initial books & members.
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import DB_DIR, DB_PATH, DEFAULT_FONT_SIZE


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt for security."""
    salt = "lib_sys_salt_2026"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def get_db_connection():
    """Create and return a thread-safe connection with foreign key support."""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and default sample data."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'Admin'
        );
    """)

    # 2. Books Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            available INTEGER NOT NULL CHECK(available >= 0)
        );
    """)

    # 3. Members Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        );
    """)

    # 4. Transactions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            status TEXT DEFAULT 'Issued',
            fine REAL DEFAULT 0.0,
            FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
            FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
        );
    """)

    # 5. Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dark_mode INTEGER DEFAULT 1,
            high_contrast INTEGER DEFAULT 0,
            font_size INTEGER DEFAULT 14
        );
    """)

    conn.commit()

    # Seed Default Admin Account
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", hash_password("admin123"), "Admin")
        )

    # Seed Default Settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO settings (dark_mode, high_contrast, font_size) VALUES (?, ?, ?)",
            (1, 0, DEFAULT_FONT_SIZE)
        )

    # Seed Sample Data if Books table is empty
    cursor.execute("SELECT COUNT(*) FROM books")
    if cursor.fetchone()[0] == 0:
        sample_books = [
            ("978-0131103627", "The C Programming Language", "Brian W. Kernighan, Dennis M. Ritchie", "Computer Science", 6, 5),
            ("978-0262033848", "Introduction to Algorithms", "Thomas H. Cormen, Charles E. Leiserson", "Algorithms", 8, 7),
            ("978-0132350884", "Clean Code", "Robert C. Martin", "Software Engineering", 5, 4),
            ("978-1449355730", "Learning Python", "Mark Lutz", "Programming", 10, 10),
            ("978-0201633610", "Design Patterns: Elements of Reusable Object-Oriented Software", "Erich Gamma, Richard Helm", "Software Engineering", 4, 3),
            ("978-0073523323", "Database System Concepts", "Abraham Silberschatz, Henry F. Korth", "Databases", 7, 7),
            ("978-0134685991", "Effective Java", "Joshua Bloch", "Programming", 6, 6),
            ("978-0136006633", "Artificial Intelligence: A Modern Approach", "Stuart Russell, Peter Norvig", "AI & ML", 5, 4),
            ("978-0321573513", "Algorithms in C++", "Robert Sedgewick", "Algorithms", 4, 4),
            ("978-1118531648", "HTML and CSS: Design and Build Websites", "Jon Duckett", "Web Development", 6, 6)
        ]
        cursor.executemany(
            "INSERT INTO books (isbn, title, author, category, quantity, available) VALUES (?, ?, ?, ?, ?, ?)",
            sample_books
        )

    # Seed Sample Members if Members table is empty
    cursor.execute("SELECT COUNT(*) FROM members")
    if cursor.fetchone()[0] == 0:
        sample_members = [
            ("MEM-101", "Shahanawaj Ansari", "9876543210", "shahanawaj@college.edu"),
            ("MEM-102", "Aarav Sharma", "9823456781", "aarav.sharma@college.edu"),
            ("MEM-103", "Priya Patel", "9890123456", "priya.patel@college.edu"),
            ("MEM-104", "Rohan Verma", "9765432109", "rohan.verma@college.edu"),
            ("MEM-105", "Sneha Kulkarni", "9812345678", "sneha.k@college.edu")
        ]
        cursor.executemany(
            "INSERT INTO members (member_id, name, phone, email) VALUES (?, ?, ?, ?)",
            sample_members
        )

    # Seed Sample Transactions if empty (gives realistic initial data on dashboard)
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        today = datetime.now().date()
        # Active loan within due date
        issue_1 = (today - timedelta(days=5)).strftime("%Y-%m-%d")
        due_1 = (today + timedelta(days=9)).strftime("%Y-%m-%d")

        # Active loan overdue by 4 days (to test overdue fine calculation)
        issue_2 = (today - timedelta(days=18)).strftime("%Y-%m-%d")
        due_2 = (today - timedelta(days=4)).strftime("%Y-%m-%d")

        # Returned transaction with paid fine
        issue_3 = (today - timedelta(days=25)).strftime("%Y-%m-%d")
        due_3 = (today - timedelta(days=11)).strftime("%Y-%m-%d")
        return_3 = (today - timedelta(days=8)).strftime("%Y-%m-%d")

        # Active loan 3
        issue_4 = (today - timedelta(days=3)).strftime("%Y-%m-%d")
        due_4 = (today + timedelta(days=11)).strftime("%Y-%m-%d")

        sample_transactions = [
            (1, 1, issue_1, due_1, None, "Issued", 0.0),
            (2, 2, issue_2, due_2, None, "Issued", 20.0),   # 4 days overdue * ₹5 = ₹20
            (3, 3, issue_3, due_3, return_3, "Returned", 15.0), # 3 days overdue * ₹5 = ₹15
            (5, 4, issue_4, due_4, None, "Issued", 0.0)
        ]
        cursor.executemany(
            "INSERT INTO transactions (book_id, member_id, issue_date, due_date, return_date, status, fine) VALUES (?, ?, ?, ?, ?, ?, ?)",
            sample_transactions
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully at:", DB_PATH)
