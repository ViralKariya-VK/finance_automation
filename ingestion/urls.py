from django.urls import path
from .views import UploadBankStatementView, UploadLedgerView

urlpatterns = [
    path("upload/bank/", UploadBankStatementView.as_view()),
    path("upload/ledger/", UploadLedgerView.as_view()),
]