from django.contrib import admin

from django.contrib import admin
from .models import ReconciliationResult

@admin.register(ReconciliationResult)
class ReconciliationResultAdmin(admin.ModelAdmin):
    list_display = ["status", "match_score", "bank_transaction", "ledger_entry", "created_at"]
    list_filter = ["status"]