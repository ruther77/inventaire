"""
Async tasks for invoice processing.

This module provides background tasks for invoice-related operations
that can be time-consuming when processing large volumes.

Tasks:
- process_single_invoice: Process one invoice (OCR, parsing, validation)
- process_bulk_invoices: Import and process multiple invoices from file
- sync_pending_invoices: Retry failed invoice processing
- cleanup_old_invoices: Archive old processed invoices
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, queue="invoices")
def process_single_invoice(
    self,
    invoice_id: int,
    tenant_id: int,
    file_path: Optional[str] = None,
    force_reprocess: bool = False,
) -> Dict[str, Any]:
    """
    Process a single invoice asynchronously.

    This task wraps the synchronous invoice processing pipeline:
    1. OCR/Text extraction
    2. Parsing (extract supplier, date, items, amounts)
    3. Product matching
    4. Validation
    5. Database storage

    Args:
        invoice_id: ID of the invoice to process
        tenant_id: Tenant ID for multi-tenancy
        file_path: Optional path to invoice file (PDF/image)
        force_reprocess: Force reprocessing even if already processed

    Returns:
        Dict with processing results:
        {
            "status": "success" | "error",
            "invoice_id": int,
            "supplier": str | None,
            "total_amount": float | None,
            "items_count": int,
            "processing_time_seconds": float,
            "error": str (if status is error)
        }
    """
    import time
    start_time = time.time()

    logger.info(
        f"[Task {self.request.id}] Processing invoice {invoice_id} "
        f"(tenant={tenant_id}, force={force_reprocess})"
    )

    try:
        # Import here to avoid circular dependencies
        from backend.services.invoices import InvoiceService

        service = InvoiceService()
        result = service.process_invoice(invoice_id, tenant_id)

        processing_time = time.time() - start_time

        response = {
            "status": "success",
            "invoice_id": invoice_id,
            "supplier": result.get("supplier"),
            "total_amount": result.get("total_amount"),
            "items_count": result.get("items_count", 0),
            "processing_time_seconds": round(processing_time, 2),
        }

        logger.info(
            f"[Task {self.request.id}] Successfully processed invoice {invoice_id} "
            f"in {processing_time:.2f}s"
        )

        return response

    except Exception as exc:
        processing_time = time.time() - start_time
        logger.error(
            f"[Task {self.request.id}] Error processing invoice {invoice_id}: {exc}",
            exc_info=True
        )

        # Retry with exponential backoff: 60s, 120s, 240s
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, max_retries=2, queue="invoices")
def process_bulk_invoices(
    self,
    file_path: str,
    tenant_id: int,
    supplier_name: Optional[str] = None,
    auto_validate: bool = False,
) -> Dict[str, Any]:
    """
    Process multiple invoices from a batch file.

    This task handles mass import scenarios:
    - Multi-invoice PDF splitting
    - Batch Excel/CSV import
    - ZIP archive containing multiple invoice files

    Args:
        file_path: Path to the batch file
        tenant_id: Tenant ID for multi-tenancy
        supplier_name: Optional supplier name to apply to all invoices
        auto_validate: Automatically validate all invoices without review

    Returns:
        Dict with batch processing results:
        {
            "status": "success" | "partial" | "failed",
            "total_files": int,
            "processed": int,
            "failed": int,
            "invoices_created": List[int],
            "errors": List[str],
            "processing_time_seconds": float,
        }
    """
    import time
    start_time = time.time()

    logger.info(
        f"[Task {self.request.id}] Starting bulk invoice processing from '{file_path}' "
        f"(tenant={tenant_id}, supplier={supplier_name}, auto_validate={auto_validate})"
    )

    try:
        # Import here to avoid circular dependencies
        from core.pdf_utils import split_pdf_into_invoices
        from backend.services.invoices import import_invoice

        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        processed = 0
        failed = 0
        errors = []
        invoices_created = []

        # Handle different file types
        if file_path_obj.suffix.lower() == ".pdf":
            # Split PDF into individual invoices
            logger.info(f"[Task {self.request.id}] Splitting PDF into individual invoices...")
            invoice_files = split_pdf_into_invoices(file_path)
            total_files = len(invoice_files)

            logger.info(f"[Task {self.request.id}] Found {total_files} invoices in PDF")

            for idx, invoice_file in enumerate(invoice_files, 1):
                try:
                    # Process each invoice
                    result = import_invoice(
                        file_path=str(invoice_file),
                        tenant_id=tenant_id,
                        supplier_name=supplier_name,
                    )
                    invoices_created.append(result.get("invoice_id"))
                    processed += 1

                    if idx % 10 == 0:
                        logger.info(
                            f"[Task {self.request.id}] Progress: {idx}/{total_files} processed"
                        )

                except Exception as exc:
                    failed += 1
                    errors.append(f"File {invoice_file.name}: {str(exc)}")
                    logger.error(
                        f"[Task {self.request.id}] Failed to process {invoice_file.name}: {exc}"
                    )

        elif file_path_obj.suffix.lower() in [".xlsx", ".xls", ".csv"]:
            # Handle spreadsheet import
            logger.info(f"[Task {self.request.id}] Processing spreadsheet import...")
            # Placeholder for spreadsheet import logic
            total_files = 1
            processed = 0
            errors.append("Spreadsheet import not yet implemented")

        else:
            raise ValueError(f"Unsupported file type: {file_path_obj.suffix}")

        processing_time = time.time() - start_time

        # Determine overall status
        if failed == 0:
            status = "success"
        elif processed > 0:
            status = "partial"
        else:
            status = "failed"

        result = {
            "status": status,
            "total_files": total_files,
            "processed": processed,
            "failed": failed,
            "invoices_created": invoices_created,
            "errors": errors[:50],  # Limit errors
            "processing_time_seconds": round(processing_time, 2),
        }

        logger.info(
            f"[Task {self.request.id}] Bulk processing completed: "
            f"{processed}/{total_files} processed in {processing_time:.2f}s"
        )

        return result

    except Exception as exc:
        processing_time = time.time() - start_time
        logger.error(
            f"[Task {self.request.id}] Fatal error in bulk processing: {exc}",
            exc_info=True
        )

        # Retry with longer countdown
        countdown = 120 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(queue="invoices")
def sync_pending_invoices(tenant_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Retry processing for invoices that failed or are stuck in pending state.

    This task is scheduled to run periodically (every 5 minutes) to ensure
    no invoices are left unprocessed due to transient errors.

    Args:
        tenant_id: Optional tenant ID to limit sync to specific tenant

    Returns:
        Dict with sync results:
        {
            "status": "success",
            "pending_invoices": int,
            "retried": int,
            "succeeded": int,
            "still_failing": int,
        }
    """
    logger.info(f"[Task] Syncing pending invoices (tenant={tenant_id or 'all'})")

    try:
        from sqlalchemy import text
        from core.data_repository import query_df, get_engine

        # Query for invoices in pending/error state
        sql = text("""
            SELECT invoice_id, tenant_id, created_at
            FROM processed_invoices
            WHERE status IN ('pending', 'error')
            AND created_at > NOW() - INTERVAL '7 days'
            """ + ("AND tenant_id = :tenant_id" if tenant_id else "")
        )

        params = {"tenant_id": tenant_id} if tenant_id else {}
        pending_df = query_df(sql, params)

        pending_count = len(pending_df)
        logger.info(f"[Task] Found {pending_count} pending invoices")

        if pending_count == 0:
            return {
                "status": "success",
                "pending_invoices": 0,
                "retried": 0,
                "succeeded": 0,
                "still_failing": 0,
            }

        retried = 0
        succeeded = 0
        still_failing = 0

        for _, row in pending_df.iterrows():
            try:
                # Trigger async processing
                process_single_invoice.delay(
                    invoice_id=row["invoice_id"],
                    tenant_id=row["tenant_id"],
                    force_reprocess=True,
                )
                retried += 1
            except Exception as exc:
                still_failing += 1
                logger.error(f"[Task] Failed to retry invoice {row['invoice_id']}: {exc}")

        return {
            "status": "success",
            "pending_invoices": pending_count,
            "retried": retried,
            "succeeded": succeeded,
            "still_failing": still_failing,
        }

    except Exception as exc:
        logger.error(f"[Task] Error syncing pending invoices: {exc}", exc_info=True)
        return {
            "status": "error",
            "error": str(exc),
        }


@celery_app.task(queue="invoices")
def cleanup_old_invoices(days_to_keep: int = 365) -> Dict[str, Any]:
    """
    Archive or cleanup old processed invoices.

    This task helps manage database size by archiving invoices older
    than the specified retention period.

    Args:
        days_to_keep: Number of days to keep invoices (default: 365)

    Returns:
        Dict with cleanup results
    """
    logger.info(f"[Task] Cleaning up invoices older than {days_to_keep} days")

    try:
        from sqlalchemy import text
        from core.data_repository import exec_sql

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        # Archive old invoices (move to archive table)
        sql = text("""
            INSERT INTO processed_invoices_archive
            SELECT * FROM processed_invoices
            WHERE created_at < :cutoff_date
            ON CONFLICT DO NOTHING
        """)

        exec_sql(sql, {"cutoff_date": cutoff_date})

        # Delete from main table
        sql_delete = text("""
            DELETE FROM processed_invoices
            WHERE created_at < :cutoff_date
        """)

        exec_sql(sql_delete, {"cutoff_date": cutoff_date})

        return {
            "status": "success",
            "cutoff_date": cutoff_date.isoformat(),
            "message": "Old invoices archived successfully",
        }

    except Exception as exc:
        logger.error(f"[Task] Error cleaning up old invoices: {exc}", exc_info=True)
        return {
            "status": "error",
            "error": str(exc),
        }


# Export tasks
__all__ = [
    "process_single_invoice",
    "process_bulk_invoices",
    "sync_pending_invoices",
    "cleanup_old_invoices",
]
