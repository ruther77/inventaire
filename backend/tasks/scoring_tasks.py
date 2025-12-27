"""
Async tasks for supplier scoring recalculation.

This module provides background tasks for computationally expensive
supplier scoring operations that would timeout in synchronous API calls.

Tasks:
- recalculate_supplier_score: Recalculate score for a single supplier
- recalculate_all_suppliers: Recalculate scores for all suppliers (nightly batch)
- recalculate_suppliers_batch: Recalculate scores for a list of suppliers
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from backend.tasks.celery_app import celery_app
from core.finance.supplier_scoring import SupplierScoreCalculator

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, queue="scoring")
def recalculate_supplier_score(
    self,
    supplier_name: str,
    tenant_id: int,
    period_days: int = 90,
    supplier_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Recalculate score for a single supplier.

    This task wraps the synchronous SupplierScoreCalculator.calculate_score()
    method to run asynchronously in the background.

    Args:
        supplier_name: Name of the supplier
        tenant_id: Tenant ID for multi-tenancy
        period_days: Analysis period in days (default: 90)
        supplier_id: Optional supplier ID

    Returns:
        Dict with calculation results:
        {
            "status": "success" | "error",
            "supplier_name": str,
            "supplier_id": int | None,
            "overall_score": float,
            "grade": str,
            "calculated_at": str (ISO timestamp),
            "error": str (if status is error)
        }

    Raises:
        Retries with exponential backoff on failure (max 3 retries)
    """
    try:
        logger.info(
            f"[Task {self.request.id}] Recalculating score for supplier '{supplier_name}' "
            f"(tenant={tenant_id}, period={period_days} days)"
        )

        # Initialize calculator
        calculator = SupplierScoreCalculator(tenant_id)

        # Calculate score (synchronous operation wrapped in async task)
        score = calculator.calculate_score(
            supplier_name=supplier_name,
            supplier_id=supplier_id,
            period_days=period_days,
        )

        result = {
            "status": "success",
            "supplier_name": supplier_name,
            "supplier_id": score.supplier_id,
            "overall_score": score.overall_score,
            "grade": score.grade,
            "dimensions": {k.value: v for k, v in score.dimensions.items()},
            "trend": score.trend,
            "calculated_at": score.last_updated.isoformat(),
        }

        logger.info(
            f"[Task {self.request.id}] Successfully calculated score for '{supplier_name}': "
            f"{score.overall_score:.1f} ({score.grade})"
        )

        return result

    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Error calculating score for '{supplier_name}': {exc}",
            exc_info=True
        )

        # Retry with exponential backoff: 60s, 120s, 240s
        countdown = 60 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(bind=True, queue="scoring")
def recalculate_all_suppliers(
    self,
    tenant_id: int,
    period_days: int = 90,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Recalculate scores for all suppliers (batch operation).

    This task is typically scheduled to run nightly via Celery Beat
    to keep all supplier scores up-to-date.

    Args:
        tenant_id: Tenant ID for multi-tenancy
        period_days: Analysis period in days (default: 90)
        force: Force recalculation even if recently calculated

    Returns:
        Dict with batch processing results:
        {
            "status": "success" | "partial" | "failed",
            "total_suppliers": int,
            "processed": int,
            "failed": int,
            "duration_seconds": float,
            "errors": List[str],
            "started_at": str,
            "completed_at": str,
        }
    """
    import time

    started_at = datetime.utcnow()
    start_time = time.time()

    logger.info(
        f"[Task {self.request.id}] Starting batch recalculation for all suppliers "
        f"(tenant={tenant_id}, period={period_days} days, force={force})"
    )

    try:
        calculator = SupplierScoreCalculator(tenant_id)

        # Get all suppliers
        all_suppliers = calculator.get_all_suppliers_ranking()
        supplier_names = [s["supplier_name"] for s in all_suppliers]
        total_suppliers = len(supplier_names)

        logger.info(f"[Task {self.request.id}] Found {total_suppliers} suppliers to process")

        # Process each supplier
        processed = 0
        failed = 0
        errors = []

        for idx, supplier_name in enumerate(supplier_names, 1):
            try:
                calculator.calculate_score(
                    supplier_name=supplier_name,
                    period_days=period_days,
                )
                processed += 1

                # Log progress every 10 suppliers
                if idx % 10 == 0:
                    logger.info(
                        f"[Task {self.request.id}] Progress: {idx}/{total_suppliers} "
                        f"({processed} success, {failed} failed)"
                    )

            except Exception as exc:
                failed += 1
                error_msg = f"{supplier_name}: {str(exc)}"
                errors.append(error_msg)
                logger.error(
                    f"[Task {self.request.id}] Failed to calculate score for '{supplier_name}': {exc}"
                )

        duration = time.time() - start_time
        completed_at = datetime.utcnow()

        # Determine overall status
        if failed == 0:
            status = "success"
        elif processed > 0:
            status = "partial"
        else:
            status = "failed"

        result = {
            "status": status,
            "total_suppliers": total_suppliers,
            "processed": processed,
            "failed": failed,
            "duration_seconds": round(duration, 2),
            "errors": errors[:50],  # Limit error list to first 50
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
        }

        logger.info(
            f"[Task {self.request.id}] Batch recalculation completed: "
            f"{processed}/{total_suppliers} processed in {duration:.2f}s"
        )

        return result

    except Exception as exc:
        duration = time.time() - start_time
        logger.error(
            f"[Task {self.request.id}] Fatal error in batch recalculation: {exc}",
            exc_info=True
        )
        return {
            "status": "failed",
            "error": str(exc),
            "duration_seconds": round(duration, 2),
            "started_at": started_at.isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
        }


@celery_app.task(bind=True, max_retries=2, queue="scoring")
def recalculate_suppliers_batch(
    self,
    supplier_names: List[str],
    tenant_id: int,
    period_days: int = 90,
) -> Dict[str, Any]:
    """
    Recalculate scores for a specific list of suppliers.

    Useful for selective recalculation when only certain suppliers
    have new data (e.g., after invoice import).

    Args:
        supplier_names: List of supplier names to recalculate
        tenant_id: Tenant ID for multi-tenancy
        period_days: Analysis period in days (default: 90)

    Returns:
        Dict with batch processing results
    """
    import time

    start_time = time.time()
    logger.info(
        f"[Task {self.request.id}] Starting batch recalculation for "
        f"{len(supplier_names)} suppliers (tenant={tenant_id})"
    )

    try:
        calculator = SupplierScoreCalculator(tenant_id)

        processed = 0
        failed = 0
        errors = []

        for supplier_name in supplier_names:
            try:
                calculator.calculate_score(
                    supplier_name=supplier_name,
                    period_days=period_days,
                )
                processed += 1
            except Exception as exc:
                failed += 1
                errors.append(f"{supplier_name}: {str(exc)}")
                logger.error(
                    f"[Task {self.request.id}] Failed to calculate score for '{supplier_name}': {exc}"
                )

        duration = time.time() - start_time

        result = {
            "status": "success" if failed == 0 else "partial",
            "total_suppliers": len(supplier_names),
            "processed": processed,
            "failed": failed,
            "duration_seconds": round(duration, 2),
            "errors": errors,
        }

        logger.info(
            f"[Task {self.request.id}] Batch recalculation completed: "
            f"{processed}/{len(supplier_names)} processed in {duration:.2f}s"
        )

        return result

    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Error in batch recalculation: {exc}",
            exc_info=True
        )
        raise self.retry(exc=exc, countdown=120)


# Export tasks
__all__ = [
    "recalculate_supplier_score",
    "recalculate_all_suppliers",
    "recalculate_suppliers_batch",
]
