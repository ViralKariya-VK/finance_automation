# Finance Data Automation & Dashboard

A production-grade Django system that ingests bank statements and internal
ledger data, automatically reconciles transactions, categorizes expenses,
and exposes insights via REST APIs and a live dashboard.

Built as part of an internship assignment for **Pilgrim Skin Care**.

---

## Live Demo

| Resource | URL |
|---|---|
| Dashboard | http://13.234.48.100:8000/dashboard/ |
| Upload Page | http://13.234.48.100:8000/upload/ |
| API — Summary | http://13.234.48.100:8000/api/summary/ |
| API — Reconciliation | http://13.234.48.100:8000/api/reconciliation/ |
| API — Category Breakdown | http://13.234.48.100:8000/api/category-breakdown/ |
| API — CSV Export | http://13.234.48.100:8000/api/export/ |
| Power BI Dashboard | https://app.powerbi.com/view?r=eyJrIjoiMGI1YWI3ZjgtMWZiOC00MGI5LWEwYmItNDA3ZjdkZjRiNGMxIiwidCI6ImQxZjE0MzQ4LWYxYjUtNGEwOS1hYzk5LTdlYmYyMTNjYmM4MSIsImMiOjEwfQ%3D%3D |

---

## What it does

A company has two records of every money movement — one from their bank,
one from their internal books. They never match perfectly because descriptions
differ, dates drift by a day or two, and some transactions only appear on one
side. This system automatically reconciles them.

Upload CSV files → Django ingests and deduplicates rows → Celery background job triggers automatically → Auto-categorization (Swiggy → Food, Uber → Transport) →
Fuzzy reconciliation (matches bank vs ledger using amount + date + description) → Results stored in PostgreSQL → REST APIs expose insights → Dashboard + Power BI visualize everything

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | Django 4.2 + DRF | Production-grade ORM, admin, API toolkit |
| Database | PostgreSQL 15 | Reliable decimal handling, concurrent writes |
| Task queue | Celery 5 + Redis 7 | Non-blocking background pipeline |
| Data processing | Pandas | Robust CSV parsing, handles messy real-world files |
| Fuzzy matching | FuzzyWuzzy | Token-set ratio matching for description similarity |
| Containerization | Docker + Compose | One command deployment |
| Deployment | AWS EC2 | Public URL for Power BI and reviewer access |
| Dashboard | HTML + Chart.js | Self-contained, no external dependencies |
| BI Tool | Power BI Service | Live API connection for executive reporting |

---

## Project Structure

finance_automation/ \
├── config/ \
│   ├── settings.py              # Django settings, reads from .env \
│   ├── celery.py                # Celery app configuration \
│   ├── urls.py                  # Root URL routing \
│   └── reconciliation_config.py # All tunable parameters in one place \
├── ingestion/ \
│   ├── models.py                # BankTransaction, LedgerEntry models \
│   ├── services.py              # CSV parsing, column normalization, dedup \
│   ├── categorizer.py           # Rule-based auto-categorization \
│   ├── tasks.py                 # Celery pipeline task \
│   ├── utils.py                 # SHA-256 hash for dedup \
│   └── views.py                 # Upload API endpoints \
├── reconciliation/ \
│   ├── models.py                # ReconciliationResult model \
│   └── services.py              # Fuzzy matching engine \
├── ledger/ \
│   ├── views.py                 # Summary, reconciliation, category APIs \
│   └── templates/ledger/ \
│       ├── dashboard.html       # Live dashboard with Chart.js \
│       └── upload.html          # CSV upload page \
├── scripts/ \
│   └── generate_sample_data.py  # Generates realistic test data \
├── sample_data/ \
│   ├── bank_statement.csv       # 14-row sample \
│   ├── internal_ledger.csv      # 14-row sample \
│   ├── bank_statement_large.csv # 5000-row realistic sample \
│   └── internal_ledger_large.csv \
├── Dockerfile \
├── docker-compose.yml \
└── requirements.txt

---

## Key Technical Decisions

### Duplicate detection via SHA-256 hashing
Each row gets a hash of `date + description + amount`. Stored with
`unique=True` — database-level guarantee, zero race conditions,
handles re-uploads of the same file gracefully.

### Dynamic fuzzy threshold
Rather than one fixed similarity threshold, the system adjusts based
on how strong the other signals are:

- Exact amount + same day    → threshold 30  (already high confidence)
- Exact amount + within 2 day   → threshold 50  (moderate confidence)
- Amount within tolerance    → threshold 65  (need stronger description match)

This solved a real problem: "AWS invoice Jan" vs "Cloud hosting AWS"
scores only 44 on token_set_ratio but they share exact amount and date
— the dynamic threshold correctly matches them.

### Amount tolerance with discrepancy flagging
Instead of strict exact match or silent tolerance, pairs with small
amount differences (within ₹1 by default) are matched as
`matched_with_discrepancy` with the exact difference recorded.
Finance team can review discrepancies without losing the match.

### Celery for non-blocking pipeline
CSV upload API responds immediately. Categorization and reconciliation
run as a background Celery task. On 5000-row files this prevents
30+ second API timeouts.

### Column normalization
Real-world CSVs have inconsistent column names. The ingestion layer
maps aliases before validation:
- "Transaction Details", "narration", "remarks" → all become `narration`
- "01/01/2024", "Jan 1 2024", "2024-01-01" → all parsed correctly

---

## Reconciliation Configuration

All tunable parameters live in `config/reconciliation_config.py`.
Change business rules without touching logic code:

```python
FUZZY_THRESHOLD = 50                    # fallback threshold
FUZZY_THRESHOLD_HIGH_CONFIDENCE = 30   # exact amount, same day
FUZZY_THRESHOLD_MEDIUM_CONFIDENCE = 50 # exact amount, within 2 days
FUZZY_THRESHOLD_LOW_CONFIDENCE = 65    # amount within tolerance
DATE_TOLERANCE_DAYS = 2                # max days between matched pair
AMOUNT_TOLERANCE = 1.00                # max ₹ difference for a match
```

---

## API Reference

### GET /api/summary/
```json
{
    "total_credits": 160000.0,
    "total_debits": 13039.5,
    "net_cashflow": 146960.5,
    "unmatched_bank_amount": 1619.5,
    "unmatched_ledger_amount": 5150.0,
    "reconciliation_summary": {
        "total_bank_transactions": 14,
        "total_ledger_entries": 14,
        "matched": 12,
        "unmatched_bank": 2,
        "unmatched_ledger": 2
    }
}
```

### GET /api/reconciliation/
Optional filter: `?status=matched` or `?status=unmatched_bank`
```json
{
    "count": 17,
    "results": [
        {
            "status": "matched",
            "match_score": 86.0,
            "amount_discrepancy": 0.0,
            "bank_transaction": {
                "date": "2024-01-06",
                "narration": "Zepto groceries",
                "amount": 890.0,
                "category": "Groceries"
            },
            "ledger_entry": {
                "date": "2024-01-06",
                "description": "Grocery Zepto",
                "amount": 890.0,
                "category": "Groceries"
            }
        }
    ]
}
```

### GET /api/category-breakdown/
```json
{
    "bank_expenses_by_category": [
        {"category": "Infrastructure", "total": 5400.0},
        {"category": "Utilities", "total": 2300.0},
        {"category": "Food", "total": 1350.5}
    ],
    "ledger_by_category": [...]
}
```

### POST /api/upload/bank/
```bash
curl -X POST http://localhost:8000/api/upload/bank/ \
  -F "file=@sample_data/bank_statement.csv"
```
```json
{
    "ingestion": {"created": 14, "skipped": 0, "total_rows": 14},
    "pipeline": "triggered in background"
}
```

---

## Bonus Features Implemented

| Feature | Implementation |
|---|---|
| Auto-categorization | Keyword rulebook in `ingestion/categorizer.py` — extensible, deterministic |
| Background jobs | Celery task in `ingestion/tasks.py` — triggered via `.delay()` after upload |
| Duplicate handling | SHA-256 hash with `unique=True` DB constraint |
| Docker setup | Full `docker-compose.yml` with 4 services, healthchecks, named volumes |

---

## Local Setup

### Option 1 — Docker (recommended)

```bash
git clone https://github.com/ViralKariya-VK/finance_automation.git
cd finance_automation
cp .env.example .env        # edit with your values
docker compose up --build
```

Open http://localhost:8000/upload/ — upload the sample CSVs and
visit http://localhost:8000/dashboard/

### Option 2 — Conda

```bash
conda create -n finance_automation python=3.11
conda activate finance_automation
pip install -r requirements.txt
cp .env.example .env        # set POSTGRES_HOST=localhost
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# in a second terminal:
celery -A config worker --loglevel=info
```

---

## Deployment (AWS EC2)

```bash
# On EC2 (Ubuntu 24.04, t2.micro)
git clone https://github.com/ViralKariya-VK/finance_automation.git
cd finance_automation
cp .env.example .env
nano .env                   # set POSTGRES_HOST=db, add EC2 IP to ALLOWED_HOSTS
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

Open port 8000 in EC2 security group inbound rules.

---

## Sample Data

`sample_data/` contains two sets of CSVs:

**Small (14 rows each)** — for quick testing. Contains intentional
mismatches to demonstrate reconciliation:
- "Swiggy order #4521" ↔ "Food delivery Swiggy"
- "AWS invoice Jan" ↔ "Cloud hosting AWS"
- Netflix and Zomato intentionally unmatched on bank side
- Office supplies and Team lunch intentionally unmatched on ledger side

**Large (5000 rows each)** — generated by `scripts/generate_sample_data.py`.
Realistic distribution: 80% matched pairs, 10% bank-only, 10% ledger-only.
Dates span 2023-2024 with random drift. Amounts include occasional
sub-₹1 discrepancies to test tolerance matching.

---

## What I would add with more time

- Celery task locking to prevent concurrent reconciliation on simultaneous uploads
- `bulk_create()` for ingestion performance on very large files
- `NormalizedLedger` flat table populated as part of the pipeline
- ML-based categorization for merchant names not in the rulebook
- Webhook notifications when reconciliation completes
- REST API authentication (JWT tokens)
