from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import ingest_bank_statement, ingest_ledger
from .tasks import run_pipeline


class UploadBankStatementView(APIView):
    """
    POST /api/upload/bank/
    Ingests the CSV, then triggers the background pipeline.
    """

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return Response(
                {"error": "Only CSV files are accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save rows to DB
        result = ingest_bank_statement(file)

        # Trigger background pipeline — returns immediately
        # Celery worker picks this up and runs categorization + reconciliation
        run_pipeline.delay()

        return Response({
            "ingestion": result,
            "pipeline": "triggered in background"
        }, status=status.HTTP_201_CREATED)


class UploadLedgerView(APIView):
    """
    POST /api/upload/ledger/
    Ingests the CSV, then triggers the background pipeline.
    """

    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not file.name.endswith(".csv"):
            return Response(
                {"error": "Only CSV files are accepted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = ingest_ledger(file)

        run_pipeline.delay()

        return Response({
            "ingestion": result,
            "pipeline": "triggered in background"
        }, status=status.HTTP_201_CREATED)