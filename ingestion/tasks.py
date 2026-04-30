from celery import shared_task
from ingestion.categorizer import categorize_all_transactions
from reconciliation.services import run_reconciliation


@shared_task
def run_pipeline():
    """
    Background task that runs the full pipeline:
    1. Categorize all uncategorized transactions
    2. Run reconciliation between bank and ledger

    Triggered automatically after every CSV upload.
    Called with run_pipeline.delay() — the .delay() means
    "run this in the background, don't make the API wait."
    """

    # Step 1 — categorize
    updated = categorize_all_transactions()

    # Step 2 — reconcile
    result = run_reconciliation()

    return {
        "categorized": updated,
        "reconciliation": result,
    }