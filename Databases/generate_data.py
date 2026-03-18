# ============================================================
# AI-Powered Financial Management Platform
# Simulated Data Generator
# ============================================================
# HOW TO RUN:
#   python generate_data.py
#
# This will create these CSV files in the same folder:
#   users.csv, transactions.csv, budgets.csv,
#   fraud_logs.csv, savings.csv, recurring_transactions.csv
#
# To load into PostgreSQL, run:
#   python generate_data.py --load
# (make sure to update DB_CONFIG below with your credentials)
# ============================================================

import csv
import random
import hashlib
import argparse
from datetime import date, timedelta, datetime
from decimal import Decimal, ROUND_UP

# ============================================================
# CONFIG — change these to match your PostgreSQL credentials
# ============================================================
DB_CONFIG = {
    "host":     "localhost",
    "port":     5433,
    "database": "financial_platform",
    "user":     "postgres",
    "password": "*******"   # <-- update this
}

NUM_USERS        = 50
TRANSACTIONS_PER_USER = 50

# ============================================================
# SEED DATA
# ============================================================
FIRST_NAMES = ["Alice","Bob","Carol","David","Emma","Frank","Grace","Henry",
               "Isla","James","Karen","Liam","Mia","Noah","Olivia","Peter",
               "Quinn","Rachel","Sam","Tina"]
LAST_NAMES  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
               "Davis","Wilson","Taylor","Anderson","Thomas","Jackson","White",
               "Harris","Martin","Thompson","Young","Lewis","Walker"]
DOMAINS     = ["gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com"]

CATEGORIES  = ["Food & Dining","Shopping","Transport","Entertainment",
               "Health","Utilities","Rent","Subscriptions","Travel","Education"]

MERCHANTS   = {
    "Subscriptions": ["Netflix","Spotify","Amazon Prime","Disney+","YouTube Premium","Apple Music"],
    "Food & Dining": ["McDonald's","Starbucks","Pizza Hut","Subway","Dunkin","Chipotle"],
    "Shopping":      ["Amazon","Walmart","Target","Best Buy","IKEA","Zara"],
    "Transport":     ["Uber","Lyft","Shell Gas","BP Gas","Chevron","Metro Card"],
    "Entertainment": ["AMC Theaters","Steam","PlayStation Store","Xbox Game Pass","Ticketmaster"],
    "Health":        ["CVS Pharmacy","Walgreens","GoodRx","Planet Fitness","Vitamin Shoppe"],
    "Utilities":     ["AT&T","Verizon","Comcast","Duke Energy","Water Dept","Gas Company"],
    "Rent":          ["Apartment Complex","Property Management","Landlord LLC"],
    "Travel":        ["Delta Airlines","Marriott Hotels","Airbnb","Expedia","Enterprise Car"],
    "Education":     ["Udemy","Coursera","Chegg","Khan Academy","College Tuition"]
}

FRAUD_RULES = [
    "rapid_transaction",    # multiple transactions within minutes
    "high_value_amount",    # single transaction over $1000
    "unusual_location",     # different category spike
]

# ============================================================
# HELPERS
# ============================================================
def fake_password_hash(username):
    return hashlib.sha256(f"{username}password123".encode()).hexdigest()

def random_date(start_days_ago=365, end_days_ago=0):
    start = date.today() - timedelta(days=start_days_ago)
    end   = date.today() - timedelta(days=end_days_ago)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def round_up_to_dollar(amount):
    """Calculate round-up savings: difference between amount and next dollar"""
    next_dollar = float(int(amount) + 1)
    return round(next_dollar - float(amount), 2)

# ============================================================
# GENERATORS
# ============================================================
def generate_users(n):
    users = []
    used_emails = set()
    for i in range(1, n + 1):
        first = FIRST_NAMES[(i - 1) % len(FIRST_NAMES)]
        last  = LAST_NAMES[(i - 1) % len(LAST_NAMES)]
        username = f"{first.lower()}{last.lower()}{i}"
        email    = f"{username}@{random.choice(DOMAINS)}"
        while email in used_emails:
            email = f"{username}{random.randint(1,99)}@{random.choice(DOMAINS)}"
        used_emails.add(email)
        users.append({
            "id":            i,
            "username":      username,
            "email":         email,
            "password_hash": fake_password_hash(username),
            "created_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    return users


def generate_transactions(users):
    transactions = []
    tx_id = 1
    for user in users:
        uid = user["id"]
        for _ in range(TRANSACTIONS_PER_USER):
            category = random.choice(CATEGORIES)
            merchant = random.choice(MERCHANTS.get(category, ["General Store"]))

            # Normal amount range per category
            if category == "Rent":
                amount = round(random.uniform(800, 2500), 2)
            elif category == "Travel":
                amount = round(random.uniform(100, 1500), 2)
            elif category == "Utilities":
                amount = round(random.uniform(50, 300), 2)
            else:
                amount = round(random.uniform(5, 250), 2)

            transactions.append({
                "id":          tx_id,
                "user_id":     uid,
                "amount":      amount,
                "category":    category,
                "description": f"{merchant} purchase",
                "date":        random_date().strftime("%Y-%m-%d"),
                "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            tx_id += 1

        # --- FRAUD TRIGGER 1: Rapid transactions (3 transactions same day, small gap)
        fraud_date = random_date(30, 1).strftime("%Y-%m-%d")
        for _ in range(3):
            transactions.append({
                "id":          tx_id,
                "user_id":     uid,
                "amount":      round(random.uniform(10, 80), 2),
                "category":    "Shopping",
                "description": "Rapid purchase - Amazon",
                "date":        fraud_date,
                "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            tx_id += 1

        # --- FRAUD TRIGGER 2: High-value transaction
        transactions.append({
            "id":          tx_id,
            "user_id":     uid,
            "amount":      round(random.uniform(1500, 5000), 2),
            "category":    "Shopping",
            "description": "High value - Best Buy",
            "date":        random_date(30, 1).strftime("%Y-%m-%d"),
            "created_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        tx_id += 1

    return transactions


def generate_budgets(users):
    budgets = []
    budget_id = 1
    for user in users:
        # Give each user budgets for 4 random categories this month
        chosen = random.sample(CATEGORIES, 4)
        for cat in chosen:
            budgets.append({
                "id":           budget_id,
                "user_id":      user["id"],
                "category":     cat,
                "limit_amount": round(random.uniform(100, 1000), 2),
                "month":        date.today().month,
                "year":         date.today().year,
                "created_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            budget_id += 1
    return budgets


def generate_fraud_logs(users, transactions):
    fraud_logs = []
    log_id = 1
    tx_by_user = {}
    for tx in transactions:
        tx_by_user.setdefault(tx["user_id"], []).append(tx)

    for user in users:
        user_txs = tx_by_user.get(user["id"], [])

        # Flag high-value transactions
        high_value = [t for t in user_txs if float(t["amount"]) > 1000]
        for tx in high_value:
            fraud_logs.append({
                "id":             log_id,
                "user_id":        user["id"],
                "transaction_id": tx["id"],
                "rule_triggered": "high_value_amount",
                "flagged_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            log_id += 1

        # Flag rapid transactions (same date, description contains "Rapid")
        rapid = [t for t in user_txs if "Rapid" in t["description"]]
        for tx in rapid:
            fraud_logs.append({
                "id":             log_id,
                "user_id":        user["id"],
                "transaction_id": tx["id"],
                "rule_triggered": "rapid_transaction",
                "flagged_at":     datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            log_id += 1

    return fraud_logs


def generate_savings(users, transactions):
    savings = []
    saving_id = 1
    # Round up every non-whole-dollar transaction under $100
    eligible = [t for t in transactions if float(t["amount"]) < 100
                and float(t["amount"]) % 1 != 0]
    # Take a sample so not every transaction gets a round-up
    sampled = random.sample(eligible, min(len(eligible), len(eligible) // 2))
    for tx in sampled:
        rounded = round_up_to_dollar(float(tx["amount"]))
        if rounded > 0:
            savings.append({
                "id":                    saving_id,
                "user_id":               tx["user_id"],
                "source_transaction_id": tx["id"],
                "rounded_amount":        rounded,
                "saved_at":              datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            saving_id += 1
    return savings


def generate_recurring(users):
    recurring = []
    rec_id = 1
    subscription_merchants = MERCHANTS["Subscriptions"]
    for user in users:
        # Each user has 2-4 recurring subscriptions
        chosen = random.sample(subscription_merchants, random.randint(2, 4))
        for merchant in chosen:
            avg_amount = round(random.uniform(8, 25), 2)
            freq_days  = random.choice([30, 30, 30, 7])   # mostly monthly
            last_seen  = random_date(40, 5)
            annual     = round(avg_amount * (365 / freq_days), 2)
            recurring.append({
                "id":              rec_id,
                "user_id":         user["id"],
                "merchant":        merchant,
                "average_amount":  avg_amount,
                "frequency_days":  freq_days,
                "last_seen":       last_seen.strftime("%Y-%m-%d"),
                "annual_estimate": annual,
                "created_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            rec_id += 1
    return recurring


# ============================================================
# CSV WRITERS
# ============================================================
def write_csv(filename, rows, fieldnames):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  ✅ {filename} — {len(rows)} rows")


# ============================================================
# POSTGRESQL LOADER (optional)
# ============================================================
def load_to_postgres(users, transactions, budgets, fraud_logs, savings, recurring):
    try:
        import psycopg2
    except ImportError:
        print("\n❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return

    print("\n📦 Loading into PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    try:
        # Users
        for u in users:
            cur.execute("""
                INSERT INTO users (id, username, email, password_hash, created_at)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (u["id"], u["username"], u["email"], u["password_hash"], u["created_at"]))

        # Transactions
        for t in transactions:
            cur.execute("""
                INSERT INTO transactions (id, user_id, amount, category, description, date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (t["id"], t["user_id"], t["amount"], t["category"],
                  t["description"], t["date"], t["created_at"]))

        # Budgets
        for b in budgets:
            cur.execute("""
                INSERT INTO budgets (id, user_id, category, limit_amount, month, year, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (b["id"], b["user_id"], b["category"], b["limit_amount"],
                  b["month"], b["year"], b["created_at"]))

        # Fraud logs
        for f in fraud_logs:
            cur.execute("""
                INSERT INTO fraud_logs (id, user_id, transaction_id, rule_triggered, flagged_at)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (f["id"], f["user_id"], f["transaction_id"],
                  f["rule_triggered"], f["flagged_at"]))

        # Savings
        for s in savings:
            cur.execute("""
                INSERT INTO savings (id, user_id, source_transaction_id, rounded_amount, saved_at)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (s["id"], s["user_id"], s["source_transaction_id"],
                  s["rounded_amount"], s["saved_at"]))

        # Recurring
        for r in recurring:
            cur.execute("""
                INSERT INTO recurring_transactions
                (id, user_id, merchant, average_amount, frequency_days, last_seen, annual_estimate, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """, (r["id"], r["user_id"], r["merchant"], r["average_amount"],
                  r["frequency_days"], r["last_seen"], r["annual_estimate"], r["created_at"]))

        conn.commit()
        print("  ✅ All data loaded into PostgreSQL successfully!")

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {e}")
    finally:
        cur.close()
        conn.close()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--load", action="store_true",
                        help="Also load data into PostgreSQL after generating CSVs")
    args = parser.parse_args()

    print("🔧 Generating simulated data...\n")

    users        = generate_users(NUM_USERS)
    transactions = generate_transactions(users)
    budgets      = generate_budgets(users)
    fraud_logs   = generate_fraud_logs(users, transactions)
    savings      = generate_savings(users, transactions)
    recurring    = generate_recurring(users)

    print("📄 Writing CSV files...")
    write_csv("users.csv",        users,        ["id","username","email","password_hash","created_at"])
    write_csv("transactions.csv", transactions, ["id","user_id","amount","category","description","date","created_at"])
    write_csv("budgets.csv",      budgets,      ["id","user_id","category","limit_amount","month","year","created_at"])
    write_csv("fraud_logs.csv",   fraud_logs,   ["id","user_id","transaction_id","rule_triggered","flagged_at"])
    write_csv("savings.csv",      savings,      ["id","user_id","source_transaction_id","rounded_amount","saved_at"])
    write_csv("recurring_transactions.csv", recurring,
              ["id","user_id","merchant","average_amount","frequency_days","last_seen","annual_estimate","created_at"])

    print(f"\n📊 Summary:")
    print(f"   Users:                   {len(users)}")
    print(f"   Transactions:            {len(transactions)}")
    print(f"   Budgets:                 {len(budgets)}")
    print(f"   Fraud logs:              {len(fraud_logs)}")
    print(f"   Savings:                 {len(savings)}")
    print(f"   Recurring transactions:  {len(recurring)}")

    if args.load:
        load_to_postgres(users, transactions, budgets, fraud_logs, savings, recurring)
    else:
        print("\n💡 To also load into PostgreSQL, run:")
        print("   python generate_data.py --load")
        print("   (update DB_CONFIG at the top of the file first!)\n")

    print("\n✅ Done! CSV files saved in the current folder.")
