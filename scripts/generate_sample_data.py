import pandas as pd
import random
from datetime import datetime, timedelta

# ----------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------
NUM_RECORDS = 5000
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 4, 30)
MATCH_RATE = 0.80          # 80% of transactions will have a match
DATE_DRIFT_DAYS = 2        # matched pairs can differ by up to 2 days
AMOUNT_DRIFT_RATE = 0.05   # 5% of matches will have slight amount difference

random.seed(42)

# ----------------------------------------------------------------
# Master transaction templates
# ----------------------------------------------------------------
TEMPLATES = [
    # (bank_narration, ledger_description, category, type, amount_range)
    ("Swiggy order #{}", "Food delivery Swiggy", "Food", "debit", (150, 800)),
    ("Zomato order #{}", "Zomato food order", "Food", "debit", (200, 1000)),
    ("Uber ride {}", "Cab Uber", "Transport", "debit", (80, 500)),
    ("Ola cab {}", "Ola cab ride", "Transport", "debit", (80, 400)),
    ("Amazon purchase", "Amazon online shopping", "Shopping", "debit", (300, 5000)),
    ("Flipkart order #{}", "Flipkart purchase", "Shopping", "debit", (200, 4000)),
    ("AWS invoice {}", "Cloud hosting AWS", "Infrastructure", "debit", (2000, 15000)),
    ("Google Workspace", "Google Workspace monthly", "Software", "debit", (500, 2000)),
    ("Netflix subscription", "Netflix monthly", "Entertainment", "debit", (500, 800)),
    ("Spotify premium", "Spotify subscription", "Entertainment", "debit", (100, 200)),
    ("Zepto groceries", "Grocery Zepto", "Groceries", "debit", (300, 2000)),
    ("BigBasket order", "BigBasket groceries", "Groceries", "debit", (500, 3000)),
    ("Electricity bill {}", "Electricity bill payment", "Utilities", "debit", (1000, 5000)),
    ("Airtel broadband", "Internet bill Airtel", "Utilities", "debit", (500, 1500)),
    ("Jio recharge", "Jio mobile recharge", "Utilities", "debit", (200, 600)),
    ("Microsoft Azure {}", "Azure cloud services", "Infrastructure", "debit", (3000, 20000)),
    ("Salary credit {}", "Monthly salary", "Income", "credit", (50000, 150000)),
    ("Client payment {}", "Client invoice payment", "Income", "credit", (20000, 200000)),
    ("Freelance payment {}", "Freelance project income", "Income", "credit", (10000, 80000)),
    ("Office supplies", "Office stationery", "Office", "debit", (500, 3000)),
    ("Team lunch {}", "Team lunch expense", "Food", "debit", (2000, 8000)),
    ("Flight booking {}", "Travel flight ticket", "Travel", "debit", (3000, 20000)),
    ("Hotel stay {}", "Hotel accommodation", "Travel", "debit", (2000, 15000)),
    ("Myntra order #{}", "Myntra clothing", "Shopping", "debit", (500, 3000)),
    ("Razorpay settlement {}", "Payment gateway settlement", "Income", "credit", (5000, 50000)),
    ("Slack subscription", "Slack workspace", "Software", "debit", (500, 2000)),
    ("Zoom subscription", "Zoom monthly plan", "Software", "debit", (1000, 2000)),
    ("GitHub subscription", "GitHub team plan", "Software", "debit", (400, 1500)),
    ("Figma subscription", "Figma design tool", "Software", "debit", (800, 2000)),
    ("Medical reimbursement", "Medical expenses", "Healthcare", "debit", (500, 5000)),
]


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_ref():
    return random.randint(1000, 9999)


def generate_data(num_records):
    bank_rows = []
    ledger_rows = []

    matched_count = int(num_records * MATCH_RATE)
    unmatched_bank_count = int(num_records * 0.10)
    unmatched_ledger_count = num_records - matched_count - unmatched_bank_count

    # ── Matched pairs ──────────────────────────────────────────
    for _ in range(matched_count):
        template = random.choice(TEMPLATES)
        bank_narration, ledger_desc, category, txn_type, amount_range = template

        bank_date = random_date(START_DATE, END_DATE)
        # Ledger date drifts by 0-2 days
        ledger_date = bank_date + timedelta(days=random.randint(0, DATE_DRIFT_DAYS))

        amount = round(random.uniform(*amount_range), 2)

        # Small % of matches have slight amount difference
        ledger_amount = amount
        if random.random() < AMOUNT_DRIFT_RATE:
            ledger_amount = round(amount + random.uniform(-0.99, 0.99), 2)

        ref = generate_ref()
        bank_rows.append({
            "date": bank_date.strftime("%Y-%m-%d"),
            "narration": bank_narration.format(ref),
            "amount": amount,
            "type": txn_type,
        })
        ledger_rows.append({
            "date": ledger_date.strftime("%Y-%m-%d"),
            "description": ledger_desc,
            "amount": ledger_amount,
            "category": category,
        })

    # ── Unmatched bank only ────────────────────────────────────
    bank_only_templates = [
        ("ATM withdrawal {}", "debit", (1000, 10000)),
        ("UPI transfer #{}", "debit", (500, 50000)),
        ("NEFT transfer {}", "credit", (1000, 100000)),
        ("IMPS payment {}", "debit", (200, 20000)),
        ("Cheque deposit {}", "credit", (5000, 100000)),
        ("Bank charges {}", "debit", (100, 500)),
        ("Interest credit", "credit", (100, 2000)),
        ("Refund credit {}", "credit", (200, 5000)),
    ]

    for _ in range(unmatched_bank_count):
        template = random.choice(bank_only_templates)
        narration, txn_type, amount_range = template
        amount = round(random.uniform(*amount_range), 2)
        bank_rows.append({
            "date": random_date(START_DATE, END_DATE).strftime("%Y-%m-%d"),
            "narration": narration.format(generate_ref()),
            "amount": amount,
            "type": txn_type,
        })

    # ── Unmatched ledger only ──────────────────────────────────
    ledger_only_templates = [
        ("Petty cash expense", "Office", (100, 500)),
        ("Employee advance", "Salary Advance", (5000, 20000)),
        ("Depreciation entry", "Accounting", (1000, 10000)),
        ("Prepaid expense", "Accounting", (500, 5000)),
        ("Accrued expense", "Accounting", (1000, 8000)),
        ("Stock purchase", "Inventory", (5000, 50000)),
        ("Vendor advance", "Operations", (2000, 20000)),
        ("Tax provision", "Tax", (5000, 30000)),
    ]

    for _ in range(unmatched_ledger_count):
        template = random.choice(ledger_only_templates)
        desc, category, amount_range = template
        amount = round(random.uniform(*amount_range), 2)
        ledger_rows.append({
            "date": random_date(START_DATE, END_DATE).strftime("%Y-%m-%d"),
            "description": desc,
            "amount": amount,
            "category": category,
        })

    return bank_rows, ledger_rows


# ── Generate and save ──────────────────────────────────────────
print(f"Generating {NUM_RECORDS} records each...")

bank_rows, ledger_rows = generate_data(NUM_RECORDS)

# Shuffle so dates aren't sorted
random.shuffle(bank_rows)
random.shuffle(ledger_rows)

bank_df = pd.DataFrame(bank_rows)
ledger_df = pd.DataFrame(ledger_rows)

bank_df.to_csv("sample_data/bank_statement_large.csv", index=False)
ledger_df.to_csv("sample_data/internal_ledger_large.csv", index=False)

print(f"Bank statement:   {len(bank_df)} rows → sample_data/bank_statement_large.csv")
print(f"Internal ledger:  {len(ledger_df)} rows → sample_data/internal_ledger_large.csv")
print(f"\nSample bank rows:")
print(bank_df.head(5).to_string())
print(f"\nSample ledger rows:")
print(ledger_df.head(5).to_string())