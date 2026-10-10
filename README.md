# 📚 Library Management System (LMS) - Web & Desktop Application

> **Academic Project**  
> **Student:** SHAHANAWAJ  
> **Roll Number:** 2410302051  
> **Stack:** Python 3, Flask, SQLite3, HTML5, CSS3, JavaScript, Jinja2, CustomTkinter  

---

## 🌟 Project Overview

The **Library Management System (LMS)** is a full-featured, production-ready library circulation and inventory platform designed to automate and streamline core library operations. Built initially with a desktop interface, it has been seamlessly transformed into a modern, responsive **Web Application** running in Google Chrome and modern browsers, while preserving 100% of the original desktop application functionality.

The platform provides librarians and college administrators with real-time visibility into book catalogs, student/faculty memberships, check-out and check-in circulation workflows, and automatic overdue fine computations.

---

## ✨ Key Features

### 1. 📊 Interactive Dashboard
- **KPI Metrics Cards:** Real-time counters for **Total Books**, **Available Copies**, **Currently Issued**, **Registered Members**, **Overdue Loans**, and **Total Fines Accrued/Collected**.
- **Visual Category Breakdown:** Progress bar analytics showing inventory distribution by academic subjects.
- **Recent Lending Activity:** Instant table log of the latest check-outs and check-ins with status chips.
- **Quick Action Bar:** Direct one-click access to Issue, Return, Add Book, and Add Member.

### 2. 📖 Books Catalog & Inventory
- **Full Catalog Browser:** View ISBN, Title, Author, Category, Total Quantity, and Available Copies.
- **Search & Filter:** Instant multi-field search (Title, Author, ISBN) and category dropdown filtering.
- **Smart Sorting:** Sort by Title, Author, Category, Availability, or Total Quantity.
- **Add / Edit Book:** Dedicated validated forms with catalog category suggestions.
- **Safe Deletion Protection:** Enforces business rules preventing deletion of books that have active outstanding loans.
- **Synchronized Inventory:** Total quantity and available counts automatically remain consistent across all loan events.

### 3. 👥 Members Management
- **Member Directory:** Maintain student and faculty records with unique Member IDs, phone numbers, and academic emails.
- **Active Loans Counter:** Displays real-time number of unreturned books per member.
- **Member Profile & History:** Dedicated view showing member contact information and full transaction history (active loans and returned archives).
- **Validation:** Strict regex validation on phone numbers (10–15 digits) and email formats.
- **Deletion Safeguard:** Prevents deleting members who currently hold unreturned library books.

### 4. 📤 Book Circulation: Issue Workflow
- **Available Copies Dropdown:** Dynamically filters books to show only those with stock > 0.
- **Member Selector:** Quick selection of registered library members.
- **Automated Due Date Calculation:** Defaults to 14 days from issue date with customizable picker.
- **Duplicate Loan Prevention:** Blocks issuing the same book title twice to the same member simultaneously.
- **Real-Time Stock Decrement:** Decreases book available copies immediately upon checkout.

### 5. 📥 Book Circulation: Return & Fine Processing
- **Active Loans Table:** Lists all unreturned books with borrower info, issue dates, and due dates.
- **Live Overdue Fine Computation:** Automatically calculates overdue days and charges **₹5.00 per day** past the due date.
- **Return Confirmation Modal:** Interactive modal with return date picker, fine notice, and single-click check-in.
- **Automatic Stock Increment:** Restores available copy count immediately and records the closing transaction.

### 6. 📋 Transactions Ledger & Export
- **Comprehensive Ledger:** Unified chronological audit log of all book issues and returns.
- **Status Filter:** Switch between All Records, Active (Issued), and Completed (Returned).
- **Search:** Search across book titles, ISBNs, member names, and member IDs.
- **CSV Data Export:** Direct one-click CSV spreadsheet download for reports, audits, and grading.

### 7. ⚙️ Settings & Accessibility
- **Theming & Comfort:** Seamless Dark Mode / Light Mode toggle with persistence in database and session.
- **High Contrast Support:** Dedicated high-contrast accessibility mode.
- **System Information:** Live display of SQLite database path, fine rates, loan policies, and project credits.

### 8. 🔐 Authentication & Access Security
- **User Registration (Sign Up):** Create accounts with full name, unique username, validated email, and password confirmation.
- **Salted Password Hashing:** Passwords stored using SHA-256 with cryptographic salt (never stored in plain text).
- **Flexible Login:** Sign in via either username or email address with clear credential validation.
- **Route Guard Protection:** Unauthenticated requests are safely redirected to the login screen with guidance alerts.
- **Session Logout & Anti-Cache:** Visible Logout button in top bar and sidebar; anti-caching headers prevent browser Back button bypass.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Backend & Routing** | Python 3.10+, Flask 3.1+, Jinja2 Templates |
| **Database** | SQLite3 (thread-safe connections, foreign keys enabled, parameterized queries) |
| **Frontend Styling** | Vanilla CSS3 (Custom Design System, CSS Variables, Responsive Grid & Flexbox) |
| **Interactivity** | Vanilla JavaScript (ES6+ for Modals, Theme Sync, Auto-dismiss alerts, Mobile Drawer) |
| **Typography** | Google Fonts (*Inter* & *Outfit*) |
| **Desktop GUI (Preserved)** | CustomTkinter 6.0+, Matplotlib, PIL |
| **Deployment / WSGI** | Gunicorn (Linux/Cloud ready), Werkzeug |

---

## 📁 Project Structure

```text
library-management-system/
│
├── app.py                      # Flask Web Application entry point & route controllers
├── main.py                     # Desktop GUI entry point (CustomTkinter)
├── config.py                   # Central settings, themes, paths, and business logic constants
├── database.py                 # SQLite schema initialization and automatic sample seeding
├── requirements.txt            # Python dependencies (Flask, Gunicorn, CustomTkinter, etc.)
├── test_app.py                 # Automated functional & integration test suite
├── README.md                   # Complete documentation and setup guide
│
├── services/                   # Reusable Business Logic & Database Service Layer
│   ├── __init__.py
│   ├── book_service.py         # Book CRUD, inventory synchronization, validation
│   ├── member_service.py       # Member CRUD, contact validation, loan history
│   ├── transaction_service.py  # Issue/Return workflows, fine calculations, dashboard stats
│   └── settings_service.py     # Theme preferences and admin authentication
│
├── templates/                  # Jinja2 HTML5 Templates
│   ├── base.html               # Master layout (sidebar, topbar, theme switcher, modals)
│   ├── dashboard.html          # Overview KPI stats, category progress bars, recent activity
│   ├── books.html              # Books catalog, search, category filter, stock badges
│   ├── book_form.html          # Add / Edit book form
│   ├── members.html            # Members directory, loan counts, search & sorting
│   ├── member_form.html        # Add / Edit member form
│   ├── member_details.html     # Member profile & full borrowing history
│   ├── issue_book.html         # Book check-out form with auto due-date calculation
│   ├── return_book.html        # Active loans list & check-in modal
│   ├── transactions.html       # Full transactions ledger with status filtering
│   └── settings.html           # Visual preferences, accessibility, system parameters & CSV export
│
├── static/                     # Static Web Assets
│   ├── css/
│   │   └── style.css           # Modern CSS tokens, dark/light themes, tables, responsive cards
│   └── js/
│       └── script.js           # Client-side theme switcher, modals, mobile drawer, alerts
│
├── database/
│   └── library.db              # SQLite Database file (auto-generated if missing)
│
└── ui/                         # Preserved Desktop GUI Components & Views
    ├── components/
    └── views/
```

---

## 🚀 Installation & Local Setup

### 1. Prerequisites
- Python 3.10 or higher installed on your system.
- Google Chrome (or any modern web browser).

### 2. Clone or Navigate to Directory
```bash
cd "library management system"
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 How to Run the Applications

### 🌐 Running the Web Application (Recommended for Chrome & Online)
Run the following command in your terminal:
```bash
python app.py
```

You will see the startup banner:
```text
======================================================================
  LIBRARY MANAGEMENT SYSTEM
  College Project | SHAHANAWAJ (Roll No: 2410302051)
======================================================================
  * Status: Running locally
  * Local Web URL: http://127.0.0.1:5000
  * Open in Google Chrome: http://127.0.0.1:5000
  * Database: .../database/library.db
======================================================================
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 🔑 Default Login Credentials
- **Username:** `admin`
- **Password:** `admin123`
*(A 1-click **⚡ Auto-Fill Demo** button is provided on the web login page for immediate sign-in.)*

---

### 🖥️ Running the Desktop GUI (Preserved CustomTkinter App)
If you wish to run the original desktop version:
```bash
python main.py
```

---

### 🧪 Running the Automated Verification Test Suite
To verify that all routes, database operations, business logic, issue/return cycles, and restrictions are working:
```bash
python test_app.py
```

---

## 🌐 Deploying Online (To Send Live URL to Teacher)

The project is structured and configured to be deployed online to any cloud platform in minutes:

### Option A: Render (Free Tier)
1. Push this project to GitHub.
2. Sign in to [Render](https://render.com) and create a **New Web Service**.
3. Connect your GitHub repository.
4. Set:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Create Web Service**. Render will assign you a live HTTPS URL (e.g. `https://my-library-lms.onrender.com`) that you can send directly to your teacher.

### Option B: Railway
1. Sign in to [Railway](https://railway.app).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Railway automatically detects `requirements.txt` and runs `gunicorn app:app` or `python app.py`.

### Option C: PythonAnywhere
1. Create a free account at [PythonAnywhere](https://www.pythonanywhere.com).
2. Upload the project files or `git clone`.
3. In the **Web** tab, configure a Flask application pointing to `app.py`.

---

## 📸 Screenshots Section (Placeholders)

| Screen | Description |
|---|---|
| **Dashboard** | ![Dashboard Preview](https://via.placeholder.com/800x450?text=Dashboard+Overview) |
| **Books Catalog** | ![Books Catalog Preview](https://via.placeholder.com/800x450?text=Books+Catalog) |
| **Member Management** | ![Members Directory](https://via.placeholder.com/800x450?text=Members+Directory) |
| **Issue & Return Flow** | ![Circulation Workflow](https://via.placeholder.com/800x450?text=Issue+and+Return+Books) |
| **Transactions Ledger** | ![Transactions Audit Log](https://via.placeholder.com/800x450?text=Transactions+Ledger) |

---

## 🔮 Future Improvements

1. **Email Overdue Reminders:** Automated SMTP background service notifying students 2 days prior to due dates.
2. **Barcode / QR Code Scanner:** Web camera integration via HTML5 MediaDevices API to scan book ISBN barcodes during checkout.
3. **Multi-Role Authentication:** Student self-service portal to reserve books online before picking them up.
4. **Enhanced Analytics:** Monthly circulation trend charts using Chart.js.

---

## 👨‍🎓 Author & Academic Information

- **Student Name:** SHAHANAWAJ
- **Roll Number:** 2410302051
- **Project Title:** Library Management System (LMS)
- **Course / Degree:** Bachelor of Technology / Computer Science & Engineering
- **Academic Year:** 2026
