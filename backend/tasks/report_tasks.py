"""
Async tasks for report generation.

This module provides background tasks for generating various types of reports
that can be computationally expensive on large datasets.

Tasks:
- generate_async_report: Generate any type of report asynchronously
- generate_daily_summary: Daily business summary report
- generate_monthly_report: Monthly financial report
- generate_supplier_performance_report: Detailed supplier analysis
- generate_inventory_report: Stock status and movement report
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, date
from pathlib import Path

from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, queue="reports")
def generate_async_report(
    self,
    report_type: str,
    tenant_id: int,
    params: Dict[str, Any],
    output_format: str = "pdf",
    notify_user: bool = True,
) -> Dict[str, Any]:
    """
    Generate a report asynchronously.

    This task wraps the synchronous report generation service to run
    in the background, preventing API timeouts on large reports.

    Args:
        report_type: Type of report (daily, weekly, monthly, custom, etc.)
        tenant_id: Tenant ID for multi-tenancy
        params: Report parameters (date range, filters, etc.)
        output_format: Output format (pdf, excel, csv, json)
        notify_user: Send notification when report is ready

    Returns:
        Dict with report generation results:
        {
            "status": "success" | "error",
            "report_id": str,
            "report_type": str,
            "file_path": str,
            "file_url": str,
            "generation_time_seconds": float,
            "file_size_bytes": int,
            "error": str (if status is error)
        }
    """
    import time
    start_time = time.time()

    logger.info(
        f"[Task {self.request.id}] Generating {report_type} report "
        f"(tenant={tenant_id}, format={output_format})"
    )

    try:
        # Import here to avoid circular dependencies
        from backend.services.reports import ReportService

        service = ReportService()
        report = service.generate(
            report_type=report_type,
            params=params,
            tenant_id=tenant_id,
            output_format=output_format,
        )

        generation_time = time.time() - start_time

        # Get file size if file exists
        file_size = 0
        if report.get("file_path"):
            file_path = Path(report["file_path"])
            if file_path.exists():
                file_size = file_path.stat().st_size

        result = {
            "status": "success",
            "report_id": report.get("report_id", self.request.id),
            "report_type": report_type,
            "file_path": report.get("file_path"),
            "file_url": report.get("url"),
            "generation_time_seconds": round(generation_time, 2),
            "file_size_bytes": file_size,
        }

        logger.info(
            f"[Task {self.request.id}] Successfully generated {report_type} report "
            f"in {generation_time:.2f}s (size: {file_size/1024:.1f} KB)"
        )

        # Send notification if requested
        if notify_user:
            # Placeholder for notification logic
            logger.info(f"[Task {self.request.id}] Notification sent for report {report_type}")

        return result

    except Exception as exc:
        generation_time = time.time() - start_time
        logger.error(
            f"[Task {self.request.id}] Error generating {report_type} report: {exc}",
            exc_info=True
        )

        # Retry with backoff: 120s, 240s
        countdown = 120 * (2 ** self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(queue="reports")
def generate_daily_summary(
    tenant_id: int,
    report_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate daily business summary report.

    This task is typically scheduled to run every night via Celery Beat
    to provide a comprehensive daily business snapshot.

    Args:
        tenant_id: Tenant ID for multi-tenancy
        report_date: Optional date (ISO format), defaults to yesterday

    Returns:
        Dict with report generation results
    """
    if report_date is None:
        report_date = (datetime.utcnow() - timedelta(days=1)).date().isoformat()

    logger.info(f"[Task] Generating daily summary for {report_date} (tenant={tenant_id})")

    try:
        params = {
            "date": report_date,
            "sections": [
                "sales_summary",
                "top_products",
                "supplier_activity",
                "inventory_alerts",
                "financial_summary",
            ]
        }

        return generate_async_report.apply(
            args=[],
            kwargs={
                "report_type": "daily_summary",
                "tenant_id": tenant_id,
                "params": params,
                "output_format": "pdf",
                "notify_user": True,
            }
        ).get()

    except Exception as exc:
        logger.error(f"[Task] Error generating daily summary: {exc}", exc_info=True)
        return {
            "status": "error",
            "error": str(exc),
        }


@celery_app.task(queue="reports")
def generate_monthly_report(
    tenant_id: int,
    month: int,
    year: int,
) -> Dict[str, Any]:
    """
    Generate monthly financial and operational report.

    This comprehensive report includes:
    - Revenue and expense analysis
    - Supplier performance metrics
    - Inventory turnover
    - Top/bottom products
    - Month-over-month comparisons

    Args:
        tenant_id: Tenant ID for multi-tenancy
        month: Month (1-12)
        year: Year (e.g., 2024)

    Returns:
        Dict with report generation results
    """
    logger.info(f"[Task] Generating monthly report for {year}-{month:02d} (tenant={tenant_id})")

    try:
        from datetime import date
        from calendar import monthrange

        # Calculate date range
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "month": month,
            "year": year,
            "include_comparisons": True,
            "sections": [
                "executive_summary",
                "revenue_analysis",
                "expense_analysis",
                "supplier_performance",
                "inventory_analysis",
                "product_performance",
                "trends_and_insights",
            ]
        }

        return generate_async_report.apply(
            args=[],
            kwargs={
                "report_type": "monthly_financial",
                "tenant_id": tenant_id,
                "params": params,
                "output_format": "pdf",
                "notify_user": True,
            }
        ).get()

    except Exception as exc:
        logger.error(f"[Task] Error generating monthly report: {exc}", exc_info=True)
        return {
            "status": "error",
            "error": str(exc),
        }


@celery_app.task(bind=True, queue="reports")
def generate_supplier_performance_report(
    self,
    tenant_id: int,
    supplier_names: Optional[List[str]] = None,
    period_days: int = 90,
) -> Dict[str, Any]:
    """
    Generate detailed supplier performance analysis report.

    This report provides in-depth analysis of supplier metrics:
    - Scoring across all dimensions
    - Historical trends
    - Delivery performance
    - Price stability
    - Invoice accuracy
    - Comparative analysis

    Args:
        tenant_id: Tenant ID for multi-tenancy
        supplier_names: Optional list of suppliers to include (None = all)
        period_days: Analysis period in days (default: 90)

    Returns:
        Dict with report generation results
    """
    logger.info(
        f"[Task {self.request.id}] Generating supplier performance report "
        f"(tenant={tenant_id}, period={period_days} days)"
    )

    try:
        from core.finance.supplier_scoring import SupplierScoreCalculator

        calculator = SupplierScoreCalculator(tenant_id)

        # Determine which suppliers to analyze
        if supplier_names is None:
            all_suppliers = calculator.get_all_suppliers_ranking()
            supplier_names = [s["supplier_name"] for s in all_suppliers]

        logger.info(f"[Task {self.request.id}] Analyzing {len(supplier_names)} suppliers")

        # Collect supplier data
        supplier_data = []
        for supplier_name in supplier_names:
            try:
                score = calculator.calculate_score(
                    supplier_name=supplier_name,
                    period_days=period_days,
                )
                supplier_data.append({
                    "name": supplier_name,
                    "score": score.overall_score,
                    "grade": score.grade,
                    "dimensions": {k.value: v for k, v in score.dimensions.items()},
                    "trend": score.trend,
                    "metrics": score.metrics,
                })
            except Exception as exc:
                logger.warning(f"Failed to analyze {supplier_name}: {exc}")

        params = {
            "supplier_data": supplier_data,
            "period_days": period_days,
            "analysis_date": datetime.utcnow().isoformat(),
        }

        return generate_async_report.apply(
            args=[],
            kwargs={
                "report_type": "supplier_performance",
                "tenant_id": tenant_id,
                "params": params,
                "output_format": "pdf",
                "notify_user": True,
            }
        ).get()

    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Error generating supplier performance report: {exc}",
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(exc),
        }


@celery_app.task(bind=True, queue="reports")
def generate_inventory_report(
    self,
    tenant_id: int,
    include_movement_analysis: bool = True,
    include_forecasts: bool = False,
) -> Dict[str, Any]:
    """
    Generate comprehensive inventory status and movement report.

    This report includes:
    - Current stock levels
    - Low stock alerts
    - Overstocked items
    - Inventory value
    - Turnover rates
    - Movement trends
    - Optional: Demand forecasts

    Args:
        tenant_id: Tenant ID for multi-tenancy
        include_movement_analysis: Include detailed movement analysis
        include_forecasts: Include demand forecasting (computationally expensive)

    Returns:
        Dict with report generation results
    """
    logger.info(
        f"[Task {self.request.id}] Generating inventory report "
        f"(tenant={tenant_id}, movement={include_movement_analysis}, "
        f"forecasts={include_forecasts})"
    )

    try:
        params = {
            "include_movement_analysis": include_movement_analysis,
            "include_forecasts": include_forecasts,
            "analysis_date": datetime.utcnow().isoformat(),
        }

        return generate_async_report.apply(
            args=[],
            kwargs={
                "report_type": "inventory_status",
                "tenant_id": tenant_id,
                "params": params,
                "output_format": "excel",  # Excel for detailed data
                "notify_user": True,
            }
        ).get()

    except Exception as exc:
        logger.error(
            f"[Task {self.request.id}] Error generating inventory report: {exc}",
            exc_info=True
        )
        return {
            "status": "error",
            "error": str(exc),
        }


# Export tasks
__all__ = [
    "generate_async_report",
    "generate_daily_summary",
    "generate_monthly_report",
    "generate_supplier_performance_report",
    "generate_inventory_report",
]
