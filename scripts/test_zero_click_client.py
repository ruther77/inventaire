#!/usr/bin/env python
"""Client de test pour les endpoints zero-click jobs."""

from __future__ import annotations

import time
from pathlib import Path

import requests


class ZeroClickClient:
    """Client pour tester les endpoints zero-click."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

        if api_key:
            self.session.headers["X-API-Key"] = api_key

    def upload_invoice(
        self,
        file_path: str | Path,
        margin_percent: float = 40.0,
        supplier_hint: str | None = None,
        auto_confirm: bool = True,
    ) -> dict:
        """Lance un job d'import zero-click."""
        url = f"{self.base_url}/api/invoices/zero-click/jobs"

        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f, "application/pdf")}
            data = {
                "margin_percent": margin_percent,
                "auto_confirm": str(auto_confirm).lower(),
            }
            if supplier_hint:
                data["supplier_hint"] = supplier_hint

            response = self.session.post(url, files=files, data=data)
            response.raise_for_status()

        result = response.json()

        if result.get("success"):
            return result.get("data", {})
        else:
            raise Exception(f"Erreur API: {result.get('error')}")

    def get_job_status(self, job_id: str) -> dict:
        """Récupère le statut d'un job."""
        url = f"{self.base_url}/api/invoices/zero-click/jobs/{job_id}"
        response = self.session.get(url)
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            return result.get("data", {})
        else:
            raise Exception(f"Erreur API: {result.get('error')}")

    def list_jobs(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        """Liste les jobs récents."""
        url = f"{self.base_url}/api/invoices/zero-click/jobs"
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status

        response = self.session.get(url, params=params)
        response.raise_for_status()

        result = response.json()

        if result.get("success"):
            return result.get("data", {})
        else:
            raise Exception(f"Erreur API: {result.get('error')}")

    def wait_for_completion(
        self,
        job_id: str,
        timeout: int = 300,
        poll_interval: int = 2,
    ) -> dict:
        """Attend la fin d'un job avec polling."""
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Job {job_id} timeout après {timeout}s")

            job = self.get_job_status(job_id)
            status = job.get("status")

            print(f"[{elapsed:.1f}s] Job {job_id}: {status}")

            if status in ("completed", "failed"):
                return job

            time.sleep(poll_interval)


def main():
    """Exemple d'utilisation."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_zero_click_client.py <fichier.pdf> [supplier_hint]")
        sys.exit(1)

    file_path = sys.argv[1]
    supplier_hint = sys.argv[2] if len(sys.argv) > 2 else None

    # Créer le client
    client = ZeroClickClient(base_url="http://localhost:8000")

    print("=" * 60)
    print("Test Zero-Click Jobs API")
    print("=" * 60)
    print()

    # 1. Upload
    print(f"📤 Upload de {file_path}...")
    job = client.upload_invoice(
        file_path=file_path,
        supplier_hint=supplier_hint,
        margin_percent=40.0,
        auto_confirm=True,
    )

    job_id = job.get("job_id")
    print(f"✅ Job créé: {job_id}")
    print(f"   Status: {job.get('status')}")
    print(f"   Filename: {job.get('filename')}")
    print()

    # 2. Polling
    print("⏳ Attente de la fin du traitement...")
    final_job = client.wait_for_completion(job_id, timeout=300, poll_interval=2)

    print()
    print("=" * 60)
    print("Résultat final:")
    print("=" * 60)
    print(f"Status: {final_job.get('status')}")

    if final_job.get("status") == "completed":
        summary = final_job.get("summary", {})
        print(f"✅ Import réussi!")
        print(f"   Lignes reçues: {summary.get('rows_received', 0)}")
        print(f"   Mouvements créés: {summary.get('movements_created', 0)}")
        print(f"   Quantité totale: {summary.get('quantity_total', 0)}")

        errors = summary.get("errors", [])
        if errors:
            print(f"   ⚠️  Erreurs: {len(errors)}")
            for err in errors[:5]:
                print(f"      - {err}")
    else:
        print(f"❌ Import échoué!")
        print(f"   Erreur: {final_job.get('error')}")

    print()

    # 3. Liste des jobs récents
    print("=" * 60)
    print("Jobs récents:")
    print("=" * 60)

    jobs_list = client.list_jobs(limit=10)
    print(f"Total: {jobs_list.get('total', 0)} jobs")
    print()

    for job in jobs_list.get("items", [])[:5]:
        status_icon = "✅" if job["status"] == "completed" else "❌" if job["status"] == "failed" else "⏳"
        print(f"{status_icon} {job['job_id'][:8]}... - {job['status']} - {job.get('filename', 'N/A')}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
