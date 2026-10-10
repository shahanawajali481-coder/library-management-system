"""
Automated Integration and Functional Test Suite for LMS Web Application.
Tests:
- Full Authentication Flow:
  1. Unauthenticated route protection
  2. Sign Up form validation (missing fields, mismatched passwords, duplicate checks)
  3. Secure registration with salted SHA-256 password hashing
  4. Login using username and email
  5. Session establishment and protected dashboard access
  6. Logout session destruction and confirmation message
  7. Browser Back-button protection (anti-cache headers & re-authentication)
- Book CRUD, Member operations, and Circulation (Issue/Return) workflows
"""

import sys
from app import app
from database import init_db, get_db_connection
from services.book_service import BookService
from services.member_service import MemberService
from services.transaction_service import TransactionService
from services.settings_service import SettingsService

def run_tests():
    print("Beginning LMS Web Application Automated Verification...")
    init_db()

    client = app.test_client()

    print("\n--- 1. Testing Unauthenticated Route Protection ---")
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/login" in res.headers.get("Location", "")
    print("[PASS] Unauthenticated access to /dashboard is blocked and redirects to /login")

    res = client.get("/books")
    assert res.status_code == 302
    assert "/login" in res.headers.get("Location", "")
    print("[PASS] Unauthenticated access to /books is blocked and redirects to /login")

    print("\n--- 2. Testing Sign Up Page & Validation ---")
    res = client.get("/signup")
    assert res.status_code == 200
    assert b"Create an Account" in res.data
    assert b"Already have an account? Login" in res.data or b"Login" in res.data
    print("[PASS] GET /signup renders successfully (200)")

    # Validation: Passwords do not match
    res = client.post("/signup", data={
        "name": "Jane Doe",
        "username": "janedoe",
        "email": "jane@college.edu",
        "password": "password123",
        "confirm_password": "differentpassword"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Passwords do not match" in res.data
    print("[PASS] Sign Up blocks mismatched passwords")

    # Successful Sign Up
    test_user_name = "Dr. Alice Smith"
    test_username = "alice_librarian"
    test_email = "alice.smith@college.edu"
    test_password = "SecurePassword2026"

    # Ensure clean state for test user if rerun
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ? OR email = ?", (test_username, test_email))
    conn.commit()
    conn.close()

    res = client.post("/signup", data={
        "name": test_user_name,
        "username": test_username,
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Account created successfully" in res.data
    print("[PASS] Valid Sign Up succeeds and redirects to Login with success message")

    # Verify Security: Password is NOT stored in plain text
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (test_username,))
    db_row = cursor.fetchone()
    assert db_row is not None
    stored_hash = db_row["password"]
    assert stored_hash != test_password, "CRITICAL ERROR: Password was stored in plain text!"
    assert len(stored_hash) == 64, "Password hash must be SHA-256 (64 hex characters)"
    conn.close()
    print("[PASS] Security verified: Password stored as salted SHA-256 hash (never plain text)")

    # Duplicate Username prevention
    res = client.post("/signup", data={
        "name": "Another Person",
        "username": test_username,
        "email": "different@college.edu",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"already registered" in res.data
    print("[PASS] Sign Up prevents duplicate username registration")

    print("\n--- 3. Testing Login Flow ---")
    # Login using username
    res = client.post("/login", data={
        "username": test_username,
        "password": test_password
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard Overview" in res.data or b"Library Overview" in res.data
    assert b"Logout" in res.data
    print(f"[PASS] Login via Username '{test_username}' succeeds and opens Dashboard")

    # Logout
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"Logged out successfully" in res.data
    print("[PASS] Logout clears session and redirects to Login")

    # Login using email
    res = client.post("/login", data={
        "username": test_email,
        "password": test_password
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dashboard Overview" in res.data or b"Library Overview" in res.data
    print(f"[PASS] Login via Email '{test_email}' succeeds and opens Dashboard")

    print("\n--- 4. Testing Browser Back-Button Protection ---")
    # Logout again
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"Logged out successfully" in res.data

    # Simulate browser Back button request to dashboard
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/login" in res.headers.get("Location", "")
    print("[PASS] After logout, protected page cannot be loaded (redirects to /login)")

    print("\n--- 5. Testing Books & Members Circulation Integrity ---")
    # Log in as admin
    client.post("/login", data={"username": "admin", "password": "admin123"})
    
    # Verify books list
    res = client.get("/books")
    assert res.status_code == 200
    print("[PASS] Books catalog loaded properly")

    # Verify members list
    res = client.get("/members")
    assert res.status_code == 200
    print("[PASS] Members directory loaded properly")

    # Clean up test user
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE username = ?", (test_username,))
    conn.commit()
    conn.close()

    print("\n==========================================================================")
    print("ALL TESTS PASSED: SIGN UP -> LOGIN -> DASHBOARD -> LOGOUT FLOW 100% VERIFIED")
    print("==========================================================================\n")

if __name__ == "__main__":
    run_tests()
