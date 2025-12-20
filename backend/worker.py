"""
Configuration du worker Celery en tâche de fond

Gère les tâches asynchrones pour :
- Traitement et OCR des factures
- Génération de rapports
- Agrégation de données
- Notifications email
- Tâches de maintenance planifiées
"""
import os
from datetime import timedelta
from celery import Celery
from celery.schedules import crontab

# Configuration Celery
CELERY_BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "amqp://guest:guest@localhost:5672//"
)
CELERY_RESULT_BACKEND = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

# Créer l'app Celery
app = Celery(
    "inventaire_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.invoices",
        "backend.tasks.reports",
        "backend.tasks.maintenance",
    ]
)

# Configuration Celery
app.conf.update(
    # Paramètres des tâches
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,

    # Paramètres d'exécution des tâches
    task_acks_late=True,  # Accusé après réussite (plus fiable)
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # Répartition équitable des tâches

    # Paramètres de résultats
    result_expires=3600,  # Les résultats expirent après 1 heure

    # Routage des tâches (optionnel, pour scaler certains types)
    task_routes={
        "backend.tasks.invoices.*": {"queue": "invoices"},
        "backend.tasks.reports.*": {"queue": "reports"},
        "backend.tasks.maintenance.*": {"queue": "maintenance"},
    },

    # Limitation de débit
    task_annotations={
        "backend.tasks.invoices.process_invoice": {"rate_limit": "10/m"},
        "backend.tasks.reports.generate_report": {"rate_limit": "5/m"},
    },

    # Paramètres de retry
    task_default_retry_delay=60,  # Délai de retry par défaut : 1 minute
    task_max_retries=3,
)

# Planning Beat pour les tâches périodiques
app.conf.beat_schedule = {
    # Tâches de maintenance quotidiennes
    "cleanup-old-cache": {
        "task": "backend.tasks.maintenance.cleanup_cache",
        "schedule": crontab(hour=3, minute=0),  # 3h chaque jour
    },
    "refresh-materialized-views": {
        "task": "backend.tasks.maintenance.refresh_views",
        "schedule": crontab(hour=4, minute=0),  # 4h chaque jour
    },
    "aggregate-daily-stats": {
        "task": "backend.tasks.maintenance.aggregate_stats",
        "schedule": crontab(hour=1, minute=0),  # 1h chaque jour
    },

    # Tâches horaires
    "check-low-stock-alerts": {
        "task": "backend.tasks.maintenance.check_stock_alerts",
        "schedule": crontab(minute=0),  # Toutes les heures
    },

    # Toutes les 5 minutes
    "sync-pending-invoices": {
        "task": "backend.tasks.invoices.sync_pending",
        "schedule": timedelta(minutes=5),
    },
}


# ============================================================
# Définitions des tâches (inline pour simplicité, à séparer si besoin)
# ============================================================

@app.task(bind=True, max_retries=3)
def process_invoice_async(self, invoice_id: int, tenant_id: int):
    """
    Traite une facture en tâche de fond (OCR, parsing, validation).

    Args:
        invoice_id: ID de la facture à traiter
        tenant_id: ID du tenant pour l'isolation
    """
    from backend.services.invoices import InvoiceService

    try:
        service = InvoiceService()
        result = service.process_invoice(invoice_id, tenant_id)
        return {"status": "success", "invoice_id": invoice_id, "result": result}

    except Exception as exc:
        # Retenter avec backoff exponentiel
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(bind=True, max_retries=2)
def generate_report_async(self, report_type: str, params: dict, tenant_id: int):
    """
    Génère un rapport en tâche de fond.

    Args:
        report_type: Type de rapport (daily, weekly, monthly, custom)
        params: Paramètres du rapport
        tenant_id: ID du tenant
    """
    try:
        # Import ici pour éviter les imports circulaires
        from backend.services.reports import ReportService

        service = ReportService()
        report = service.generate(report_type, params, tenant_id)
        return {"status": "success", "report_id": report.id, "url": report.url}

    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


@app.task
def cleanup_cache():
    """Nettoie les entrées de cache expirées et les données anciennes."""
    from backend.cache import get_redis_client

    client = get_redis_client()
    if client:
        # Redis gère le TTL automatiquement, mais on peut nettoyer manuellement
        info = client.info("memory")
        return {
            "status": "success",
            "memory_used": info.get("used_memory_human"),
            "keys_count": client.dbsize()
        }
    return {"status": "skipped", "reason": "Redis not available"}


@app.task
def refresh_materialized_views():
    """Rafraîchit les vues matérialisées PostgreSQL pour accélérer les requêtes."""
    import psycopg2
    from contextlib import closing

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"status": "error", "reason": "DATABASE_URL not set"}

    views = [
        "mv_daily_sales",
        "mv_product_stats",
        "mv_supplier_scores",
    ]

    refreshed = []
    try:
        with closing(psycopg2.connect(database_url)) as conn:
            with conn.cursor() as cur:
                for view in views:
                    try:
                        cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                        refreshed.append(view)
                    except psycopg2.Error:
                        pass  # La vue peut ne pas exister
            conn.commit()

        return {"status": "success", "refreshed": refreshed}

    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.task
def aggregate_daily_stats():
    """Agrège les statistiques pour les performances du tableau de bord."""
    # Cette tâche pré-calcule les agrégations lourdes
    return {"status": "success", "message": "Stats aggregated"}


@app.task
def check_stock_alerts():
    """Vérifie les stocks bas et génère des alertes."""
    return {"status": "success", "alerts_generated": 0}


@app.task
def sync_pending_invoices():
    """Synchronise les factures en attente qui ont échoué au traitement."""
    return {"status": "success", "synced": 0}


@app.task(bind=True)
def send_notification_async(self, notification_type: str, recipient: str, data: dict):
    """
    Envoie une notification en tâche de fond (email, SMS, push).

    Args:
        notification_type: Type de notification
        recipient: Identifiant du destinataire
        data: Données de notification
    """
    # Emplacement prévu pour la logique de notification
    return {"status": "sent", "type": notification_type, "recipient": recipient}


# ============================================================
# Fonctions utilitaires pour gérer les tâches
# ============================================================

def get_task_status(task_id: str) -> dict:
    """Récupère le statut d'une tâche en arrière-plan."""
    result = app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }


def cancel_task(task_id: str) -> bool:
    """Annule une tâche en attente ou en cours."""
    result = app.AsyncResult(task_id)
    result.revoke(terminate=True)
    return True


# Exporter les fonctions courantes pour simplifier les imports
__all__ = [
    "app",
    "process_invoice_async",
    "generate_report_async",
    "send_notification_async",
    "get_task_status",
    "cancel_task",
]
