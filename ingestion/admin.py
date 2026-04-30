from django.contrib import admin

from django.contrib import admin
from .models import BankTransaction, LedgerEntry

@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ["date", "narration", "amount", "type", "category"]
    list_filter = ["type", "category"]
    search_fields = ["narration"]

@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["date", "description", "amount", "category"]
    list_filter = ["category"]
    search_fields = ["description"]