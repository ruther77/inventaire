"""Supply planning endpoints."""

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
    alert_threshold: int = Query(7, ge=1, le=120, description="Seuil d’alerte en jours."),
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
    """Expose the dynamic supply planning data structure."""

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
