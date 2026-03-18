"""
GuideSpend AI — Project Overview PDF Generator
Generates a professional, multi-page PDF for group presentation.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, ListFlowable, ListItem, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# ── Colors ──────────────────────────────────────────────────────────
DARK_BG       = HexColor("#0f172a")
TEAL          = HexColor("#14b8a6")
TEAL_DARK     = HexColor("#0d9488")
BLUE          = HexColor("#2563eb")
SLATE_700     = HexColor("#334155")
SLATE_500     = HexColor("#64748b")
SLATE_300     = HexColor("#cbd5e1")
SLATE_100     = HexColor("#f1f5f9")
WHITE         = HexColor("#ffffff")
EMERALD       = HexColor("#10b981")
AMBER         = HexColor("#f59e0b")
ROSE          = HexColor("#f43f5e")
LIGHT_TEAL_BG = HexColor("#f0fdfa")
LIGHT_BLUE_BG = HexColor("#eff6ff")
BORDER_GRAY   = HexColor("#e2e8f0")

# ── Styles ──────────────────────────────────────────────────────────
def make_styles():
    s = {}
    s["title"] = ParagraphStyle("Title", fontName="Helvetica-Bold", fontSize=28,
                                 leading=34, textColor=SLATE_700, alignment=TA_CENTER,
                                 spaceAfter=8)
    s["subtitle"] = ParagraphStyle("Subtitle", fontName="Helvetica", fontSize=14,
                                    leading=18, textColor=SLATE_500, alignment=TA_CENTER,
                                    spaceAfter=4)
    s["date"] = ParagraphStyle("Date", fontName="Helvetica", fontSize=12,
                                leading=16, textColor=TEAL, alignment=TA_CENTER,
                                spaceAfter=20)
    s["h1"] = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=20,
                              leading=26, textColor=TEAL_DARK, spaceBefore=20,
                              spaceAfter=10, borderPadding=(0,0,4,0))
    s["h2"] = ParagraphStyle("H2", fontName="Helvetica-Bold", fontSize=14,
                              leading=18, textColor=SLATE_700, spaceBefore=14,
                              spaceAfter=6)
    s["h3"] = ParagraphStyle("H3", fontName="Helvetica-Bold", fontSize=12,
                              leading=16, textColor=BLUE, spaceBefore=10,
                              spaceAfter=4)
    s["body"] = ParagraphStyle("Body", fontName="Helvetica", fontSize=10,
                                leading=14, textColor=SLATE_700, alignment=TA_JUSTIFY,
                                spaceAfter=6)
    s["body_bold"] = ParagraphStyle("BodyBold", fontName="Helvetica-Bold", fontSize=10,
                                     leading=14, textColor=SLATE_700, spaceAfter=6)
    s["bullet"] = ParagraphStyle("Bullet", fontName="Helvetica", fontSize=10,
                                  leading=14, textColor=SLATE_700, leftIndent=20,
                                  spaceAfter=3)
    s["bullet2"] = ParagraphStyle("Bullet2", fontName="Helvetica", fontSize=9.5,
                                   leading=13, textColor=SLATE_500, leftIndent=40,
                                   spaceAfter=2)
    s["code"] = ParagraphStyle("Code", fontName="Courier", fontSize=9,
                                leading=12, textColor=SLATE_700, leftIndent=20,
                                spaceAfter=4, backColor=SLATE_100)
    s["toc"] = ParagraphStyle("TOC", fontName="Helvetica", fontSize=11,
                               leading=18, textColor=SLATE_700, leftIndent=10,
                               spaceAfter=2)
    s["toc_section"] = ParagraphStyle("TOCSection", fontName="Helvetica-Bold",
                                       fontSize=11, leading=18, textColor=TEAL_DARK,
                                       leftIndent=10, spaceAfter=2)
    s["caption"] = ParagraphStyle("Caption", fontName="Helvetica-Oblique", fontSize=9,
                                   leading=12, textColor=SLATE_500, alignment=TA_CENTER,
                                   spaceAfter=8)
    s["small"] = ParagraphStyle("Small", fontName="Helvetica", fontSize=9,
                                 leading=12, textColor=SLATE_500, spaceAfter=4)
    return s

S = make_styles()

# ── Helpers ─────────────────────────────────────────────────────────
def section_heading(text, number=None):
    """Create a colored section heading with optional number."""
    prefix = f"Section {number}: " if number else ""
    return Paragraph(f"<b>{prefix}{text}</b>", S["h1"])

def sub_heading(text):
    return Paragraph(f"<b>{text}</b>", S["h2"])

def sub_sub_heading(text):
    return Paragraph(f"<b>{text}</b>", S["h3"])

def body(text):
    return Paragraph(text, S["body"])

def body_bold(text):
    return Paragraph(text, S["body_bold"])

def bullet(text, level=1):
    style = S["bullet"] if level == 1 else S["bullet2"]
    return Paragraph(f"\u2022  {text}", style)

def arrow_bullet(text):
    return Paragraph(f"\u2192  {text}", S["bullet"])

def numbered_bullet(num, text):
    return Paragraph(f"<b>{num}.</b>  {text}", S["bullet"])

def spacer(h=6):
    return Spacer(1, h)

def divider():
    """Visual divider line using a thin table."""
    t = Table([[""]], colWidths=[460])
    t.setStyle(TableStyle([
        ("LINEBELOW", (0,0), (-1,-1), 1, BORDER_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    return t

def info_box(title, items, bg=LIGHT_TEAL_BG):
    """Colored info box with title and bullet items."""
    content = [[Paragraph(f"<b>{title}</b>", S["body_bold"])]]
    for item in items:
        content.append([Paragraph(f"\u2022  {item}", S["bullet"])])
    t = Table(content, colWidths=[440])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), bg),
        ("BOX", (0,0), (-1,-1), 0.5, BORDER_GRAY),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("RIGHTPADDING", (0,0), (-1,-1), 12),
    ]))
    return t

def make_table(headers, rows, col_widths=None):
    """Create a styled data table."""
    data = [headers] + rows
    if not col_widths:
        col_widths = [460 // len(headers)] * len(headers)
    t = Table(data, colWidths=col_widths)
    style = [
        ("BACKGROUND", (0,0), (-1,0), TEAL_DARK),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
        ("FONTSIZE", (0,1), (-1,-1), 9),
        ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
        ("TEXTCOLOR", (0,1), (-1,-1), SLATE_700),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER_GRAY),
    ]
    # Alternating row colors
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0,i), (-1,i), SLATE_100))
    t.setStyle(TableStyle(style))
    return t

def step_box(step_num, title, items):
    """A numbered step box."""
    elements = []
    elements.append(Paragraph(f"<b>Step {step_num} - {title}</b>", S["h3"]))
    for item in items:
        elements.append(bullet(item))
    elements.append(spacer(4))
    return elements

# ── Page Templates ──────────────────────────────────────────────────
def on_first_page(canvas, doc):
    canvas.saveState()
    # Top teal bar
    canvas.setFillColor(TEAL_DARK)
    canvas.rect(0, A4[1] - 4, A4[0], 4, fill=1, stroke=0)
    # Bottom bar
    canvas.setFillColor(TEAL_DARK)
    canvas.rect(0, 0, A4[0], 4, fill=1, stroke=0)
    canvas.restoreState()

def on_later_pages(canvas, doc):
    canvas.saveState()
    # Top teal line
    canvas.setFillColor(TEAL_DARK)
    canvas.rect(0, A4[1] - 3, A4[0], 3, fill=1, stroke=0)
    # Footer
    canvas.setFillColor(SLATE_500)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(72, 30, "GuideSpend AI - Project Overview & Architecture")
    canvas.drawRightString(A4[0] - 72, 30, f"Page {doc.page}")
    # Bottom line
    canvas.setFillColor(TEAL_DARK)
    canvas.rect(0, 0, A4[0], 2, fill=1, stroke=0)
    canvas.restoreState()


# ── Build Document ──────────────────────────────────────────────────
def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=50, bottomMargin=50,
        leftMargin=68, rightMargin=68,
    )
    story = []

    # ════════════════════════════════════════════════════
    # TITLE PAGE
    # ════════════════════════════════════════════════════
    story.append(Spacer(1, 120))
    # Teal accent line
    t = Table([[""]], colWidths=[200])
    t.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-1),3,TEAL)]))
    story.append(t)
    story.append(spacer(16))
    story.append(Paragraph("GuideSpend AI", S["title"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Project Overview &amp; Architecture", ParagraphStyle(
        "TitleSub", fontName="Helvetica", fontSize=18, leading=22,
        textColor=SLATE_500, alignment=TA_CENTER, spaceAfter=16)))
    story.append(spacer(8))
    t = Table([[""]], colWidths=[200])
    t.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-1),3,TEAL)]))
    story.append(t)
    story.append(spacer(20))
    story.append(Paragraph("Complete Technical Documentation for Group Presentation", S["subtitle"]))
    story.append(spacer(8))
    story.append(Paragraph("March 5, 2026", S["date"]))
    story.append(Spacer(1, 60))

    story.append(info_box("Tech Stack at a Glance", [
        "<b>Backend:</b> Python Flask + PostgreSQL (Supabase) + Plaid API",
        "<b>Frontend:</b> React 19 + Vite + Tailwind CSS 4.2 + Axios",
        "<b>Auth:</b> JWT (JSON Web Tokens) + bcrypt password hashing",
        "<b>Security:</b> Fernet encryption for banking tokens, SSL connections",
    ]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ════════════════════════════════════════════════════
    story.append(section_heading("Table of Contents"))
    story.append(divider())
    toc_items = [
        ("1", "Project Overview"),
        ("2", "How the Application Works (End-to-End Flow)"),
        ("3", "How Plaid Works in This Project"),
        ("4", "Backend Architecture"),
        ("5", "Frontend Architecture"),
        ("6", "Key Features Developed"),
        ("7", "Database Schema Evolution"),
        ("8", "How to Add AI Chatbot"),
        ("9", "Complete Project File Structure"),
    ]
    for num, title in toc_items:
        story.append(Paragraph(
            f"<b>Section {num}</b> &mdash; {title}", S["toc_section"]))
    story.append(divider())
    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 1: PROJECT OVERVIEW
    # ════════════════════════════════════════════════════
    story.append(section_heading("Project Overview", 1))
    story.append(divider())
    story.append(body(
        "<b>GuideSpend AI</b> is a personal finance management web application that connects "
        "to users' real bank accounts via the <b>Plaid API</b>, automatically fetches and "
        "categorizes transactions, and provides intelligent financial insights including "
        "spending analysis, health scoring, cashflow forecasting, and subscription detection."
    ))
    story.append(spacer(8))
    story.append(sub_heading("What Does It Do?"))
    features = [
        "Connects to real bank accounts securely via Plaid (no bank passwords stored)",
        "Automatically fetches and categorizes transactions from all linked banks",
        "Provides financial insights: spending trends, period comparisons, volatility",
        "Calculates a Financial Health Score (0-100) with actionable advice",
        "Forecasts future cashflow and predicts overdraft risk",
        "Detects recurring subscriptions automatically with confidence scoring",
        "Visualizes spending with pie charts and bar charts",
        "Supports manual transaction entry alongside bank data",
    ]
    for f in features:
        story.append(bullet(f))

    story.append(spacer(8))
    story.append(sub_heading("Tech Stack"))
    story.append(make_table(
        ["Layer", "Technology", "Purpose"],
        [
            ["Backend", "Python Flask 3.1", "REST API server, business logic"],
            ["Database", "PostgreSQL (Supabase)", "Data storage, hosted on AWS"],
            ["Banking API", "Plaid SDK", "Bank account linking, transaction data"],
            ["Frontend", "React 19 + Vite 7", "Single-page app, fast dev builds"],
            ["Styling", "Tailwind CSS 4.2", "Utility-first CSS, dark theme"],
            ["HTTP Client", "Axios", "API calls with JWT interceptors"],
            ["Charts", "Recharts", "Pie and bar chart visualizations"],
            ["Auth", "JWT + bcrypt", "Secure session tokens, password hashing"],
            ["Encryption", "Fernet (AES)", "Banking token encryption at rest"],
        ],
        col_widths=[80, 140, 240]
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 2: HOW THE APP WORKS
    # ════════════════════════════════════════════════════
    story.append(section_heading("How the Application Works", 2))
    story.append(divider())
    story.append(body("This section walks through the complete user journey from signup to seeing financial insights."))
    story.append(spacer(6))

    # Step 1
    for el in step_box(1, "User Registration &amp; Login", [
        "User creates an account with username, email, and password",
        "Password is hashed with <b>bcrypt</b> (never stored in plain text)",
        "On login, server verifies credentials and returns a <b>JWT token</b>",
        "JWT token is stored in browser <b>localStorage</b>",
        "All subsequent API requests include this token in the Authorization header",
        "Token expires after <b>24 hours</b> (auto-logout on expiry)",
    ]):
        story.append(el)

    # Step 2
    for el in step_box(2, "Connecting a Bank Account (Plaid)", [
        'User clicks <b>"Connect Bank Account"</b> button on dashboard',
        "Frontend requests a <b>Link Token</b> from our backend",
        "Our backend calls <b>Plaid API</b> to generate the Link Token",
        "Plaid Link widget opens in the browser (Plaid's own secure UI)",
        "User selects their bank and enters credentials <b>(handled entirely by Plaid)</b>",
        "Plaid returns a temporary <b>public_token</b> to our frontend",
        "Frontend sends public_token to our backend",
        "Backend exchanges public_token for a permanent <b>access_token</b> via Plaid",
        "access_token is <b>encrypted with Fernet</b> and stored in our database",
        "This encrypted token lets us fetch financial data going forward",
    ]):
        story.append(el)

    # Step 3
    for el in step_box(3, "Fetching Transactions", [
        "Backend decrypts the access_token only when making Plaid API calls",
        "Uses Plaid's <b>Transaction Sync API</b> with cursor-based incremental syncing",
        "Only fetches <b>new, modified, or removed</b> transactions (not full history)",
        'Merchant names are cleaned: "NETFLIX PAYMENT VISA 12345" becomes "Netflix"',
        "Transactions stored with <b>ON CONFLICT upsert</b> (idempotent, safe to re-run)",
        "Background job can auto-sync <b>hourly</b> for all users",
    ]):
        story.append(el)

    # Step 4
    for el in step_box(4, "Dashboard Display", [
        "Dashboard shows: <b>total balance, income, spending</b> across all linked accounts",
        'Account filter dropdown: view per-account or "All Accounts"',
        "Paginated transaction table with <b>category badges</b> and source indicators",
        "Linked account cards with <b>real-time balances</b> from Plaid",
        "Financial insights, health score, cashflow forecast, subscriptions",
        "Analytics charts: spending by category (pie) and monthly trends (bar)",
    ]):
        story.append(el)

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 3: HOW PLAID WORKS
    # ════════════════════════════════════════════════════
    story.append(section_heading("How Plaid Works in This Project", 3))
    story.append(divider())

    story.append(sub_heading("What is Plaid?"))
    story.append(body(
        "<b>Plaid</b> is a financial technology company that acts as a secure middleman between "
        "our app and banks. We <b>never</b> handle bank credentials directly - Plaid does. "
        "Plaid is used by major apps like Venmo, Cash App, and Robinhood."
    ))

    story.append(spacer(8))
    story.append(sub_heading("Our 5 Plaid Integration Points"))
    story.append(make_table(
        ["#", "Endpoint", "What It Does"],
        [
            ["1", "POST /plaid/create_link_token", "Gets a token for Plaid's secure bank login widget"],
            ["2", "POST /plaid/exchange_token", "Swaps temporary public_token for permanent access_token"],
            ["3", "GET /plaid/accounts", "Fetches real-time balances for all linked accounts"],
            ["4", "POST /plaid/sync_transactions", "Incremental fetch of new/modified/removed transactions"],
            ["5", "DELETE /plaid/disconnect/<item_id>", "Revokes access token and cleans up all data"],
        ],
        col_widths=[20, 185, 255]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Plaid Data Flow"))
    story.append(body("<b>Connecting a bank:</b>"))
    story.append(Paragraph(
        "User Browser \u2192 Plaid Link Widget \u2192 Plaid Servers \u2192 public_token \u2192 "
        "Our Backend \u2192 exchange for access_token \u2192 Encrypt \u2192 Store in PostgreSQL",
        S["code"]))
    story.append(spacer(4))
    story.append(body("<b>Fetching transactions:</b>"))
    story.append(Paragraph(
        "Our Backend \u2192 Decrypt access_token \u2192 Plaid Sync API \u2192 "
        "Transaction Data \u2192 Normalize merchant names \u2192 Upsert to PostgreSQL",
        S["code"]))

    story.append(spacer(10))
    story.append(sub_heading("Security Measures"))
    story.append(info_box("How We Protect Banking Data", [
        "Access tokens <b>encrypted at rest</b> with Fernet symmetric encryption (AES-128-CBC)",
        "Tokens <b>only decrypted in memory</b> when making Plaid API calls",
        "<b>Ownership verification</b> on all operations (user can only access their own data)",
        "Currently using Plaid <b>Sandbox</b> environment (test mode with fake bank data)",
        "SSL/TLS encryption for all database connections",
    ]))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 4: BACKEND ARCHITECTURE
    # ════════════════════════════════════════════════════
    story.append(section_heading("Backend Architecture", 4))
    story.append(divider())

    story.append(sub_heading("Architecture Pattern: MVC with Service Layer"))
    story.append(make_table(
        ["Layer", "Folder", "Responsibility"],
        [
            ["Routes (Controllers)", "backend/routes/", "Handle HTTP requests, parse params, return JSON"],
            ["Services", "backend/services/", "Business logic, computations, orchestration"],
            ["Models", "backend/models/", "Pure database access (SQL only, no business logic)"],
            ["Utils", "backend/utils/", "Cross-cutting: logging, encryption, errors, DB pool"],
        ],
        col_widths=[120, 110, 230]
    ))
    story.append(spacer(6))
    story.append(body(
        "The app uses Flask's <b>Application Factory</b> pattern. The <b>create_app()</b> function "
        "initializes Flask, loads config, sets up JWT, database pool, encryption, Plaid client, "
        "registers all route blueprints, and error handlers."
    ))

    story.append(spacer(10))
    story.append(sub_heading("All API Endpoints"))
    story.append(sub_sub_heading("Auth Routes (/auth)"))
    story.append(make_table(
        ["Method", "Endpoint", "Description"],
        [
            ["POST", "/auth/register", "Create new user account"],
            ["POST", "/auth/login", "Authenticate and get JWT token"],
            ["GET", "/auth/protected", "Verify token validity (health check)"],
        ],
        col_widths=[50, 150, 260]
    ))
    story.append(spacer(6))

    story.append(sub_sub_heading("Plaid Routes (/plaid)"))
    story.append(make_table(
        ["Method", "Endpoint", "Description"],
        [
            ["POST", "/plaid/create_link_token", "Get Plaid widget token"],
            ["POST", "/plaid/exchange_token", "Exchange public token for access token"],
            ["GET", "/plaid/accounts", "List linked accounts with live balances"],
            ["POST", "/plaid/sync_transactions", "Fetch new/modified/removed transactions"],
            ["DELETE", "/plaid/disconnect/<item_id>", "Remove bank connection + cleanup"],
        ],
        col_widths=[50, 185, 225]
    ))
    story.append(spacer(6))

    story.append(sub_sub_heading("Transaction Routes (/transactions)"))
    story.append(make_table(
        ["Method", "Endpoint", "Description"],
        [
            ["POST", "/transactions", "Create manual transaction"],
            ["GET", "/transactions", "List transactions (paginated, filterable by account)"],
            ["DELETE", "/transactions/<id>", "Delete a transaction (with ownership check)"],
        ],
        col_widths=[50, 165, 245]
    ))
    story.append(spacer(6))

    story.append(sub_sub_heading("Analytics Routes"))
    story.append(make_table(
        ["Method", "Endpoint", "Description"],
        [
            ["GET", "/v1/insights/time-range", "Unified insights (week/month/rolling/custom)"],
            ["GET", "/v1/insights/weekly/latest", "Legacy weekly report"],
            ["GET", "/v1/cashflow/forecast", "Balance projection (7/14/30 days)"],
            ["GET", "/v1/health-score", "Financial health score (0-100)"],
            ["GET", "/v1/subscriptions", "List detected recurring payments"],
            ["POST", "/v1/subscriptions/recompute", "Trigger subscription detection"],
        ],
        col_widths=[50, 175, 235]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Database Tables"))
    story.append(make_table(
        ["Table", "Purpose", "Key Fields"],
        [
            ["users", "User accounts", "id, username, email, password_hash"],
            ["plaid_items", "Encrypted bank connections", "access_token, item_id, institution_name, cursor"],
            ["transactions", "All transactions (manual + bank)", "amount, category, date, plaid_account_id, source"],
            ["time_range_reports", "Cached financial insights", "start_date, end_date, total_spent, volatility_score"],
            ["weekly_reports", "Legacy weekly analytics", "week_start, week_end, top_merchants (JSON)"],
            ["recurring_merchants", "Detected subscriptions", "merchant_key, cadence, confidence_score, next_expected"],
            ["cashflow_forecasts", "Balance projections", "horizon_days, risk_score, projected_daily_balances (JSON)"],
            ["health_scores", "Financial wellness metrics", "health_score (0-100), component_scores (JSON)"],
        ],
        col_widths=[110, 145, 205]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Background Jobs"))
    story.append(make_table(
        ["Job", "Schedule", "What It Does"],
        [
            ["sync_transactions", "Every hour", "Incremental transaction sync for all users"],
            ["weekly_jobs", "Monday 2:00 AM", "Generate weekly financial reports"],
            ["subscription_jobs", "Daily 3:00 AM", "Detect recurring payments for all users"],
            ["cashflow_jobs", "Daily 4:00 AM", "Pre-compute cashflow forecasts"],
        ],
        col_widths=[120, 100, 240]
    ))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 5: FRONTEND ARCHITECTURE
    # ════════════════════════════════════════════════════
    story.append(section_heading("Frontend Architecture", 5))
    story.append(divider())

    story.append(sub_heading("Component Hierarchy"))
    story.append(Paragraph(
        "main.jsx \u2192 BrowserRouter \u2192 AuthProvider \u2192 AccountProvider \u2192 App",
        S["code"]))
    story.append(Paragraph(
        "App \u2192 Routes: /login, /register, /dashboard (ProtectedRoute)",
        S["code"]))
    story.append(spacer(8))

    story.append(sub_heading("Dashboard Components"))
    story.append(body("The Dashboard.jsx orchestrates all components:"))
    story.append(make_table(
        ["Component", "What It Displays"],
        [
            ["ConnectBankButton", "Plaid Link widget integration for bank connection"],
            ["BalanceCard", "Per-account balance card with type icon and disconnect option"],
            ["InsightsCard", "Multi-mode financial insights (week/month/rolling/custom) with nav"],
            ["HealthScoreCard", "Circular gauge (0-100) with component scores and explanations"],
            ["SubscriptionsCard", "Detected recurring payments with confidence scores"],
            ["CashflowCard", "Balance projection sparkline chart with risk assessment"],
            ["TransactionsTable", "Paginated transaction list with category badges"],
            ["Charts", "Pie chart (by category) + Bar chart (monthly trends)"],
        ],
        col_widths=[130, 330]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Custom Hooks (Data Fetching)"))
    story.append(body(
        "All hooks follow a consistent pattern: return <b>{ data, loading, error, refresh }</b> "
        "and use <b>requestIdRef</b> for race-condition protection."
    ))
    story.append(make_table(
        ["Hook", "Purpose", "Extra Controls"],
        [
            ["useAccounts", "Fetch linked accounts with balances", "validAccounts filter"],
            ["useTransactions", "Paginated transaction fetching", "nextPage, prevPage, goToPage"],
            ["useTimeRangeInsights", "Multi-mode financial insights", "mode, offset, rollingDays, customRange"],
            ["useSubscriptions", "Subscription data", "recompute() trigger"],
            ["useCashflowForecast", "Balance projections", "horizonDays selector (7/14/30)"],
            ["useHealthScore", "Health score metrics", "windowDays selector (30/60/90)"],
        ],
        col_widths=[120, 160, 180]
    ))

    story.append(spacer(10))
    story.append(sub_heading("State Management"))
    story.append(body("No Redux or Zustand. Uses React built-in tools:"))
    story.append(bullet("<b>AuthContext</b> - JWT token, login/logout/register methods"))
    story.append(bullet("<b>AccountContext</b> - Selected account filter (persisted to localStorage)"))
    story.append(bullet("<b>useState + useCallback</b> - Component-level state in hooks"))
    story.append(bullet("<b>useRef</b> - Race-condition protection (requestIdRef)"))
    story.append(bullet("<b>localStorage</b> - Persistence for token, mode, account filter"))

    story.append(spacer(10))
    story.append(sub_heading("API Client Architecture"))
    story.append(bullet("Central <b>Axios instance</b> (apiClient.js) with base URL config"))
    story.append(bullet("<b>Request interceptor:</b> Auto-attaches JWT from localStorage"))
    story.append(bullet("<b>Response interceptor:</b> 401 = clear token + redirect to login"))
    story.append(bullet("<b>7 API modules:</b> auth, plaid, transactions, insights, subscriptions, cashflow, healthScore"))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 6: KEY FEATURES DEVELOPED
    # ════════════════════════════════════════════════════
    story.append(section_heading("Key Features Developed", 6))
    story.append(divider())

    features = [
        ("1. User Authentication System", [
            "Secure registration with <b>bcrypt</b> password hashing",
            "JWT-based session management (24-hour expiry)",
            "Auto-logout on token expiration via Axios interceptor",
            "Protected routes on frontend (redirect to login if not authenticated)",
        ]),
        ("2. Multi-Bank Account Linking", [
            "Connect <b>multiple banks</b> via Plaid Link widget",
            "Per-account balance display with <b>real-time data</b> from Plaid",
            "Account disconnect with <b>confirmation modal</b> and full cleanup",
            "Per-account filtering across all dashboard views",
        ]),
        ("3. Transaction Management", [
            "<b>Automatic sync</b> from linked banks (cursor-based incremental)",
            "Manual transaction entry for cash/other payments",
            "Smart <b>merchant name normalization</b> (removes noise like card numbers)",
            "Paginated display with color-coded <b>category badges</b>",
            "Source tracking: <b>Bank</b> vs <b>Manual</b> indicator",
        ]),
        ("4. Time-Range Financial Insights Engine", [
            "<b>4 analysis modes:</b> Week, Month, Rolling (7/30/90 days), Custom date range",
            "Period navigation with arrows and <b>Today button</b>",
            "Metrics: total spent, income, net change, period change %, volatility score",
            "Top 5 merchants and categories by spend amount",
            "Human-readable <b>explanation text</b> for each report",
            "Cached with <b>idempotent upsert</b> (ON CONFLICT pattern)",
        ]),
        ("5. Financial Health Score (0-100)", [
            "<b>4 weighted components:</b> Savings Rate (30%), Spending Stability (20%), Subscription Load (20%), Cash Buffer (30%)",
            "Color-coded circular gauge: Green (70+), Amber (40-69), Red (&lt;40)",
            "Explanations with <b>strengths, risks, and actionable suggestions</b>",
            "Configurable analysis window: 30, 60, or 90 days",
        ]),
        ("6. Cashflow Forecasting", [
            "<b>Deterministic</b> daily balance projection (7/14/30 day horizons)",
            "Factors: daily spending avg, income avg, volatility, upcoming subscriptions",
            "Risk score (0-100) with <b>overdraft prediction</b>",
            "Visual sparkline chart showing projected daily balances",
        ]),
        ("7. Subscription/Recurring Payment Detection", [
            "<b>Deterministic heuristic</b> (not ML): analyzes 180 days of expenses",
            "Groups by normalized merchant, matches cadence patterns",
            "Supports: weekly, biweekly, monthly, quarterly cadences",
            "Confidence scoring: cadence fit (40%), sample size (25%), amount stability (25%), bonus (10%)",
            "Predicts <b>next expected charge date</b> for each subscription",
        ]),
        ("8. Analytics Visualizations", [
            "<b>Donut pie chart</b> for spending by category (top 8)",
            "<b>Bar chart</b> for monthly spending trends (last 6 months)",
            "Built with <b>Recharts</b> library with custom tooltips",
        ]),
    ]

    for title, items in features:
        story.append(sub_heading(title))
        for item in items:
            story.append(bullet(item))
        story.append(spacer(4))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 7: DATABASE SCHEMA EVOLUTION
    # ════════════════════════════════════════════════════
    story.append(section_heading("Database Schema Evolution", 7))
    story.append(divider())
    story.append(body("The database evolved through <b>7 migrations</b>, tracking the expansion from basic transactions to advanced analytics:"))
    story.append(spacer(6))

    story.append(make_table(
        ["#", "Migration", "What It Added"],
        [
            ["1", "Multi-account support", "plaid_account_id, institution_name, account_name columns"],
            ["2", "Weekly reports", "weekly_reports table with JSONB columns"],
            ["3", "Time-range reports", "Flexible date windows (week/month/rolling/custom)"],
            ["4", "Period change fix", "Ensured period_change column exists (idempotent)"],
            ["5", "Recurring merchants", "Subscription detection with confidence scoring"],
            ["6", "Cashflow forecasts", "Daily balance projections with risk assessment"],
            ["7", "Health scores", "Composite financial wellness metrics (0-100)"],
        ],
        col_widths=[20, 130, 310]
    ))

    story.append(spacer(12))
    story.append(sub_heading("Tables Ready in DB but Not Yet Wired to UI"))
    story.append(info_box("Future Feature Database Tables", [
        "<b>budgets</b> - Per-category spending limits with progress tracking",
        "<b>fraud_logs</b> - Suspicious transaction flags and alerts",
        "<b>savings</b> - Round-up savings accumulation tracking",
    ], bg=LIGHT_BLUE_BG))

    story.append(spacer(12))
    story.append(sub_heading("Key Database Design Patterns"))
    story.append(bullet("<b>Idempotent Upserts:</b> All tables use UNIQUE constraints + ON CONFLICT for safe re-runs"))
    story.append(bullet("<b>JSONB Flexibility:</b> Top merchants, categories, explanations stored as flexible JSON"))
    story.append(bullet("<b>Composite Indexing:</b> transactions(user_id, date) for fast aggregation"))
    story.append(bullet("<b>Sentinel Values:</b> account_id defaults to 'all' (not NULL) for UNIQUE constraints"))
    story.append(bullet("<b>Cascade Deletion:</b> Foreign keys use ON DELETE CASCADE for data integrity"))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 8: HOW TO ADD AI CHATBOT
    # ════════════════════════════════════════════════════
    story.append(section_heading("How to Add AI Chatbot", 8))
    story.append(divider())

    story.append(body(
        "Integrate an <b>AI chatbot</b> using the <b>Anthropic Claude API</b> that can answer "
        "users' financial questions using their actual transaction data. This is the natural next "
        "step to make GuideSpend AI truly intelligent."
    ))

    story.append(spacer(10))
    story.append(sub_heading("Architecture for AI Chatbot"))
    story.append(sub_sub_heading("New Backend Components"))
    story.append(bullet("<b>backend/services/chatbot_service.py</b> - Orchestrates AI conversations"))
    story.append(bullet("<b>backend/routes/chatbot.py</b> - API endpoints for chat (POST /v1/chat)"))
    story.append(bullet("<b>New DB table:</b> chat_history (user_id, message, role, timestamp)"))

    story.append(spacer(10))
    story.append(sub_heading("How the AI Chatbot Would Work"))
    for el in step_box(1, "User Asks a Question", [
        'User types in chat widget: "How much did I spend on food this month?"',
    ]):
        story.append(el)
    for el in step_box(2, "Frontend Sends to Backend", [
        "Frontend sends message to <b>POST /v1/chat</b> endpoint with JWT auth",
    ]):
        story.append(el)
    for el in step_box(3, "Backend Builds Context", [
        "Fetches user's relevant data: transactions, insights, health score, subscriptions",
        "Constructs a <b>system prompt</b> with the user's financial context",
        "Sends the question + context to <b>Claude API</b> (Anthropic)",
    ]):
        story.append(el)
    for el in step_box(4, "AI Response Displayed", [
        "Claude returns a natural language response based on real financial data",
        "Frontend displays the response in the chat widget",
        "Conversation history saved to <b>chat_history</b> table",
    ]):
        story.append(el)

    story.append(spacer(6))
    story.append(sub_heading("Example System Prompt"))
    story.append(Paragraph(
        '"You are a helpful financial advisor for GuideSpend AI. The user has: '
        'Total spending this month: $2,450. Top categories: Food ($680), '
        'Transportation ($340). Health score: 72/100. '
        'Answer financial questions based on this data. Be concise."',
        S["code"]))

    story.append(spacer(10))
    story.append(sub_heading("Potential AI Features"))
    story.append(make_table(
        ["Feature", "Description"],
        [
            ["Ask About Finances", "Natural language queries about spending patterns"],
            ["Smart Alerts", "AI-generated warnings about unusual spending"],
            ["Budget Recommendations", "AI suggests category budgets based on history"],
            ["Savings Tips", "Personalized suggestions based on spending patterns"],
            ["Bill Negotiation Tips", "Identifies subscriptions that could be reduced"],
            ["Monthly Summary", "AI-written narrative of the month's finances"],
            ["Anomaly Detection", "AI flags unusual or suspicious transactions"],
        ],
        col_widths=[140, 320]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Implementation Steps"))
    impl_steps = [
        ("Install SDK", "pip install anthropic (Python SDK for Claude API)"),
        ("Add API Key", "Add ANTHROPIC_API_KEY to backend/.env"),
        ("Create Service", "chatbot_service.py with context building + API calls"),
        ("Create Routes", "POST /v1/chat and GET /v1/chat/history endpoints"),
        ("Create DB Table", "chat_history table for conversation persistence"),
        ("Build Frontend", "ChatWidget.jsx component with message bubbles"),
        ("Add Hook", "useChatbot hook + chatApi.js API module"),
        ("Integrate", "Add ChatWidget to Dashboard.jsx"),
    ]
    rows = [[str(i+1), s, d] for i, (s, d) in enumerate(impl_steps)]
    story.append(make_table(
        ["Step", "Action", "Details"],
        rows,
        col_widths=[30, 100, 330]
    ))

    story.append(spacer(10))
    story.append(sub_heading("Tech Stack for AI"))
    story.append(info_box("AI Integration Tech", [
        "<b>Anthropic Claude API</b> (claude-sonnet-4-6 for speed, claude-opus-4-6 for depth)",
        "<b>Python anthropic SDK</b> on backend for API calls",
        "<b>React chat widget</b> component on frontend",
        "<b>WebSocket or polling</b> for real-time chat experience",
    ], bg=LIGHT_BLUE_BG))

    story.append(PageBreak())

    # ════════════════════════════════════════════════════
    # SECTION 9: PROJECT FILE STRUCTURE
    # ════════════════════════════════════════════════════
    story.append(section_heading("Complete Project File Structure", 9))
    story.append(divider())

    story.append(sub_heading("Backend (backend/)"))
    backend_files = [
        ["app.py", "App factory - creates and configures the Flask application"],
        ["config.py", "Environment-based configuration (DB, JWT, Plaid, pagination)"],
        ["extensions.py", "JWT manager + Plaid client singleton initialization"],
        ["models/user.py", "User CRUD (create, find by email/id)"],
        ["models/plaid_item.py", "Bank connection management (upsert, cursor, tokens)"],
        ["models/transaction.py", "Transaction CRUD + pagination + plaid upserts"],
        ["models/time_range_report.py", "Aggregation queries (5 SQL queries, 1 connection)"],
        ["models/weekly_report.py", "Legacy weekly report queries"],
        ["models/health_score.py", "Health metric data queries"],
        ["models/cashflow_forecast.py", "Forecast data queries"],
        ["models/recurring_merchant.py", "Subscription data queries"],
        ["routes/auth.py", "/auth endpoints (register, login, protected)"],
        ["routes/plaid.py", "/plaid endpoints (link, exchange, accounts, sync, disconnect)"],
        ["routes/transactions.py", "/transactions endpoints (CRUD)"],
        ["routes/insights.py", "/v1/insights endpoints (time-range, weekly)"],
        ["routes/cashflow.py", "/v1/cashflow endpoints (forecast)"],
        ["routes/health_score.py", "/v1/health-score endpoint"],
        ["routes/subscriptions.py", "/v1/subscriptions endpoints (list, detail, recompute)"],
        ["services/auth_service.py", "Registration + authentication logic (bcrypt, JWT)"],
        ["services/plaid_service.py", "Plaid API orchestration (link, exchange, sync, disconnect)"],
        ["services/transaction_service.py", "Transaction business logic + pagination"],
        ["services/insights_service.py", "Date resolution + analytics engine + caching"],
        ["services/cashflow_service.py", "Balance projection algorithm + risk scoring"],
        ["services/health_score_service.py", "Composite health scoring (4 components, 0-100)"],
        ["services/subscription_service.py", "Recurring payment detection (heuristic)"],
        ["utils/db.py", "PostgreSQL connection pool (ThreadedConnectionPool)"],
        ["utils/encryption.py", "Fernet encrypt/decrypt for Plaid tokens"],
        ["utils/errors.py", "Custom exception hierarchy (ValidationError, etc.)"],
        ["utils/logger.py", "Structured JSON logging with context injection"],
        ["utils/merchant_normalization.py", "Merchant name cleanup (remove noise tokens)"],
        ["jobs/sync_transactions.py", "Hourly: Incremental transaction sync for all users"],
        ["jobs/weekly_jobs.py", "Weekly: Generate financial reports for all users"],
        ["jobs/subscription_jobs.py", "Daily: Detect recurring payments for all users"],
        ["jobs/cashflow_jobs.py", "Daily: Pre-compute cashflow forecasts"],
    ]
    story.append(make_table(
        ["File", "Purpose"],
        backend_files,
        col_widths=[175, 285]
    ))

    story.append(spacer(12))
    story.append(sub_heading("Frontend (frontend/src/)"))
    frontend_files = [
        ["main.jsx", "App bootstrap + provider tree (Router, Auth, Account)"],
        ["App.jsx", "Routing config + ProtectedRoute wrapper"],
        ["api/apiClient.js", "Axios instance + JWT interceptors"],
        ["api/authApi.js", "Auth API calls (register, login, verify)"],
        ["api/plaidApi.js", "Plaid API calls (link, exchange, sync, accounts, disconnect)"],
        ["api/transactionApi.js", "Transaction API calls (CRUD, pagination)"],
        ["api/insightsApi.js", "Insights API calls (time-range, weekly)"],
        ["api/cashflowApi.js", "Cashflow forecast API calls"],
        ["api/healthScoreApi.js", "Health score API calls"],
        ["api/subscriptionsApi.js", "Subscription API calls (list, detail, recompute)"],
        ["context/AuthContext.jsx", "JWT token state + login/logout/register methods"],
        ["context/AccountContext.jsx", "Account filter state (persisted to localStorage)"],
        ["hooks/useAccounts.js", "Account data fetching with validAccounts filter"],
        ["hooks/useTransactions.js", "Paginated transaction fetching with nav controls"],
        ["hooks/useTimeRangeInsights.js", "Multi-mode insights with navigation"],
        ["hooks/useSubscriptions.js", "Subscription data + recompute trigger"],
        ["hooks/useCashflowForecast.js", "Cashflow projections with horizon selector"],
        ["hooks/useHealthScore.js", "Health score with window selector (30/60/90)"],
        ["components/ConnectBankButton.jsx", "Plaid Link widget integration"],
        ["components/BalanceCard.jsx", "Per-account balance card with disconnect"],
        ["components/InsightsCard.jsx", "Multi-mode financial insights display"],
        ["components/HealthScoreCard.jsx", "Circular health gauge + explanations"],
        ["components/SubscriptionsCard.jsx", "Recurring payments list"],
        ["components/CashflowCard.jsx", "Balance projection sparkline"],
        ["components/TransactionsTable.jsx", "Paginated transaction table"],
        ["components/Charts.jsx", "Pie chart + bar chart (Recharts)"],
        ["pages/Login.jsx", "Login form with error handling"],
        ["pages/Register.jsx", "Registration form with validation"],
        ["pages/Dashboard.jsx", "Main app hub - orchestrates all components"],
    ]
    story.append(make_table(
        ["File", "Purpose"],
        frontend_files,
        col_widths=[185, 275]
    ))

    # ── Build ───────────────────────────────────────────
    doc.build(story, onFirstPage=on_first_page, onLaterPages=on_later_pages)
    print(f"PDF created: {output_path}")


if __name__ == "__main__":
    output = r"C:\Users\msi\Desktop\ai-banking\GuideSpend_AI_Project_Overview.pdf"
    build_pdf(output)
