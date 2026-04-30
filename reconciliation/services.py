from datetime import timedelta
from fuzzywuzzy import fuzz
from ingestion.models import BankTransaction, LedgerEntry
from .models import ReconciliationResult

# Import all config from one place
from config.reconciliation_config import (
    FUZZY_THRESHOLD,
    DATE_TOLERANCE_DAYS,
    AMOUNT_TOLERANCE,
    EXACT_MATCH,
    DISCREPANCY_MATCH,
    FUZZY_THRESHOLD_HIGH_CONFIDENCE,
    FUZZY_THRESHOLD_MEDIUM_CONFIDENCE,
    FUZZY_THRESHOLD_LOW_CONFIDENCE,
)



def amounts_are_compatible(bank_amount, ledger_amount):
    """
    Checks if two amounts are close enough to be considered a match.

    Returns (is_compatible, discrepancy, status_to_use)

    Examples with AMOUNT_TOLERANCE = 1.00:
        450.00 vs 450.00  →  (True,  0.00, "matched")
        16.05  vs 16.00   →  (True,  0.05, "matched_with_discrepancy")
        100.00 vs 102.00  →  (False, 2.00, None)
    """
    discrepancy = abs(float(bank_amount) - float(ledger_amount))

    if discrepancy == 0:
        return True, 0.00, EXACT_MATCH

    if discrepancy <= AMOUNT_TOLERANCE:
        return True, round(discrepancy, 2), DISCREPANCY_MATCH

    return False, round(discrepancy, 2), None


def get_fuzzy_threshold(date_diff_days, is_exact_amount):
    """
    Returns the appropriate fuzzy threshold based on how strongly
    the amount and date already signal a match.

    Logic:
        Exact amount + same day     → very low threshold (30)
            "we're already 90% sure, just confirm it's not random"
        Exact amount + 1-2 days     → medium threshold (50)
            "amount is certain, date is close, description helps confirm"
        Amount within tolerance     → high threshold (65)
            "amount isn't certain, need stronger description signal"
    """
    if is_exact_amount and date_diff_days == 0:
        return FUZZY_THRESHOLD_HIGH_CONFIDENCE

    if is_exact_amount and date_diff_days <= DATE_TOLERANCE_DAYS:
        return FUZZY_THRESHOLD_MEDIUM_CONFIDENCE

    return FUZZY_THRESHOLD_LOW_CONFIDENCE


def find_match_for_bank_transaction(bank_txn, unmatched_ledger_entries):
    """
    Given one bank transaction, finds the best matching ledger entry.
    Uses dynamic fuzzy threshold based on amount and date confidence.
    """
    best_match = None
    best_score = 0
    best_discrepancy = 0
    best_status = None

    bank_date = bank_txn.date
    bank_narration = bank_txn.narration.lower()

    for entry in unmatched_ledger_entries:

        # Rule 1 — Amount check with tolerance
        compatible, discrepancy, amount_status = amounts_are_compatible(
            bank_txn.amount, entry.amount
        )
        if not compatible:
            continue

        # Rule 2 — Date tolerance check
        date_diff = abs((entry.date - bank_date).days)
        if date_diff > DATE_TOLERANCE_DAYS:
            continue

        # Rule 3 — Dynamic fuzzy threshold
        is_exact = (discrepancy == 0)
        threshold = get_fuzzy_threshold(date_diff, is_exact)

        score = fuzz.token_set_ratio(bank_narration, entry.description.lower())

        if score >= threshold and score > best_score:
            best_score = score
            best_match = entry
            best_discrepancy = discrepancy
            best_status = amount_status

    return best_match, best_score, best_discrepancy, best_status


def run_reconciliation():
    """
    Main reconciliation function.
    Clears previous results and runs fresh matching.
    """
    ReconciliationResult.objects.all().delete()

    bank_transactions = list(BankTransaction.objects.all())
    ledger_entries = list(LedgerEntry.objects.all())

    matched_ledger_ids = set()
    matched_count = 0
    discrepancy_count = 0
    unmatched_bank_count = 0

    for bank_txn in bank_transactions:
        available_entries = [
            e for e in ledger_entries
            if e.id not in matched_ledger_ids
        ]

        match, score, discrepancy, status = find_match_for_bank_transaction(
            bank_txn, available_entries
        )

        if match:
            ReconciliationResult.objects.create(
                bank_transaction=bank_txn,
                ledger_entry=match,
                status=status,
                match_score=score,
                amount_discrepancy=discrepancy,
            )
            matched_ledger_ids.add(match.id)
            matched_count += 1

            if status == DISCREPANCY_MATCH:
                discrepancy_count += 1
        else:
            ReconciliationResult.objects.create(
                bank_transaction=bank_txn,
                ledger_entry=None,
                status="unmatched_bank",
                match_score=0,
                amount_discrepancy=0,
            )
            unmatched_bank_count += 1

    # Remaining unmatched ledger entries
    unmatched_ledger_count = 0
    for entry in ledger_entries:
        if entry.id not in matched_ledger_ids:
            ReconciliationResult.objects.create(
                bank_transaction=None,
                ledger_entry=entry,
                status="unmatched_ledger",
                match_score=0,
                amount_discrepancy=0,
            )
            unmatched_ledger_count += 1

    return {
        "matched": matched_count,
        "matched_exact": matched_count - discrepancy_count,
        "matched_with_discrepancy": discrepancy_count,
        "unmatched_bank": unmatched_bank_count,
        "unmatched_ledger": unmatched_ledger_count,
        "total_bank": len(bank_transactions),
        "total_ledger": len(ledger_entries),
    }