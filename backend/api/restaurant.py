"""API endpoints for restaurant-specific modules."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, Body

from backend.dependencies.tenant import Tenant, get_current_tenant
from backend.schemas.restaurant import (
    RestaurantBankStatementCreate,
    RestaurantBankStatementEntry,
    RestaurantBankStatementUpdate,
    RestaurantBankStatementSummary,
    RestaurantBankAccountOverview,
    RestaurantForecastOverview,
    RestaurantTvaSummaryEntry,
    RestaurantBankStatementExpenseLink,
    RestaurantCategory,
    RestaurantCategoryCreate,
    RestaurantCostCenter,
    RestaurantCostCenterCreate,
    RestaurantExpense,
    RestaurantExpenseCreate,
    RestaurantExpenseSummary,
    RestaurantExpenseFromStatement,
    RestaurantIngredient,
    RestaurantIngredientCreate,
    RestaurantIngredientPriceHistoryEntry,
    RestaurantIngredientPriceUpdate,
    RestaurantPlat,
    RestaurantPlatCreate,
    RestaurantPlatIngredientCreate,
    RestaurantPlatPriceHistoryEntry,
    RestaurantPlatPriceUpdate,
    RestaurantPriceHistoryOverview,
    RestaurantDashboardOverview,
    RestaurantAlert,
    RestaurantConsumptionEntry,
    RestaurantPriceHistoryComparisonEntry,
    RestaurantPlatEpicerieLink,
)
from backend.services import restaurant as restaurant_service
from backend.services import supply as supply_service  # noqa: F401

router = APIRouter(prefix="/restaurant", tags=["restaurant"])


@router.get("/charges/categories", response_model=list[RestaurantCategory])
def list_categories(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_depense_categories(tenant.id)


@router.post("/charges/categories", response_model=RestaurantCategory)
def create_category(payload: RestaurantCategoryCreate, tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.create_depense_category(tenant.id, payload.nom)


@router.get("/charges/cost-centers", response_model=list[RestaurantCostCenter])
def list_cost_centers(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_cost_centers(tenant.id)


@router.post("/charges/cost-centers", response_model=RestaurantCostCenter)
def create_cost_center(payload: RestaurantCostCenterCreate, tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.create_cost_center(tenant.id, payload.nom)


@router.get("/charges/expenses", response_model=list[RestaurantExpense])
def list_expenses(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_expenses(tenant.id)


@router.post("/charges/expenses", response_model=RestaurantExpense)
def create_expense(payload: RestaurantExpenseCreate, tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.create_expense(
        tenant.id,
        {
            "tenant_id": tenant.id,
            **payload.dict(),
        },
    )


@router.get("/charges/summary", response_model=list[RestaurantExpenseSummary])
def expense_summary(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.expense_summary_by_month(tenant.id)


@router.get("/charges/tva-summary", response_model=list[RestaurantTvaSummaryEntry])
def tva_summary(
    months: int = Query(6, ge=1, le=24),
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.expense_summary_by_tva(tenant.id, months=months)


@router.get("/ingredients", response_model=list[RestaurantIngredient])
def list_ingredients(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_ingredients(tenant.id)


@router.post("/ingredients", response_model=RestaurantIngredient)
def create_ingredient(payload: RestaurantIngredientCreate, tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.create_ingredient(tenant.id, payload.dict())


@router.patch("/ingredients/{ingredient_id}/price", response_model=RestaurantIngredient)
def update_ingredient_price(
    ingredient_id: int,
    payload: RestaurantIngredientPriceUpdate,
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.update_ingredient_price(tenant.id, ingredient_id, payload.cout_unitaire)


@router.get("/ingredients/{ingredient_id}/price-history", response_model=list[RestaurantIngredientPriceHistoryEntry])
def ingredient_price_history(
    ingredient_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.list_ingredient_price_history(tenant.id, ingredient_id)


@router.get("/plats", response_model=list[RestaurantPlat])
def list_plats(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_plats(tenant.id)


@router.post("/plats", response_model=RestaurantPlat)
def create_plat(payload: RestaurantPlatCreate, tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.create_plat(tenant.id, payload.dict())


@router.post("/plats/{plat_id}/ingredients")
def attach_ingredient(plat_id: int, payload: RestaurantPlatIngredientCreate, tenant: Tenant = Depends(get_current_tenant)):
    restaurant_service.attach_ingredient_to_plat(tenant.id, plat_id, payload.dict())
    return {"status": "updated"}


@router.patch("/plats/{plat_id}/price", response_model=RestaurantPlat)
def update_plat_price(
    plat_id: int,
    payload: RestaurantPlatPriceUpdate,
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.update_plat_price(tenant.id, plat_id, payload.prix_vente_ttc)


@router.get("/plats/{plat_id}/price-history", response_model=list[RestaurantPlatPriceHistoryEntry])
def plat_price_history(
    plat_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.list_plat_price_history(tenant.id, plat_id)


@router.post("/plats/recompute-costs")
def recompute_plat_costs(
    margin_threshold: float = Body(35.0, ge=1.0, description="Seuil de marge (%) pour générer des alertes."),
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.refresh_plat_costs(tenant.id, margin_threshold=margin_threshold)


@router.get("/bank-statements", response_model=list[RestaurantBankStatementEntry])
def list_bank_statements(
    account: str | None = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.list_bank_statements(tenant.id, account=account)


@router.get("/bank-accounts/overview", response_model=list[RestaurantBankAccountOverview])
def list_bank_accounts_overview(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_bank_accounts_overview(tenant.id)


@router.post("/transfer")
def transfer_from_epicerie(
    produit_restaurant_id: int = Body(..., embed=True),
    quantite: float = Body(1.0, ge=0.0001, embed=True),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Transfère du stock depuis l'épicerie vers le restaurant via la fonction SQL transfer_from_epicerie.
    """
    return restaurant_service.transfer_from_epicerie(tenant.id, produit_restaurant_id, quantite)


@router.get("/consumptions", response_model=list[RestaurantConsumptionEntry])
def list_consumptions(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_sales_consumptions(tenant.id)


@router.get("/price-history/comparison", response_model=list[RestaurantPriceHistoryComparisonEntry])
def list_price_history_comparison(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_combined_price_history(tenant.id)


@router.get("/plats/mappings", response_model=list[RestaurantPlatEpicerieLink])
def list_plats_with_epicerie(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_plat_epicerie_links(tenant.id)


@router.post("/ingredients/sync")
def sync_ingredients(tenant: Tenant = Depends(get_current_tenant)):
    count = restaurant_service.sync_ingredients_from_mappings(tenant.id)
    return {"inserted": count}


@router.get("/bank-statements/summary", response_model=RestaurantBankStatementSummary)
def bank_statement_summary(
    account: str | None = Query(None),
    months: int = Query(6, ge=0, le=120),
    grouping: str | None = Query("default"),
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.get_bank_statement_summary(tenant.id, account=account, months=months, grouping=grouping)


@router.post("/bank-statements", response_model=RestaurantBankStatementEntry)
def create_bank_statement(
    payload: RestaurantBankStatementCreate,
    tenant: Tenant = Depends(get_current_tenant),
):
    return restaurant_service.create_bank_statement(tenant.id, payload.dict())


@router.patch("/bank-statements/{entry_id}", response_model=RestaurantBankStatementEntry)
def update_bank_statement(
    entry_id: int,
    payload: RestaurantBankStatementUpdate,
    tenant: Tenant = Depends(get_current_tenant),
):
    update_payload = {k: v for k, v in payload.dict().items() if v is not None}
    return restaurant_service.update_bank_statement(tenant.id, entry_id, update_payload)


@router.post("/bank-statements/{entry_id}/create-expense", response_model=RestaurantBankStatementExpenseLink)
def create_expense_from_statement(
    entry_id: int,
    payload: RestaurantExpenseFromStatement,
    tenant: Tenant = Depends(get_current_tenant),
):
    result = restaurant_service.create_expense_from_bank_statement(tenant.id, entry_id, payload.dict(exclude_unset=True))
    return RestaurantBankStatementExpenseLink(
        expense=result["expense"],
        statement=result["statement"],
    )


@router.post("/bank-statements/import-pdf")
async def import_bank_statements_pdf(
    account: str = Form(...),
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
):
    content = await file.read()
    summary = restaurant_service.import_bank_statements_from_pdf(tenant.id, account, content)
    duplicates = summary["total"] - summary["inserted"]
    return {"inserted": summary["inserted"], "total": summary["total"], "duplicates": duplicates}


@router.get("/alerts", response_model=list[RestaurantAlert])
def list_restaurant_alerts(tenant: Tenant = Depends(get_current_tenant)):
    return restaurant_service.list_plat_alerts(tenant.id)


@router.get("/dashboard/overview", response_model=RestaurantDashboardOverview)
def restaurant_dashboard_overview(tenant: Tenant = Depends(get_current_tenant)):
    payload = restaurant_service.build_dashboard_overview(tenant.id)
    return RestaurantDashboardOverview(**payload)


@router.get("/forecasts/overview", response_model=RestaurantForecastOverview)
def restaurant_forecast_overview(
    horizon_days: int = Query(30, ge=1, le=180),
    granularity: str = Query("weekly"),
    top: int = Query(8, ge=1, le=50),
    tenant: Tenant = Depends(get_current_tenant),
):
    payload = restaurant_service.build_forecast_overview(
        tenant.id,
        horizon_days=horizon_days,
        granularity=granularity,
        top_limit=top,
    )
    return RestaurantForecastOverview(**payload)


@router.get("/prices/history", response_model=RestaurantPriceHistoryOverview)
def price_history_overview(
    limit: int = Query(12, ge=1, le=200),
    tenant: Tenant = Depends(get_current_tenant),
):
    payload = restaurant_service.list_recent_price_changes(tenant.id, limit=limit)
    return RestaurantPriceHistoryOverview(**payload)
