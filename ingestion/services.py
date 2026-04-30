import pandas as pd
from dateutil import parser as dateutil_parser
from .models import BankTransaction, LedgerEntry
from .utils import generate_hash


# ------------------------------------------------------------------
# Column name aliases
# Maps standard column names to all common variations we might see
# ------------------------------------------------------------------
BANK_COLUMN_ALIASES = {
    "date": [
        "date", "transaction date", "value date",
        "posting date", "txn date", "trans date"
    ],
    "narration": [
        "narration", "description", "details", "particular",
        "particulars", "transaction details", "remarks",
        "transaction narration", "narrative", "memo"
    ],
    "amount": [
        "amount", "transaction amount", "txn amount",
        "value", "sum", "debit amount", "credit amount"
    ],
    "type": [
        "type", "transaction type", "txn type",
        "dr/cr", "credit/debit", "debit/credit", "dr cr"
    ],
}

LEDGER_COLUMN_ALIASES = {
    "date": [
        "date", "transaction date", "entry date",
        "posting date", "ledger date", "value date"
    ],
    "description": [
        "description", "narration", "details", "particular",
        "particulars", "remarks", "memo", "note", "notes",
        "transaction details", "ledger description"
    ],
    "amount": [
        "amount", "transaction amount", "value",
        "sum", "ledger amount", "entry amount"
    ],
    "category": [
        "category", "expense category", "type",
        "expense type", "head", "cost head",
        "account head", "gl code", "gl category"
    ],
}


# ------------------------------------------------------------------
# Step 1 — Normalize column names
# Renames whatever columns exist in the CSV to our standard names
# ------------------------------------------------------------------
def normalize_columns(df, aliases):
    """
    Takes a dataframe and a aliases dict.
    Finds which actual column maps to which standard name.
    Returns renamed dataframe.

    Example:
        CSV has "Transaction Details" column
        aliases maps "narration" → ["narration", "transaction details", ...]
        Result: column renamed to "narration"
    """
    column_map = {}

    for standard_name, variations in aliases.items():
        for actual_col in df.columns:
            if actual_col.strip().lower() in variations:
                column_map[actual_col] = standard_name
                break  # first match wins, move to next standard name

    return df.rename(columns=column_map)


# ------------------------------------------------------------------
# Step 2 — Validate that required columns exist after normalization
# ------------------------------------------------------------------
def validate_columns(df, required_columns, csv_type):
    """
    After normalization, checks all required columns are present.
    Returns (is_valid, error_message)
    """
    actual = set(df.columns.str.strip().str.lower())
    missing = set(required_columns) - actual

    if missing:
        return False, (
            f"{csv_type} CSV is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}. "
            f"Please check the column names in your file."
        )

    return True, None


# ------------------------------------------------------------------
# Step 3 — Safe date parsing
# Handles any date format using dateutil
# ------------------------------------------------------------------
def parse_date_safely(date_value):
    """
    Converts any date string/value to a Python date object.

    Handles formats like:
        2024-01-01
        01/01/2024
        Jan 1 2024
        1-Jan-24
        01-01-2024
        2024/01/01

    Raises ValueError with a clear message if parsing fails.
    """
    try:
        # If pandas already parsed it as a datetime, just get the date
        if hasattr(date_value, 'date'):
            return date_value.date()

        # Otherwise parse the string
        return dateutil_parser.parse(str(date_value).strip()).date()

    except Exception:
        raise ValueError(
            f"Cannot parse date '{date_value}'. "
            f"Accepted formats: YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, "
            f"Month DD YYYY, etc."
        )


# ------------------------------------------------------------------
# Step 4 — Safe amount parsing
# Normalizes amount to 2 decimal places
# ------------------------------------------------------------------
def parse_amount_safely(amount_value):
    """
    Converts any amount value to a float rounded to 2 decimal places.

    Handles:
        "450.00"  → 450.00
        "450"     → 450.00
        "1,200"   → 1200.00  (removes commas)
        "₹450"    → 450.00   (removes currency symbols)
        450.0     → 450.00
    """
    try:
        # Remove currency symbols and commas
        cleaned = str(amount_value).strip()
        cleaned = cleaned.replace(",", "").replace("₹", "").replace("$", "").strip()
        return round(float(cleaned), 2)

    except Exception:
        raise ValueError(
            f"Cannot parse amount '{amount_value}'. "
            f"Expected a number like 450.00 or 1200"
        )


# ------------------------------------------------------------------
# Main ingestion functions
# ------------------------------------------------------------------
def ingest_bank_statement(file):
    """
    Reads a bank statement CSV, normalizes columns,
    validates structure, and saves new rows to the DB.
    """
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return {"error": f"Could not read CSV file: {str(e)}"}

    # Normalize column names to our standard names
    df = normalize_columns(df, BANK_COLUMN_ALIASES)

    # Validate required columns exist
    required = ["date", "narration", "amount", "type"]
    is_valid, error = validate_columns(df, required, "Bank statement")
    if not is_valid:
        return {"error": error}

    created_count = 0
    skipped_count = 0
    error_rows = []

    for index, row in df.iterrows():
        try:
            # Parse date and amount safely
            parsed_date = parse_date_safely(row["date"])
            parsed_amount = parse_amount_safely(row["amount"])
            narration = str(row["narration"]).strip()
            txn_type = str(row["type"]).strip().lower()

            # Validate type field
            if txn_type not in ["credit", "debit"]:
                error_rows.append({
                    "row": index + 2,  # +2 for header and 0-index
                    "error": f"Invalid type '{txn_type}'. Must be 'credit' or 'debit'"
                })
                continue

            # Generate hash for dedup
            row_hash = generate_hash(parsed_date, narration, parsed_amount)

            if BankTransaction.objects.filter(hash=row_hash).exists():
                skipped_count += 1
                continue

            BankTransaction.objects.create(
                date=parsed_date,
                narration=narration,
                amount=parsed_amount,
                type=txn_type,
                hash=row_hash,
            )
            created_count += 1

        except ValueError as e:
            error_rows.append({"row": index + 2, "error": str(e)})
            continue

    return {
        "created": created_count,
        "skipped": skipped_count,
        "total_rows": len(df),
        "errors": error_rows,
    }


def ingest_ledger(file):
    """
    Reads an internal ledger CSV, normalizes columns,
    validates structure, and saves new rows to the DB.
    """
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return {"error": f"Could not read CSV file: {str(e)}"}

    # Normalize column names
    df = normalize_columns(df, LEDGER_COLUMN_ALIASES)

    # Validate required columns exist
    required = ["date", "description", "amount", "category"]
    is_valid, error = validate_columns(df, required, "Internal ledger")
    if not is_valid:
        return {"error": error}

    created_count = 0
    skipped_count = 0
    error_rows = []

    for index, row in df.iterrows():
        try:
            parsed_date = parse_date_safely(row["date"])
            parsed_amount = parse_amount_safely(row["amount"])
            description = str(row["description"]).strip()
            category = str(row["category"]).strip() if pd.notna(row["category"]) else ""

            row_hash = generate_hash(parsed_date, description, parsed_amount)

            if LedgerEntry.objects.filter(hash=row_hash).exists():
                skipped_count += 1
                continue

            LedgerEntry.objects.create(
                date=parsed_date,
                description=description,
                amount=parsed_amount,
                category=category,
                hash=row_hash,
            )
            created_count += 1

        except ValueError as e:
            error_rows.append({"row": index + 2, "error": str(e)})
            continue

    return {
        "created": created_count,
        "skipped": skipped_count,
        "total_rows": len(df),
        "errors": error_rows,
    }