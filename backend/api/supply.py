"""
Module de gestion de la planification d'approvisionnement.

Ce module fournit l'endpoint pour calculer et optimiser les besoins
en approvisionnement basés sur:
- Les ventes quotidiennes moyennes
- Le stock actuel
- La couverture de stock cible (en jours)
- Les seuils d'alerte personnalisables

Le système suggère automatiquement les quantités à commander pour
maintenir une couverture optimale tout en évitant la rupture de stock.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.schemas.supply import SupplyPlanResponseSchema
from backend.services import supply as supply_service
from backend.dependencies.tenant import Tenant, get_current_tenant


router = APIRouter(prefix="/supply", tags=["approvisionnement"])


@router.get("/plan", response_model=SupplyPlanResponseSchema)
def get_supply_plan(
    target_coverage: int = Query(21, ge=1, le=120, description="Nombre de jours de stock visés."),
    alert_threshold: int = Query(7, ge=1, le=120, description="Seuil d'alerte en jours."),
    min_daily_sales: float = Query(
        0.0,
        ge=0,
        le=100,
        description="Filtre sur les ventes quotidiennes minimales.",
    ),
    categories: Optional[List[str]] = Query(
        default=None,
        description="Liste optionnelle de catégories à inclure (répéter le paramètre).",
    ),
    search: Optional[str] = Query(
        default=None,
        max_length=120,
        description="Terme de recherche appliqué côté serveur.",
    ),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Calcule le plan d'approvisionnement dynamique optimisé.

    Analyse le stock actuel, les ventes moyennes et calcule les quantités
    à commander pour atteindre la couverture cible. Identifie les produits
    en alerte (stock faible) et priorise les approvisionnements.

    Args:
        target_coverage: Nombre de jours de stock cible (par défaut: 21)
        alert_threshold: Seuil d'alerte en jours (par défaut: 7)
        min_daily_sales: Filtre les produits avec ventes quotidiennes min (par défaut: 0.0)
        categories: Liste optionnelle de catégories à filtrer
        search: Terme de recherche sur nom/code produit
        tenant: Tenant actuel (injecté automatiquement)

    Returns:
        SupplyPlanResponseSchema avec:
        - items: Liste des produits avec quantités à commander
        - summary: Statistiques globales (total produits, alertes, valeur)

    Raises:
        HTTPException 500: En cas d'erreur de calcul

    Example:
        GET /supply/plan?target_coverage=30&alert_threshold=5&min_daily_sales=0.5
    """
    try:
        return supply_service.compute_supply_plan(
            target_coverage=target_coverage,
            alert_threshold=alert_threshold,
            min_daily_sales=min_daily_sales,
            categories=categories,
            search=search,
            tenant_id=tenant.id,
        )
    except Exception as exc:  # pragma: no cover - FastAPI converts to 500
        raise HTTPException(status_code=500, detail=str(exc)) from exc
