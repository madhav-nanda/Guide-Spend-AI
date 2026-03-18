from fpdf import FPDF

class ProjectPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.cell(0, 10, "GuideSpend AI - Project Documentation", align="C")
            self.ln(5)
            self.set_draw_color(180, 180, 180)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 14)
        self.ln(4)
        self.cell(0, 10, title)
        self.ln(8)
        self.set_draw_color(100, 100, 100)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.ln(2)
        self.cell(0, 8, title)
        self.ln(8)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=10):
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.cell(indent, 5.5, "")
        self.set_font("Helvetica", "", 10)
        self.cell(4, 5.5, "- ")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bold_bullet(self, bold_part, normal_part, indent=10):
        self.cell(indent, 5.5, "")
        self.cell(4, 5.5, "- ")
        self.set_font("Helvetica", "B", 10)
        w = self.get_string_width(bold_part)
        self.cell(w, 5.5, bold_part)
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, normal_part)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 9)
        self.set_fill_color(240, 240, 240)
        lines = text.split("\n")
        for line in lines:
            self.cell(10, 5, "")
            self.cell(0, 5, line, fill=True)
            self.ln(5)
        self.set_font("Helvetica", "", 10)
        self.ln(3)

    def table_row(self, cols, widths, bold=False):
        self.set_font("Helvetica", "B" if bold else "", 9)
        h = 7
        for i, col in enumerate(cols):
            self.cell(widths[i], h, col, border=1)
        self.ln(h)

    def check_page_break(self, h=40):
        if self.get_y() + h > 270:
            self.add_page()


pdf = ProjectPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)

# ============================================================
# COVER PAGE
# ============================================================
pdf.add_page()
pdf.ln(60)
pdf.set_font("Helvetica", "B", 28)
pdf.cell(0, 15, "GuideSpend AI", align="C")
pdf.ln(15)
pdf.set_font("Helvetica", "", 16)
pdf.cell(0, 10, "Project Documentation", align="C")
pdf.ln(20)
pdf.set_draw_color(120, 120, 120)
pdf.line(60, pdf.get_y(), 150, pdf.get_y())
pdf.ln(15)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 8, "AI-Powered Financial Management Platform", align="C")
pdf.ln(10)
pdf.cell(0, 8, "Full-Stack Architecture & Technical Reference", align="C")
pdf.ln(30)
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 8, "Tech Stack: React + Flask + PostgreSQL + Plaid", align="C")
pdf.ln(8)
pdf.cell(0, 8, "March 2026", align="C")

# ============================================================
# TABLE OF CONTENTS
# ============================================================
pdf.add_page()
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Table of Contents")
pdf.ln(15)

toc_items = [
    ("1.", "Project Overview"),
    ("2.", "Tech Stack"),
    ("3.", "Project Structure (File Tree)"),
    ("4.", "Backend Architecture (Flask API)"),
    ("5.", "Database Schema"),
    ("6.", "Frontend Architecture (React)"),
    ("7.", "Frontend Components"),
    ("8.", "API Client & Authentication State"),
    ("9.", "Critical Flows"),
    ("10.", "Security Layers"),
    ("11.", "How Frontend Connects to Backend"),
    ("12.", "Future Features (Tables Ready, Not Wired)"),
]
for num, item in toc_items:
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(12, 8, num)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, item)
    pdf.ln(8)

# ============================================================
# 1. PROJECT OVERVIEW
# ============================================================
pdf.add_page()
pdf.section_title("1. Project Overview")
pdf.body_text(
    "GuideSpend AI is a secure, AI-powered financial management platform. "
    "It helps users manage their finances by connecting real bank accounts via Plaid, "
    "tracking transactions, visualizing spending patterns, and providing analytics through "
    "an intuitive dashboard."
)
pdf.body_text("Core capabilities:")
pdf.bullet("Connect real bank accounts using Plaid (sandbox mode)")
pdf.bullet("Automatic transaction syncing from linked accounts")
pdf.bullet("Manual transaction entry")
pdf.bullet("Spending analytics with pie and bar charts")
pdf.bullet("Account balance overview across all linked banks")
pdf.bullet("Secure JWT-based authentication")
pdf.bullet("Encrypted storage of sensitive banking tokens")

# ============================================================
# 2. TECH STACK
# ============================================================
pdf.section_title("2. Tech Stack")

pdf.sub_title("Frontend")
pdf.bullet("React 19.2.0 - UI framework")
pdf.bullet("Vite 7.3.1 - Build tool and dev server")
pdf.bullet("Tailwind CSS 4.2.1 - Utility-first styling")
pdf.bullet("React Router DOM 7.13.1 - Client-side routing")
pdf.bullet("Axios 1.13.6 - HTTP client for API calls")
pdf.bullet("Recharts 3.7.0 - Data visualization (charts)")
pdf.bullet("React-Plaid-Link 4.1.1 - Plaid widget integration")
pdf.bullet("Lucide React 0.575.0 - Icon library")

pdf.ln(3)
pdf.sub_title("Backend")
pdf.bullet("Flask 3.1.3 - Python web framework")
pdf.bullet("Flask-JWT-Extended 4.7.1 - JWT authentication")
pdf.bullet("Flask-CORS 6.0.2 - Cross-origin request handling")
pdf.bullet("bcrypt 5.0.0 - Password hashing")
pdf.bullet("psycopg2-binary 2.9.11 - PostgreSQL driver")
pdf.bullet("plaid-python 38.3.0 - Plaid API client")
pdf.bullet("cryptography 46.0.5 - Fernet encryption for tokens")
pdf.bullet("python-dotenv 1.2.1 - Environment variable loading")

pdf.ln(3)
pdf.sub_title("Database & External Services")
pdf.bullet("PostgreSQL - Hosted on Supabase (AWS us-east-2)")
pdf.bullet("Plaid API - Banking data aggregation (sandbox environment)")

# ============================================================
# 3. PROJECT STRUCTURE
# ============================================================
pdf.add_page()
pdf.section_title("3. Project Structure (File Tree)")

tree = """ai-banking/
|-- backend/
|   |-- app.py                  # Flask REST API (all endpoints)
|   |-- requirements.txt        # Python dependencies
|   |-- .env                    # Environment variables
|   +-- venv/                   # Python virtual environment
|-- frontend/
|   |-- src/
|   |   |-- main.jsx            # React entry point
|   |   |-- App.jsx             # Main router component
|   |   |-- index.css           # Global styles
|   |   |-- App.css             # App-level styles
|   |   |-- api/
|   |   |   +-- axios.js        # Axios client with JWT interceptors
|   |   |-- context/
|   |   |   +-- AuthContext.jsx  # Authentication state (Context API)
|   |   |-- pages/
|   |   |   |-- Login.jsx       # Login page
|   |   |   |-- Register.jsx    # Registration page
|   |   |   +-- Dashboard.jsx   # Main dashboard
|   |   +-- components/
|   |       |-- BackgroundLayer.jsx     # Animated gradient background
|   |       |-- BalanceCard.jsx         # Bank account card
|   |       |-- ConnectBankButton.jsx   # Plaid Link integration
|   |       |-- TransactionsTable.jsx   # Transaction list table
|   |       +-- Charts.jsx             # Pie + Bar chart analytics
|   |-- package.json            # Node.js dependencies
|   |-- vite.config.js          # Vite dev server + proxy config
|   +-- index.html              # HTML template
|-- models.py                   # SQLAlchemy ORM models (reference)
|-- generate_data.py            # Seed data generator script
|-- erd_dbdiagram.txt           # Database ERD schema
+-- README.md                   # Project documentation"""

pdf.code_block(tree)

# ============================================================
# 4. BACKEND ARCHITECTURE
# ============================================================
pdf.add_page()
pdf.section_title("4. Backend Architecture (Flask API)")

pdf.body_text(
    "The entire backend is contained in a single file: backend/app.py. "
    "It is a Flask REST API that handles authentication, transaction management, "
    "and Plaid banking integration. All protected routes require a valid JWT token."
)

pdf.sub_title("4.1 Authentication Endpoints")

pdf.bold_bullet("POST /register ", "- Creates a new user account. Accepts username, email, and password. "
    "The password is hashed using bcrypt before being stored in the database.")
pdf.bold_bullet("POST /login ", "- Authenticates a user. Verifies email and password against the stored "
    "bcrypt hash. On success, returns a JWT access token that the frontend stores in localStorage.")
pdf.bold_bullet("GET /protected ", "- A test endpoint that verifies token validity. Used by the frontend "
    "on app load to check if the stored token is still valid.")

pdf.check_page_break()
pdf.sub_title("4.2 Transaction Endpoints")

pdf.bold_bullet("POST /transactions ", "- Adds a manual transaction for the authenticated user. "
    "Accepts amount, category, description, and date.")
pdf.bold_bullet("GET /transactions ", "- Retrieves all transactions for the authenticated user, "
    "ordered by date descending. Returns id, amount, category, description, date, source, "
    "and plaid_transaction_id.")
pdf.bold_bullet("DELETE /transactions/<id> ", "- Deletes a specific transaction, but only if it "
    "belongs to the authenticated user.")

pdf.check_page_break()
pdf.sub_title("4.3 Plaid Integration Endpoints")

pdf.bold_bullet("POST /plaid/create_link_token ", "- Generates a Plaid Link token. The frontend "
    "calls this to initialize the Plaid Link widget where users select and log into their bank.")
pdf.bold_bullet("POST /plaid/exchange_token ", "- After the user authenticates with their bank, "
    "Plaid returns a temporary public_token. This endpoint exchanges it for a permanent "
    "access_token, encrypts it using Fernet symmetric encryption, and stores it in the "
    "plaid_items table.")
pdf.bold_bullet("POST /plaid/sync_transactions ", "- Fetches transactions from all linked bank "
    "accounts using Plaid's cursor-based sync API. Handles three event types: ADDED (insert new), "
    "MODIFIED (update existing), and REMOVED (delete). Stores a cursor per plaid_item for "
    "incremental syncing.")
pdf.bold_bullet("GET /plaid/accounts ", "- Retrieves all linked bank accounts with real-time "
    "balances. Decrypts each stored access_token and calls the Plaid API to fetch current "
    "account information.")
pdf.bold_bullet("DELETE /plaid/disconnect ", "- Disconnects a linked bank account. Removes the "
    "plaid_item record and all associated Plaid-sourced transactions.")

pdf.check_page_break()
pdf.sub_title("4.4 Database Connection")
pdf.body_text(
    "The backend connects to a PostgreSQL database hosted on Supabase using psycopg2. "
    "The connection uses SSL (sslmode=require) for security. Connection parameters are loaded "
    "from environment variables defined in the .env file: DB_HOST, DB_PORT, DB_NAME, DB_USER, "
    "and DB_PASSWORD."
)

# ============================================================
# 5. DATABASE SCHEMA
# ============================================================
pdf.add_page()
pdf.section_title("5. Database Schema")

pdf.body_text("The project uses 7 database tables in PostgreSQL:")

pdf.sub_title("5.1 users")
pdf.body_text("Stores registered user accounts.")
widths = [50, 50, 90]
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["username", "varchar(50)", "Unique, not null"], widths)
pdf.table_row(["email", "varchar(120)", "Unique, not null"], widths)
pdf.table_row(["password_hash", "text", "bcrypt hashed password"], widths)
pdf.table_row(["created_at", "timestamp", "Default: now()"], widths)

pdf.ln(5)
pdf.sub_title("5.2 transactions")
pdf.body_text("Stores both manual and Plaid-synced transactions.")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["amount", "decimal(10,2)", "Transaction amount"], widths)
pdf.table_row(["category", "varchar(50)", "Transaction category"], widths)
pdf.table_row(["description", "text", "Transaction description"], widths)
pdf.table_row(["date", "date", "Transaction date"], widths)
pdf.table_row(["created_at", "timestamp", "Default: now()"], widths)
pdf.table_row(["plaid_transaction_id", "varchar", "Plaid ID (nullable)"], widths)
pdf.table_row(["source", "varchar", "'plaid' or 'manual'"], widths)

pdf.check_page_break(60)
pdf.ln(5)
pdf.sub_title("5.3 plaid_items")
pdf.body_text("Stores linked bank account connections with encrypted access tokens.")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["access_token", "text", "Fernet-encrypted Plaid token"], widths)
pdf.table_row(["item_id", "varchar", "Unique Plaid item identifier"], widths)
pdf.table_row(["institution_id", "varchar", "Bank institution ID"], widths)
pdf.table_row(["institution_name", "varchar", "Bank name (e.g., Chase)"], widths)
pdf.table_row(["cursor", "text", "Sync cursor for pagination"], widths)
pdf.table_row(["created_at", "timestamp", "Creation timestamp"], widths)
pdf.table_row(["updated_at", "timestamp", "Last update timestamp"], widths)

pdf.check_page_break(60)
pdf.ln(5)
pdf.sub_title("5.4 budgets")
pdf.body_text("Stores spending limits per category per month. (Not yet wired to frontend.)")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["category", "varchar(50)", "Budget category"], widths)
pdf.table_row(["limit_amount", "decimal(10,2)", "Monthly limit"], widths)
pdf.table_row(["month", "int", "Month number (1-12)"], widths)
pdf.table_row(["year", "int", "Year"], widths)
pdf.table_row(["created_at", "timestamp", "Default: now()"], widths)

pdf.check_page_break(60)
pdf.ln(5)
pdf.sub_title("5.5 fraud_logs")
pdf.body_text("Records flagged suspicious transactions. (Not yet wired to frontend.)")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["transaction_id", "int (FK)", "References transactions.id"], widths)
pdf.table_row(["rule_triggered", "varchar(100)", "Which fraud rule was matched"], widths)
pdf.table_row(["flagged_at", "timestamp", "When it was flagged"], widths)

pdf.check_page_break(60)
pdf.ln(5)
pdf.sub_title("5.6 savings")
pdf.body_text("Tracks round-up savings from transactions. (Not yet wired to frontend.)")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["source_transaction_id", "int (FK)", "References transactions.id"], widths)
pdf.table_row(["rounded_amount", "decimal(10,2)", "Amount saved via round-up"], widths)
pdf.table_row(["saved_at", "timestamp", "When saving was recorded"], widths)

pdf.check_page_break(60)
pdf.ln(5)
pdf.sub_title("5.7 recurring_transactions")
pdf.body_text("Detected recurring payments (subscriptions, bills). (Not yet wired to frontend.)")
pdf.table_row(["Column", "Type", "Notes"], widths, bold=True)
pdf.table_row(["id", "int (PK)", "Auto-increment primary key"], widths)
pdf.table_row(["user_id", "int (FK)", "References users.id"], widths)
pdf.table_row(["merchant", "varchar(100)", "Merchant name"], widths)
pdf.table_row(["average_amount", "decimal(10,2)", "Average transaction amount"], widths)
pdf.table_row(["frequency_days", "int", "Days between payments"], widths)
pdf.table_row(["last_seen", "date", "Most recent occurrence"], widths)
pdf.table_row(["annual_estimate", "decimal(10,2)", "Projected yearly cost"], widths)
pdf.table_row(["created_at", "timestamp", "Default: now()"], widths)

# ============================================================
# 6. FRONTEND ARCHITECTURE
# ============================================================
pdf.add_page()
pdf.section_title("6. Frontend Architecture (React)")

pdf.sub_title("6.1 Entry Point - main.jsx")
pdf.body_text(
    "This is where the React app starts. It wraps the entire application in three layers:\n"
    "1. BrowserRouter - Enables client-side URL routing.\n"
    "2. AuthProvider - Makes authentication state available to all components via React Context.\n"
    "3. App - The root component that defines routes."
)

pdf.sub_title("6.2 Router - App.jsx")
pdf.body_text("Defines the application routes:")
pdf.bullet("/login - Renders the Login page (public)")
pdf.bullet("/register - Renders the Register page (public)")
pdf.bullet("/dashboard - Renders the Dashboard (protected route)")
pdf.bullet("/* (catch-all) - Redirects to /dashboard")
pdf.ln(2)
pdf.body_text(
    "The ProtectedRoute component checks if the user is authenticated. If not, it redirects "
    "to /login. While verifying the token, it shows a loading spinner."
)

pdf.sub_title("6.3 Pages")

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Login.jsx")
pdf.ln(7)
pdf.body_text(
    "A form with email and password fields. On submit, it calls the login() function from "
    "AuthContext, which sends a POST request to /login. On success, the JWT token is stored "
    "in localStorage and the user is redirected to /dashboard. Displays error messages on failure."
)

pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Register.jsx")
pdf.ln(7)
pdf.body_text(
    "A form with full name, email, password, and confirm password fields. Validates that "
    "passwords match and are at least 6 characters. On submit, calls register() from AuthContext "
    "which sends a POST to /register, then automatically logs the user in and redirects to /dashboard."
)

pdf.check_page_break()
pdf.set_font("Helvetica", "B", 10)
pdf.cell(0, 7, "Dashboard.jsx (Main Application View)")
pdf.ln(7)
pdf.body_text(
    "The most complex page. On mount, it fetches data from two endpoints:\n"
    "- GET /plaid/accounts: Retrieves all linked bank accounts with real-time balances.\n"
    "- GET /transactions: Retrieves all transactions (both manual and Plaid-synced).\n\n"
    "It then renders:\n"
    "- Navigation bar with logo and logout button\n"
    "- Summary cards showing total balance, total income, and total spending\n"
    "- Linked accounts section with a BalanceCard for each account\n"
    "- Analytics section with pie chart (spending by category) and bar chart (monthly trend)\n"
    "- Transactions table listing all transactions\n"
    "- Connect Bank button to link new accounts via Plaid"
)

# ============================================================
# 7. FRONTEND COMPONENTS
# ============================================================
pdf.add_page()
pdf.section_title("7. Frontend Components")

pdf.sub_title("7.1 ConnectBankButton.jsx")
pdf.body_text(
    "This is the most complex component. It handles the entire Plaid bank linking flow:\n\n"
    "Step 1: User clicks 'Connect Bank Account' button.\n"
    "Step 2: Component sends POST /plaid/create_link_token to get a Plaid link token.\n"
    "Step 3: The Plaid Link widget opens automatically (a modal where users select their bank).\n"
    "Step 4: User selects a bank and enters their bank credentials.\n"
    "Step 5: Plaid returns a temporary public_token to the frontend.\n"
    "Step 6: Component sends POST /plaid/exchange_token with the public_token.\n"
    "Step 7: Backend exchanges it for a permanent access_token, encrypts it, and stores it.\n"
    "Step 8: Component sends POST /plaid/sync_transactions to pull in transactions.\n"
    "Step 9: Dashboard refreshes via the onSuccess callback.\n\n"
    "Shows loading states: 'Connecting...' and 'Syncing Transactions...' during the process."
)

pdf.check_page_break()
pdf.sub_title("7.2 BalanceCard.jsx")
pdf.body_text(
    "Displays a single linked bank account. Shows:\n"
    "- Institution name and account name\n"
    "- Account type icon (bank, credit card, etc.)\n"
    "- Current balance and available balance\n"
    "- Masked account number (last 4 digits)\n"
    "- Color-coded border by account type (teal for depository, orange for credit, etc.)"
)

pdf.sub_title("7.3 TransactionsTable.jsx")
pdf.body_text(
    "Renders all transactions in a table format with columns:\n"
    "- Date (formatted as MM/DD/YYYY)\n"
    "- Description\n"
    "- Category (displayed as a colored badge, formatted from snake_case to Title Case)\n"
    "- Amount (green text for income, white for expenses)\n"
    "- Source ('Bank' badge for Plaid transactions, 'Manual' badge for manual entries)\n\n"
    "Shows a friendly empty state message when there are no transactions."
)

pdf.check_page_break()
pdf.sub_title("7.4 Charts.jsx")
pdf.body_text(
    "Contains two Recharts visualizations:\n\n"
    "Pie Chart (Spending by Category):\n"
    "- Donut-style chart showing top 8 spending categories\n"
    "- Only includes expenses (negative amounts)\n"
    "- Shows category name and dollar amount in the legend\n\n"
    "Bar Chart (Monthly Spending Trend):\n"
    "- Shows spending over the last 6 months\n"
    "- X-axis: month labels (e.g., 'Jan 26')\n"
    "- Y-axis: dollar amounts\n"
    "- Both charts show 'No spending data' if there are no expenses."
)

pdf.sub_title("7.5 BackgroundLayer.jsx")
pdf.body_text(
    "A purely visual component that renders a fixed animated background behind all pages. "
    "It creates three gradient orbs (purple, teal, blue) with blur effects to achieve the "
    "premium dark-theme aesthetic seen across the application."
)

# ============================================================
# 8. API CLIENT & AUTH STATE
# ============================================================
pdf.add_page()
pdf.section_title("8. API Client & Authentication State")

pdf.sub_title("8.1 Axios Client (api/axios.js)")
pdf.body_text(
    "A configured Axios instance that all API calls go through. Key features:\n\n"
    "Base URL: '/api' - All requests are prefixed with /api. Vite's dev server proxies these "
    "to http://127.0.0.1:5000, stripping the /api prefix.\n\n"
    "Request Interceptor: Before every request, it reads the JWT token from localStorage "
    "and attaches it as an Authorization: Bearer <token> header.\n\n"
    "Response Interceptor: If any response returns HTTP 401 (Unauthorized), it automatically "
    "clears the stored token and redirects the user to /login. This handles expired tokens."
)

pdf.sub_title("8.2 Auth Context (context/AuthContext.jsx)")
pdf.body_text(
    "A React Context provider that manages authentication state globally. Provides:\n\n"
    "- token: The JWT stored in localStorage\n"
    "- isAuthenticated: Boolean flag indicating login status\n"
    "- isLoading: True while verifying token on app startup\n"
    "- login(email, password): Sends POST /login, stores returned token, navigates to /dashboard\n"
    "- register(name, email, password): Sends POST /register, then auto-calls login()\n"
    "- logout(): Clears token from localStorage, navigates to /login\n\n"
    "On initial app load, it checks if a token exists in localStorage and verifies it by "
    "calling GET /protected. If valid, the user stays logged in. If invalid, they're redirected "
    "to login."
)

# ============================================================
# 9. CRITICAL FLOWS
# ============================================================
pdf.add_page()
pdf.section_title("9. Critical Flows")

pdf.sub_title("9.1 Authentication Flow")
pdf.body_text(
    "1. User fills in the Login or Register form.\n"
    "2. Frontend sends POST /login (or POST /register then POST /login).\n"
    "3. Backend verifies credentials using bcrypt hash comparison.\n"
    "4. Backend generates a JWT access token and returns it.\n"
    "5. Frontend stores the token in localStorage.\n"
    "6. AuthContext sets isAuthenticated = true.\n"
    "7. React Router redirects the user to /dashboard.\n"
    "8. Every subsequent API call includes the JWT in the Authorization header (axios interceptor).\n"
    "9. If the token expires, a 401 response triggers auto-logout (axios response interceptor)."
)

pdf.sub_title("9.2 Bank Connection Flow")
pdf.body_text(
    "1. User clicks 'Connect Bank Account' on the Dashboard.\n"
    "2. Frontend sends POST /plaid/create_link_token to get a Plaid link token.\n"
    "3. The Plaid Link widget opens in a modal overlay.\n"
    "4. User selects their bank from the list.\n"
    "5. User enters their bank credentials (in Plaid's secure widget).\n"
    "6. Plaid authenticates and returns a temporary public_token to the frontend.\n"
    "7. Frontend sends POST /plaid/exchange_token with the public_token.\n"
    "8. Backend calls Plaid to exchange the public_token for a permanent access_token.\n"
    "9. Backend encrypts the access_token using Fernet and stores it in plaid_items table.\n"
    "10. Frontend sends POST /plaid/sync_transactions.\n"
    "11. Backend uses cursor-based sync to fetch all transactions from Plaid.\n"
    "12. Transactions are stored in the transactions table with source='plaid'.\n"
    "13. Dashboard refreshes to show the new accounts and transactions."
)

pdf.check_page_break()
pdf.sub_title("9.3 Dashboard Data Loading Flow")
pdf.body_text(
    "1. Dashboard component mounts (user navigates to /dashboard).\n"
    "2. GET /plaid/accounts is called:\n"
    "   - Backend fetches all plaid_items for the user.\n"
    "   - For each item, decrypts the access_token.\n"
    "   - Calls Plaid API to get current account info and balances.\n"
    "   - Returns array of accounts with real-time balance data.\n"
    "3. GET /transactions is called:\n"
    "   - Backend queries SELECT * FROM transactions WHERE user_id = (current user).\n"
    "   - Returns all transactions ordered by date descending.\n"
    "4. Frontend processes the data:\n"
    "   - Calculates total balance (sum of all account balances).\n"
    "   - Calculates total income (sum of positive transaction amounts).\n"
    "   - Calculates total spending (sum of negative transaction amounts).\n"
    "   - Aggregates spending by category for the pie chart.\n"
    "   - Aggregates spending by month for the bar chart.\n"
    "5. All components render with the processed data."
)

# ============================================================
# 10. SECURITY LAYERS
# ============================================================
pdf.add_page()
pdf.section_title("10. Security Layers")

pdf.sub_title("10.1 Password Security")
pdf.body_text(
    "All passwords are hashed using bcrypt with an automatically generated salt before "
    "storage. Plain-text passwords are never stored in the database. During login, the "
    "submitted password is compared against the hash using bcrypt's secure comparison."
)

pdf.sub_title("10.2 JWT Authentication")
pdf.body_text(
    "After login, the server issues a JSON Web Token (JWT). This token is sent with every "
    "API request in the Authorization header. The backend validates the token on every protected "
    "endpoint using Flask-JWT-Extended. Tokens are stateless, meaning the server does not store "
    "session data."
)

pdf.sub_title("10.3 Plaid Token Encryption")
pdf.body_text(
    "Plaid access tokens (which grant access to a user's bank data) are encrypted at rest "
    "using Fernet symmetric encryption from Python's cryptography library. The encryption key "
    "is stored as an environment variable. Tokens are decrypted only when making Plaid API calls."
)

pdf.sub_title("10.4 Database Security")
pdf.body_text(
    "The PostgreSQL connection requires SSL (sslmode=require), ensuring all data in transit "
    "between the backend and database is encrypted."
)

pdf.sub_title("10.5 Frontend Security")
pdf.body_text(
    "The Axios response interceptor detects HTTP 401 responses and automatically clears the "
    "stored token and redirects to login, preventing stale sessions. The Vite proxy ensures "
    "the backend URL is not exposed to the browser in development."
)

# ============================================================
# 11. HOW FRONTEND CONNECTS TO BACKEND
# ============================================================
pdf.add_page()
pdf.section_title("11. How Frontend Connects to Backend")

pdf.sub_title("11.1 The Proxy Setup")
pdf.body_text(
    "During development, the React frontend runs on port 5173 (Vite) and the Flask backend "
    "runs on port 5000. Since they are on different ports, direct requests would be blocked "
    "by the browser's same-origin policy.\n\n"
    "Solution: Vite's dev server is configured with a proxy in vite.config.js:\n"
    "- Any request to /api/* is forwarded to http://127.0.0.1:5000\n"
    "- The /api prefix is stripped before reaching Flask\n"
    "- Example: Frontend calls /api/login -> Vite proxies to http://127.0.0.1:5000/login\n\n"
    "This means the browser thinks it's talking to the same server, avoiding CORS issues."
)

pdf.sub_title("11.2 Complete Request Lifecycle")
pdf.body_text(
    "1. User action triggers an API call (e.g., clicking login button).\n"
    "2. The component calls axios.post('/api/login', data).\n"
    "3. Axios request interceptor adds the JWT token to the header (if logged in).\n"
    "4. Vite dev server receives the request at /api/login.\n"
    "5. Vite strips /api prefix and forwards to http://127.0.0.1:5000/login.\n"
    "6. Flask receives the request, validates JWT (if protected route).\n"
    "7. Flask processes the request (query DB, call Plaid, etc.).\n"
    "8. Flask returns JSON response.\n"
    "9. Axios receives the response.\n"
    "10. If 401 error: axios interceptor clears token and redirects to /login.\n"
    "11. If success: the component updates its state and re-renders."
)

pdf.sub_title("11.3 Endpoint Mapping")
pdf.body_text("How frontend calls map to backend routes:")
w = [80, 60, 50]
pdf.table_row(["Frontend Call", "Backend Route", "Auth Required"], w, bold=True)
pdf.table_row(["POST /api/register", "POST /register", "No"], w)
pdf.table_row(["POST /api/login", "POST /login", "No"], w)
pdf.table_row(["GET /api/protected", "GET /protected", "Yes (JWT)"], w)
pdf.table_row(["GET /api/transactions", "GET /transactions", "Yes (JWT)"], w)
pdf.table_row(["POST /api/transactions", "POST /transactions", "Yes (JWT)"], w)
pdf.table_row(["DELETE /api/transactions/<id>", "DELETE /transactions/<id>", "Yes (JWT)"], w)
pdf.table_row(["POST /api/plaid/create_link_token", "POST /plaid/create_link_token", "Yes (JWT)"], w)
pdf.table_row(["POST /api/plaid/exchange_token", "POST /plaid/exchange_token", "Yes (JWT)"], w)
pdf.table_row(["POST /api/plaid/sync_transactions", "POST /plaid/sync_transactions", "Yes (JWT)"], w)
pdf.table_row(["GET /api/plaid/accounts", "GET /plaid/accounts", "Yes (JWT)"], w)
pdf.table_row(["DELETE /api/plaid/disconnect", "DELETE /plaid/disconnect", "Yes (JWT)"], w)

# ============================================================
# 12. FUTURE FEATURES
# ============================================================
pdf.add_page()
pdf.section_title("12. Future Features (Tables Ready, Not Wired)")

pdf.body_text(
    "The database has four tables that are populated with seed data (via generate_data.py) "
    "but are not yet connected to the frontend UI. These are ready for future development:"
)

pdf.sub_title("12.1 Budget Tracking (budgets table)")
pdf.body_text(
    "Per-category monthly spending limits. Could display as progress bars on the dashboard "
    "showing how much of each budget has been used."
)

pdf.sub_title("12.2 Fraud Detection (fraud_logs table)")
pdf.body_text(
    "Flags suspicious transactions based on rules (e.g., rapid transactions, unusually high "
    "amounts). Could show alerts/notifications on the dashboard when suspicious activity "
    "is detected."
)

pdf.sub_title("12.3 Round-Up Savings (savings table)")
pdf.body_text(
    "Automatically rounds up each transaction to the nearest dollar and tracks the difference "
    "as savings. Could display a savings total and history on the dashboard."
)

pdf.sub_title("12.4 Recurring Payment Analysis (recurring_transactions table)")
pdf.body_text(
    "Detects recurring payments (subscriptions, bills) by analyzing transaction patterns. "
    "Stores merchant name, average amount, frequency, and annual estimate. Could show a "
    "subscriptions overview with total monthly/yearly costs."
)

# ============================================================
# OUTPUT
# ============================================================
output_path = "C:/Users/msi/Desktop/ai-banking/GuideSpend_AI_Documentation.pdf"
pdf.output(output_path)
print(f"PDF generated: {output_path}")
