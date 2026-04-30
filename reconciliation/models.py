from django.db import models

from django.db import models
from ingestion.models import BankTransaction, LedgerEntry


class ReconciliationResult(models.Model):

    STATUS_CHOICES = [
        ("matched", "Matched"),
        ("unmatched_bank", "Unmatched - Bank only"),
        ("unmatched_ledger", "Unmatched - Ledger only"),
    ]

    bank_transaction = models.OneToOneField(
        BankTransaction,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reconciliation"
    )
    ledger_entry = models.OneToOneField(
        LedgerEntry,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="reconciliation"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    match_score = models.FloatField(default=0.0)

    # New field — records the amount difference for discrepancy cases
    amount_discrepancy = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.status} | score: {self.match_score} | diff: {self.amount_discrepancy}"