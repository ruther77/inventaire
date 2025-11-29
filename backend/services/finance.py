"""Finance service exposing reconciliation helpers to the API."""

from __future__ import annotations

from typing import Any

from core.finance import reconciliation as reconciliation_core
from core.finance import insights as insights_core


def run_reconciliation(
    tenant_id: int,
    *,
    amount_tolerance: float = 2.0,
    max_days_difference: int = 10,
    auto_threshold: float = 0.9,
) -> dict[str, Any]:
    """Lance le job de rapprochement en configurant les marges de tolérance."""

    return reconciliation_core.run_reconciliation_job(
        tenant_id,
        amount_tolerance=amount_tolerance,
        max_days_difference=max_days_difference,
        auto_threshold=auto_threshold,
    )


def list_matches(tenant_id: int, status: str | None = None) -> list[dict[str, Any]]:
    """Expose les correspondances relevés/factures générées par le job de rapprochement."""

    return reconciliation_core.fetch_matches(tenant_id, status=status)


def update_match_status(tenant_id: int, match_id: int, *, status: str, note: str | None = None) -> dict[str, Any]:
    """Met à jour le statut manuel d'une correspondance (validée, rejetée...)."""

    return reconciliation_core.update_match_status(tenant_id, match_id, status=status, note=note)


def refresh_recurring(tenant_id: int, *, min_occurrences: int = 3) -> dict[str, Any]:
    """Recalcule les dépenses récurrentes à partir des relevés existants."""

    return insights_core.refresh_recurring_expenses(tenant_id, min_occurrences=min_occurrences)


def list_recurring(tenant_id: int) -> list[dict[str, Any]]:
    """Retourne les dépenses identifiées comme récurrentes."""

    return insights_core.list_recurring_expenses(tenant_id)


def refresh_anomalies(tenant_id: int, *, zscore_threshold: float = 2.5, min_occurrences: int = 3) -> dict[str, Any]:
    """Marque les anomalies de dépenses via détection statistique (z-score)."""

    return insights_core.refresh_anomaly_flags(
        tenant_id,
        zscore_threshold=zscore_threshold,
        min_occurrences=min_occurrences,
    )


def list_anomalies(tenant_id: int, severity: str | None = None) -> list[dict[str, Any]]:
    """Liste les anomalies référencées en base, filtrables par sévérité."""

    return insights_core.list_anomaly_flags(tenant_id, severity=severity)
