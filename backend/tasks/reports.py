"""Tâches de fond pour la génération de rapports."""
from backend.worker import app


@app.task(bind=True, max_retries=2, queue="reports")
def generate_report(self, report_type: str, params: dict, tenant_id: int):
    """Génère un rapport de manière asynchrone."""
    try:
        # Logique lourde de génération de rapport
        return {
            "status": "generated",
            "report_type": report_type,
            "tenant_id": tenant_id,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)


@app.task(queue="reports")
def generate_daily_summary(tenant_id: int):
    """Génère un rapport quotidien de synthèse."""
    return {"status": "generated", "type": "daily_summary"}


@app.task(queue="reports")
def generate_monthly_report(tenant_id: int, month: int, year: int):
    """Génère un rapport financier mensuel."""
    return {"status": "generated", "type": "monthly", "month": month, "year": year}
