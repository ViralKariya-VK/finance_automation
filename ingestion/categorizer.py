# Rules: keyword (lowercase) → category
# Order matters — first match wins
CATEGORY_RULES = {
    # Food & drink
    "swiggy": "Food",
    "zomato": "Food",
    "zepto": "Groceries",
    "bigbasket": "Groceries",
    "blinkit": "Groceries",

    # Transport
    "uber": "Transport",
    "ola": "Transport",
    "rapido": "Transport",

    # Cloud & software
    "aws": "Infrastructure",
    "amazon web": "Infrastructure",
    "google workspace": "Software",
    "microsoft": "Software",
    "netflix": "Entertainment",
    "spotify": "Entertainment",

    # Shopping
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",

    # Utilities
    "electricity": "Utilities",
    "bescom": "Utilities",
    "mseb": "Utilities",
    "broadband": "Utilities",
    "airtel": "Utilities",
    "jio": "Utilities",

    # Finance
    "salary": "Income",
    "client payment": "Income",
    "invoice": "Income",
    "advance": "Salary Advance",

    # Office
    "office": "Office",
}


def categorize(description):
    """
    Takes a transaction description and returns a category.

    Checks each keyword against the description (case-insensitive).
    Returns the first matching category.
    If nothing matches, returns "Uncategorized".
    """
    description_lower = description.lower()

    for keyword, category in CATEGORY_RULES.items():
        if keyword in description_lower:
            return category

    return "Uncategorized"


def categorize_all_transactions():
    """
    Runs categorization on every BankTransaction and LedgerEntry
    that currently has no category assigned.

    This is called by the Celery task in Step 6.
    Returns a count of how many records were updated.
    """
    # Import here to avoid circular imports
    from .models import BankTransaction, LedgerEntry

    updated = 0

    # Categorize bank transactions that are still empty
    bank_txns = BankTransaction.objects.filter(category="")
    for txn in bank_txns:
        txn.category = categorize(txn.narration)
        txn.save()
        updated += 1

    # Categorize ledger entries that are still empty
    ledger_entries = LedgerEntry.objects.filter(category="")
    for entry in ledger_entries:
        entry.category = categorize(entry.description)
        entry.save()
        updated += 1

    return updated