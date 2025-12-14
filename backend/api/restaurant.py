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
    RestaurantPlatMappingCreate,
    # NEW SCHEMAS FOR UX 4.7
    RestaurantOverview,
    PlatListResponse,
    PlatDetail,
    CostBreakdownResponse,
    IngredientListItem,
    IngredientPriceHistoryResponse,
    FoodCostAnalysis,
    PriceSimulation,
    PriceSimulationInput,
    RestaurantAlertDetail,
    RestaurantMenuOverview,
)
from backend.services import restaurant as restaurant_service
from backend.services.restaurant import menus as restaurant_menus_service
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


@router.get("/bank-statements", response_model=list[RestaurantBankStatementEntry], deprecated=True)
def list_bank_statements(
    account: str | None = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: Utiliser GET /finance/transactions à la place.
    Cet endpoint sera supprimé dans une version future.
    """
    return restaurant_service.list_bank_statements(tenant.id, account=account)


@router.get("/bank-accounts/overview", response_model=list[RestaurantBankAccountOverview], deprecated=True)
def list_bank_accounts_overview(tenant: Tenant = Depends(get_current_tenant)):
    """
    DEPRECATED: Utiliser GET /finance/accounts/overview à la place.
    Cet endpoint sera supprimé dans une version future.
    """
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


@router.get("/epicerie/products")
def list_epicerie_products():
    """List all epicerie products available for mapping."""
    return restaurant_service.list_epicerie_products(tenant_epicerie=1)


@router.put("/plats/{plat_id}/mapping", response_model=RestaurantPlatEpicerieLink)
def upsert_plat_mapping(
    plat_id: int,
    payload: RestaurantPlatMappingCreate,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Create or update a plat-epicerie mapping."""
    restaurant_service.upsert_plat_epicerie_mapping(
        tenant_restaurant=tenant.id,
        plat_id=plat_id,
        produit_epicerie_id=payload.produit_epicerie_id,
        ratio=payload.ratio,
    )
    links = restaurant_service.list_plat_epicerie_links(tenant.id)
    for link in links:
        if link["plat_id"] == plat_id:
            return link
    return {"plat_id": plat_id, "plat_nom": "", "produit_epicerie_id": payload.produit_epicerie_id, "ratio": payload.ratio}


@router.delete("/plats/{plat_id}/mapping")
def delete_plat_mapping(
    plat_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Delete a plat-epicerie mapping."""
    restaurant_service.delete_plat_epicerie_mapping(tenant.id, plat_id)
    return {"status": "deleted", "plat_id": plat_id}


@router.get("/bank-statements/summary", response_model=RestaurantBankStatementSummary, deprecated=True)
def bank_statement_summary(
    account: str | None = Query(None),
    months: int = Query(6, ge=0, le=120),
    grouping: str | None = Query("default"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: Utiliser GET /finance/stats/treasury à la place.
    Cet endpoint sera supprimé dans une version future.
    """
    return restaurant_service.get_bank_statement_summary(tenant.id, account=account, months=months, grouping=grouping)


@router.post("/bank-statements", response_model=RestaurantBankStatementEntry, deprecated=True)
def create_bank_statement(
    payload: RestaurantBankStatementCreate,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: Utiliser POST /finance/transactions à la place.
    Cet endpoint sera supprimé dans une version future.
    """
    return restaurant_service.create_bank_statement(tenant.id, payload.dict())


@router.patch("/bank-statements/{entry_id}", response_model=RestaurantBankStatementEntry, deprecated=True)
def update_bank_statement(
    entry_id: int,
    payload: RestaurantBankStatementUpdate,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: Utiliser PATCH /finance/transactions/{id} à la place.
    Cet endpoint sera supprimé dans une version future.
    """
    update_payload = {k: v for k, v in payload.dict().items() if v is not None}
    return restaurant_service.update_bank_statement(tenant.id, entry_id, update_payload)


@router.post("/bank-statements/{entry_id}/create-expense", response_model=RestaurantBankStatementExpenseLink, deprecated=True)
def create_expense_from_statement(
    entry_id: int,
    payload: RestaurantExpenseFromStatement,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: La liaison transaction-dépense sera gérée via /finance/*.
    Cet endpoint sera supprimé dans une version future.
    """
    result = restaurant_service.create_expense_from_bank_statement(tenant.id, entry_id, payload.dict(exclude_unset=True))
    return RestaurantBankStatementExpenseLink(
        expense=result["expense"],
        statement=result["statement"],
    )


@router.post("/bank-statements/import-pdf", deprecated=True)
async def import_bank_statements_pdf(
    account: str = Form(...),
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    DEPRECATED: Utiliser POST /finance/bank-statements/import à la place.
    Cet endpoint sera supprimé dans une version future.
    """
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


# ========== NEW ENDPOINTS FOR UX 4.7: Restaurant Overview & Food Cost ==========


@router.get("/overview", response_model=RestaurantOverview)
def get_restaurant_overview(
    period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Vue d'ensemble du restaurant.

    Returns:
    - Chiffre d'affaires période
    - Food cost % global
    - Nombre de plats actifs
    - Top 5 plats par ventes
    - Alertes (marges faibles, ruptures ingrédients)
    """
    payload = restaurant_service.get_restaurant_overview(tenant.id, period=period)
    return RestaurantOverview(**payload)


@router.get("/plats/list", response_model=PlatListResponse)
def list_plats_paginated(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    categorie: str | None = Query(None),
    actif: bool | None = Query(None),
    min_margin_pct: float | None = Query(None),
    sort_by: str = Query("nom", description="nom, margin_pct, sales_count, prix_vente_ttc"),
    sort_desc: bool = Query(False),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Liste paginée des plats avec filtres et tri.

    Filters:
    - categorie: Filtrer par catégorie
    - actif: Filtrer par statut actif/inactif
    - min_margin_pct: Marge minimale en %

    Sort:
    - sort_by: Champ de tri (nom, margin_pct, sales_count, prix_vente_ttc)
    - sort_desc: Tri descendant si true
    """
    payload = restaurant_service.list_plats_paginated(
        tenant.id,
        page=page,
        page_size=page_size,
        categorie=categorie,
        actif=actif,
        min_margin_pct=min_margin_pct,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )
    return PlatListResponse(**payload)


@router.get("/plats/{plat_id}/detail", response_model=PlatDetail)
def get_plat_detail(
    plat_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Détails complets d'un plat.

    Returns:
    - Fiche technique complète
    - Liste ingrédients avec quantités et coûts
    - Historique des prix
    - Calculs de marge et food cost
    """
    payload = restaurant_service.get_plat_detail(tenant.id, plat_id)
    return PlatDetail(**payload)


@router.get("/plats/{plat_id}/cost-breakdown", response_model=CostBreakdownResponse)
def get_plat_cost_breakdown(
    plat_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Décomposition détaillée du coût d'un plat.

    Returns:
    - Coût par ingrédient
    - % du coût total
    - Tendance prix ingrédients (30j)
    """
    payload = restaurant_service.get_plat_cost_breakdown(tenant.id, plat_id)
    return CostBreakdownResponse(**payload)


@router.get("/ingredients/list", response_model=list[IngredientListItem])
def list_ingredients_enhanced(tenant: Tenant = Depends(get_current_tenant)):
    """
    Liste enrichie des ingrédients.

    Returns:
    - Prix unitaire actuel
    - Fournisseur principal
    - Stock actuel
    - Tendance prix (30j)
    """
    ingredients = restaurant_service.list_ingredients_enhanced(tenant.id)
    return [IngredientListItem(**ing) for ing in ingredients]


@router.get("/ingredients/{ingredient_id}/price-history-detail", response_model=IngredientPriceHistoryResponse)
def get_ingredient_price_history_detail(
    ingredient_id: int,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Historique détaillé des prix d'un ingrédient.
    """
    payload = restaurant_service.get_ingredient_price_history_detail(tenant.id, ingredient_id)
    return IngredientPriceHistoryResponse(**payload)


@router.get("/food-cost/analysis", response_model=FoodCostAnalysis)
def get_food_cost_analysis(
    period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
    target_food_cost: float = Query(30.0, ge=0, le=100, description="Food cost cible en %"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Analyse complète du food cost.

    Returns:
    - Food cost par catégorie de plat
    - Évolution sur période
    - Comparaison objectif vs réel
    - Recommandations IA
    """
    payload = restaurant_service.analyze_food_cost(tenant.id, period=period, target_food_cost=target_food_cost)
    return FoodCostAnalysis(**payload)


@router.post("/plats/{plat_id}/simulate-price", response_model=PriceSimulation)
def simulate_plat_price_change(
    plat_id: int,
    payload: PriceSimulationInput,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Simulation de changement de prix.

    Input:
    - new_price: Nouveau prix de vente (OU)
    - target_margin_pct: Marge cible en % (calculera le prix nécessaire)

    Returns:
    - État actuel vs simulé
    - Impact sur food cost, marge, rentabilité
    - Estimation impact annuel
    """
    result = restaurant_service.simulate_price_change(
        tenant.id,
        plat_id,
        new_price=payload.new_price,
        target_margin_pct=payload.target_margin_pct,
    )
    return PriceSimulation(**result)


@router.get("/alerts/detailed", response_model=list[RestaurantAlertDetail])
def list_restaurant_alerts_detailed(
    alert_type: str | None = Query(None, description="plat_margin, ingredient_price, stock_rupture"),
    severity: str | None = Query(None, description="critical, warning, info"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Liste détaillée des alertes restaurant.

    Types d'alertes:
    - plat_margin: Marges < seuil
    - ingredient_price: Prix ingrédients en hausse
    - stock_rupture: Ruptures de stock prévues

    Severities:
    - critical: Action urgente requise
    - warning: À surveiller
    - info: Informatif
    """
    alerts = restaurant_service.list_alerts_detailed(
        tenant.id,
        alert_type=alert_type,
        severity=severity,
    )
    return [RestaurantAlertDetail(**alert) for alert in alerts]


# ========== SCÉNARIO 3.6 - Restaurant Menus & Coûts (inspiré newCMS) ==========


@router.get("/menus/overview", response_model=RestaurantMenuOverview)
def get_restaurant_menus_overview(tenant: Tenant = Depends(get_current_tenant)):
    """
    Vue d'ensemble des menus : coûts matière, food cost, alertes ingrédients.
    """
    return restaurant_menus_service.get_menu_overview(tenant.id)
