from django.db import models

from django.db import models


class BankTransaction(models.Model):
    date = models.DateField()
    narration = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(
        max_length=10,
        choices=[("credit", "Credit"), ("debit", "Debit")]
    )
    category = models.CharField(max_length=100, blank=True, default="")
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} | {self.narration} | {self.amount} | {self.type}"


class LedgerEntry(models.Model):
    date = models.DateField()
    description = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.CharField(max_length=100, blank=True, default="")
    hash = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} | {self.description} | {self.amount}"