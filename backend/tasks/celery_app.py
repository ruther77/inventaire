"""
Celery Application Configuration for Inventaire System

This module configures the Celery application for distributed task processing.
Uses Redis as both broker and result backend for simplicity.

Key features:
- Redis-based broker and backend
- Multiple task queues (scoring, invoices, reports, maintenance)
- Automatic task retry with exponential backoff
- Result expiration and cleanup
- Task rate limiting
- Periodic task scheduling with Celery Beat
"""

import os
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab

# Environment variables with defaults
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# Celery broker and backend configuration
# Using Redis databases:
# - DB 1 for broker (task queue)
# - DB 2 for backend (results storage)
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
)
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND",
    f"redis://{REDIS_HOST}:{REDIS_PORT}/2"
)

# Create Celery application
celery_app = Celery(
    "inventaire",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.scoring_tasks",
        "backend.tasks.invoice_tasks",
        "backend.tasks.report_tasks",
        "backend.tasks.maintenance",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Serialization settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone settings
    timezone="Europe/Paris",
    enable_utc=True,

    # Task execution settings
    task_acks_late=True,  # Acknowledge after task completion (more reliable)
    task_reject_on_worker_lost=True,  # Reject tasks if worker dies
    worker_prefetch_multiplier=1,  # Fair task distribution

    # Result settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Task routing - direct tasks to specific queues
    task_routes={
        "backend.tasks.scoring_tasks.*": {"queue": "scoring"},
        "backend.tasks.invoice_tasks.*": {"queue": "invoices"},
        "backend.tasks.report_tasks.*": {"queue": "reports"},
        "backend.tasks.maintenance.*": {"queue": "maintenance"},
    },

    # Rate limiting to prevent overload
    task_annotations={
        "backend.tasks.scoring_tasks.recalculate_supplier_score": {"rate_limit": "10/m"},
        "backend.tasks.invoice_tasks.process_bulk_invoices": {"rate_limit": "5/m"},
        "backend.tasks.report_tasks.generate_async_report": {"rate_limit": "5/m"},
    },

    # Default retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,

    # Worker settings
    worker_max_tasks_per_child=1000,  # Restart worker after 1000 tasks (memory cleanup)
    worker_disable_rate_limits=False,

    # Monitoring
    task_track_started=True,
    task_send_sent_event=True,
)

# Celery Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Supplier scoring recalculation - Daily at 2 AM
    "recalculate-all-supplier-scores": {
        "task": "backend.tasks.scoring_tasks.recalculate_all_suppliers",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "scoring"},
    },

    # Maintenance tasks
    "cleanup-cache": {
        "task": "backend.tasks.maintenance.cleanup_cache",
        "schedule": crontab(hour=3, minute=0),  # 3 AM daily
        "options": {"queue": "maintenance"},
    },

    "refresh-materialized-views": {
        "task": "backend.tasks.maintenance.refresh_views",
        "schedule": crontab(hour=4, minute=0),  # 4 AM daily
        "options": {"queue": "maintenance"},
    },

    "aggregate-daily-stats": {
        "task": "backend.tasks.maintenance.aggregate_stats",
        "schedule": crontab(hour=1, minute=0),  # 1 AM daily
        "options": {"queue": "maintenance"},
    },

    # Hourly tasks
    "check-low-stock-alerts": {
        "task": "backend.tasks.maintenance.check_stock_alerts",
        "schedule": crontab(minute=0),  # Every hour
        "options": {"queue": "maintenance"},
    },

    # Periodic invoice synchronization - Every 5 minutes
    "sync-pending-invoices": {
        "task": "backend.tasks.invoice_tasks.sync_pending_invoices",
        "schedule": timedelta(minutes=5),
        "options": {"queue": "invoices"},
    },
}

# Health check task
@celery_app.task(name="backend.tasks.celery_app.health_check")
def health_check():
    """Health check task for monitoring."""
    return {
        "status": "healthy",
        "timestamp": str(celery_app.now()),
        "broker": CELERY_BROKER_URL,
        "backend": CELERY_RESULT_BACKEND,
    }

# Export the app
__all__ = ["celery_app"]
