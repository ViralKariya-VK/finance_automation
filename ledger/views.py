from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum
from django.http import HttpResponse
from ingestion.models import BankTransaction, LedgerEntry
from reconciliation.models import ReconciliationResult
import csv
from django.shortcuts import render


class SummaryView(APIView):
    """
    GET /api/summary/
    Returns high-level financial summary.
    """

    def get(self, request):
        # Total credits from bank
        total_credits = BankTransaction.objects.filter(
            type="credit"
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Total debits from bank
        total_debits = BankTransaction.objects.filter(
            type="debit"
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Unmatched amount — sum of bank transactions with no ledger match
        unmatched_bank_amount = BankTransaction.objects.filter(
            reconciliation__status="unmatched_bank"
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Unmatched amount on ledger side
        unmatched_ledger_amount = LedgerEntry.objects.filter(
            reconciliation__status="unmatched_ledger"
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Reconciliation counts
        total_bank = BankTransaction.objects.count()
        total_ledger = LedgerEntry.objects.count()
        matched = ReconciliationResult.objects.filter(
            status="matched"
        ).count()

        return Response({
            "total_credits": float(total_credits),
            "total_debits": float(total_debits),
            "net_cashflow": float(total_credits - total_debits),
            "unmatched_bank_amount": float(unmatched_bank_amount),
            "unmatched_ledger_amount": float(unmatched_ledger_amount),
            "reconciliation_summary": {
                "total_bank_transactions": total_bank,
                "total_ledger_entries": total_ledger,
                "matched": matched,
                "unmatched_bank": ReconciliationResult.objects.filter(
                    status="unmatched_bank"
                ).count(),
                "unmatched_ledger": ReconciliationResult.objects.filter(
                    status="unmatched_ledger"
                ).count(),
            }
        })


class ReconciliationView(APIView):
    """
    GET /api/reconciliation/
    Returns full list of matched and unmatched entries.
    """

    def get(self, request):
        status_filter = request.query_params.get("status", None)
        limit = request.query_params.get("limit", None)

        queryset = ReconciliationResult.objects.all()
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if limit:
            queryset = queryset[:int(limit)]

        results = []
        for r in queryset:
            results.append({
                "id": r.id,
                "status": r.status,
                "match_score": r.match_score,
                "bank_transaction": {
                    "id": r.bank_transaction.id,
                    "date": str(r.bank_transaction.date),
                    "narration": r.bank_transaction.narration,
                    "amount": float(r.bank_transaction.amount),
                    "type": r.bank_transaction.type,
                    "category": r.bank_transaction.category,
                } if r.bank_transaction else None,
                "ledger_entry": {
                    "id": r.ledger_entry.id,
                    "date": str(r.ledger_entry.date),
                    "description": r.ledger_entry.description,
                    "amount": float(r.ledger_entry.amount),
                    "category": r.ledger_entry.category,
                } if r.ledger_entry else None,
            })

        return Response({
            "count": len(results),
            "results": results
        })


class CategoryBreakdownView(APIView):
    """
    GET /api/category-breakdown/
    Returns expenses grouped by category.
    Power BI will use this to build the pie chart.
    """

    def get(self, request):
        # Group bank transactions by category and sum amounts
        # Only debits (expenses) — credits are income
        breakdown = BankTransaction.objects.filter(
            type="debit"
        ).values("category").annotate(
            total=Sum("amount")
        ).order_by("-total")

        # Also get ledger breakdown for comparison
        ledger_breakdown = LedgerEntry.objects.values(
            "category"
        ).annotate(
            total=Sum("amount")
        ).order_by("-total")

        return Response({
            "bank_expenses_by_category": [
                {
                    "category": item["category"] or "Uncategorized",
                    "total": float(item["total"])
                }
                for item in breakdown
            ],
            "ledger_by_category": [
                {
                    "category": item["category"] or "Uncategorized",
                    "total": float(item["total"])
                }
                for item in ledger_breakdown
            ]
        })


class ExportLedgerView(APIView):
    """
    GET /api/export/
    Returns full reconciliation data as a downloadable CSV.
    Used to connect Power BI when direct API connection isn't available.
    """

    def get(self, request):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="ledger_export.csv"'

        writer = csv.writer(response)

        # Header row
        writer.writerow([
            "date",
            "narration",
            "amount",
            "type",
            "category",
            "source",
            "reconciliation_status",
            "match_score"
        ])

        # Write reconciliation results
        for r in ReconciliationResult.objects.all():
            if r.bank_transaction:
                writer.writerow([
                    r.bank_transaction.date,
                    r.bank_transaction.narration,
                    r.bank_transaction.amount,
                    r.bank_transaction.type,
                    r.bank_transaction.category,
                    "bank",
                    r.status,
                    r.match_score,
                ])
            if r.ledger_entry:
                writer.writerow([
                    r.ledger_entry.date,
                    r.ledger_entry.description,
                    r.ledger_entry.amount,
                    "n/a",
                    r.ledger_entry.category,
                    "ledger",
                    r.status,
                    r.match_score,
                ])

        return response
    
class DashboardView(APIView):
    """
    GET /dashboard/
    Serves the HTML dashboard page.
    """
    def get(self, request):
        return render(request, "ledger/dashboard.html")
    
class UploadPageView(APIView):
    """
    GET /upload/
    Serves the CSV upload page.
    """
    def get(self, request):
        return render(request, "ledger/upload.html")