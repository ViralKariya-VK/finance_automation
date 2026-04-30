from django.urls import path
from .views import (
    SummaryView,
    ReconciliationView,
    CategoryBreakdownView,
    ExportLedgerView,
    DashboardView,
    UploadPageView,
)

urlpatterns = [
    path("summary/", SummaryView.as_view()),
    path("reconciliation/", ReconciliationView.as_view()),
    path("category-breakdown/", CategoryBreakdownView.as_view()),
    path("export/", ExportLedgerView.as_view()),
    path("dashboard/", DashboardView.as_view()),
    path("upload/", UploadPageView.as_view()),
]