# ------------------------------------------------------------------
# Reconciliation Configuration
# ------------------------------------------------------------------
# All tunable parameters for the reconciliation engine live here.
# Change these values without touching any logic code.
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# Dynamic fuzzy threshold based on match confidence
# ------------------------------------------------------------------
# When amount and date are strong matches, we relax the description
# requirement. When they are weaker, we require stronger description
# similarity to compensate.
#
# Confidence levels:
#   HIGH   — exact amount + same day
#   MEDIUM — exact amount + within date tolerance
#   LOW    — amount within tolerance + within date tolerance
# ------------------------------------------------------------------
# Default threshold (fallback, not used directly in dynamic matching)
FUZZY_THRESHOLD = 50

# Dynamic thresholds based on match confidence
FUZZY_THRESHOLD_HIGH_CONFIDENCE = 30    # exact amount, same day
FUZZY_THRESHOLD_MEDIUM_CONFIDENCE = 50  # exact amount, within 2 days
FUZZY_THRESHOLD_LOW_CONFIDENCE = 65     # amount within tolerance


# ------------------------------------------------------------------
# Date tolerance (in days)
# ------------------------------------------------------------------
# Maximum number of days difference allowed between a bank transaction
# date and a ledger entry date for them to be considered a match.
#
# Why not 0?
#   Bank statements often record transactions 1-2 days after they occur.
#   A payment made on Jan 1 might appear on the bank statement Jan 2 or 3.
#
# Increase if your bank consistently posts transactions late.
# Decrease if you want stricter date matching.
# ------------------------------------------------------------------
DATE_TOLERANCE_DAYS = 2


# ------------------------------------------------------------------
# Amount tolerance (in currency units — INR)
# ------------------------------------------------------------------
# Maximum absolute difference allowed between bank and ledger amounts
# for a pair to still be considered a match.
#
# Examples with AMOUNT_TOLERANCE = 1.00:
#   ₹450.00 vs ₹450.00  → difference = 0.00  → MATCH
#   ₹16.05  vs ₹16.00   → difference = 0.05  → MATCH
#   ₹100.00 vs ₹101.00  → difference = 1.00  → MATCH (at boundary)
#   ₹100.00 vs ₹101.50  → difference = 1.50  → NO MATCH
#
# Set to 0.0 for strict exact matching.
# Set to 1.0 for typical rounding/fee tolerance.
# Set to 5.0 if your bank charges small variable fees on transactions.
#
# WARNING: Higher values increase false positive risk — two different
# transactions with similar amounts and descriptions might incorrectly
# match. Only increase if you have a specific business reason.
# ------------------------------------------------------------------
AMOUNT_TOLERANCE = 1.00


# ------------------------------------------------------------------
# Match status thresholds
# ------------------------------------------------------------------
# When amount tolerance > 0, a match can be one of two types:
#   "matched"                  — amounts are exactly equal
#   "matched_with_discrepancy" — amounts differ but within tolerance
#
# The discrepancy is recorded so the finance team can review it.
# ------------------------------------------------------------------
EXACT_MATCH = "matched"
DISCREPANCY_MATCH = "matched_with_discrepancy"