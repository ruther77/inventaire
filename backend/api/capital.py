from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.schemas.capital import CapitalOverviewResponse
from backend.services import capital as capital_service
from backend.dependencies.tenant import Tenant, get_current_tenant

router = APIRouter(prefix="/capital", tags=["capital"])


@router.get("/overview", response_model=CapitalOverviewResponse)
def get_capital_overview(tenant: Tenant = Depends(get_current_tenant)):
    data = capital_service.build_capital_overview()
    return CapitalOverviewResponse(
        **{
            "entities": data["entities"],
            "global_summary": data["global"],
            "latest_prices": data["latest_prices"],
        }
    )
