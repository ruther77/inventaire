"""
Module de gestion du tableau de bord principal.

Ce module fournit les endpoints pour récupérer les métriques consolidées
du tableau de bord incluant:
- Statistiques de ventes et revenus
- Indicateurs de stock et rotation
- Alertes et notifications importantes
- Tendances et évolutions

Les données sont agrégées et optimisées pour l'affichage rapide.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.schemas.dashboard import DashboardResponse
from backend.services import dashboard as dashboard_service
from backend.dependencies.tenant import Tenant, get_current_tenant_or_default

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/metrics", response_model=DashboardResponse)
def get_dashboard_metrics(tenant: Tenant = Depends(get_current_tenant_or_default)):
    """
    Récupère les métriques consolidées du tableau de bord.

    Charge et agrège toutes les données nécessaires à l'affichage du
    tableau de bord principal incluant les KPIs, graphiques et alertes.

    Args:
        tenant: Tenant actuel (injecté automatiquement)

    Returns:
        DashboardResponse avec toutes les métriques formatées

    Example:
        GET /dashboard/metrics
    """
    data = dashboard_service.fetch_dashboard_metrics(tenant_id=tenant.id)
    return DashboardResponse(**data)
