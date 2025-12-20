"""Tâches de fond pour le traitement des factures."""
from backend.worker import app


@app.task(bind=True, max_retries=3, queue="invoices")
def process_invoice(self, invoice_id: int, tenant_id: int):
    """Traite une facture (OCR, parsing, validation)."""
    try:
        # Traitement lourd à exécuter ici
        return {"status": "processed", "invoice_id": invoice_id}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@app.task(queue="invoices")
def sync_pending():
    """Synchronise les factures en attente."""
    return {"status": "success", "synced": 0}


@app.task(bind=True, queue="invoices")
def batch_import_invoices(self, file_path: str, tenant_id: int):
    """Importe des factures depuis un fichier batch."""
    return {"status": "imported", "count": 0}
