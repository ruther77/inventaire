"""Endpoints API pour les modules spécifiques restaurant."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Query, UploadFile, File, Body, HTTPException

logger = logging.getLogger(__name__)


from backend.dependencies.tenant import Tenant, get_restaurant_tenant
from backend.schemas.restaurant import (
    RestaurantForecastOverview,
    RestaurantTvaSummaryEntry,
    RestaurantCategory,
    RestaurantCategoryCreate,
    RestaurantCostCenter,
    RestaurantCostCenterCreate,
    RestaurantExpense,
    RestaurantExpenseCreate,
    RestaurantExpenseSummary,
    RestaurantIngredient,
    RestaurantIngredientCreate,
    RestaurantIngredientUpdate,
    RestaurantIngredientEpicerieLink,
    RestaurantIngredientRatioUpdate,
    RestaurantIngredientPriceHistoryEntry,
    RestaurantIngredientPriceUpdate,
    RestaurantPlat,
    RestaurantPlatCreate,
    RestaurantPlatIngredientCreate,
    RestaurantPlatIngredientUpdate,
    RestaurantPlatPriceHistoryEntry,
    RestaurantPlatPriceUpdate,
    RestaurantPriceHistoryOverview,
    RestaurantDashboardOverview,
    RestaurantAlert,
    RestaurantConsumptionEntry,
    RestaurantPriceHistoryComparisonEntry,
    # Nouveaux schémas pour l'UX 4.7
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
from backend.services.restaurant import stock as restaurant_stock_service
from backend.services import supply as supply_service  # noqa: F401
from datetime import date
from typing import Optional

router = APIRouter(prefix="/restaurant", tags=["restaurant"])


@router.get("/charges/categories", response_model=list[RestaurantCategory])
def list_categories(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_depense_categories(tenant.id)


@router.post("/charges/categories", response_model=RestaurantCategory)
def create_category(payload: RestaurantCategoryCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_depense_category(tenant.id, payload.nom)


@router.get("/charges/cost-centers", response_model=list[RestaurantCostCenter])
def list_cost_centers(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_cost_centers(tenant.id)


@router.post("/charges/cost-centers", response_model=RestaurantCostCenter)
def create_cost_center(payload: RestaurantCostCenterCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_cost_center(tenant.id, payload.nom)


@router.get("/charges/expenses", response_model=list[RestaurantExpense])
def list_expenses(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_expenses(tenant.id)


@router.post("/charges/expenses", response_model=RestaurantExpense)
def create_expense(payload: RestaurantExpenseCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_expense(
        tenant.id,
        {
            "tenant_id": tenant.id,
            **payload.dict(),
        },
    )


@router.get("/charges/summary", response_model=list[RestaurantExpenseSummary])
def expense_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.expense_summary_by_month(tenant.id)


@router.get("/charges/tva-summary", response_model=list[RestaurantTvaSummaryEntry])
def tva_summary(
    months: int = Query(6, ge=1, le=24),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.expense_summary_by_tva(tenant.id, months=months)


@router.get("/ingredients", response_model=list[RestaurantIngredient])
def list_ingredients(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_ingredients(tenant.id)


@router.post("/ingredients", response_model=RestaurantIngredient)
def create_ingredient(payload: RestaurantIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_ingredient(tenant.id, payload.dict())


@router.put("/ingredients/{ingredient_id}", response_model=RestaurantIngredient)
def update_ingredient(
    ingredient_id: int,
    payload: RestaurantIngredientUpdate,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Mettre à jour un ingrédient (nom, unité, coût, stock, catégorie, fournisseur)."""
    try:
        return restaurant_service.update_ingredient(tenant.id, ingredient_id, payload.dict(exclude_unset=True))
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ingredients/{ingredient_id}")
def delete_ingredient(
    ingredient_id: int,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Supprimer un ingrédient. Échoue si l'ingrédient est utilisé dans des plats."""
    try:
        return restaurant_service.delete_ingredient(tenant.id, ingredient_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/ingredients/{ingredient_id}/price", response_model=RestaurantIngredient)
def update_ingredient_price(
    ingredient_id: int,
    payload: RestaurantIngredientPriceUpdate,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.update_ingredient_price(tenant.id, ingredient_id, payload.cout_unitaire)


@router.get("/ingredients/{ingredient_id}/price-history", response_model=list[RestaurantIngredientPriceHistoryEntry])
def ingredient_price_history(
    ingredient_id: int,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.list_ingredient_price_history(tenant.id, ingredient_id)


@router.put("/ingredients/{ingredient_id}/link-epicerie", response_model=RestaurantIngredient)
def link_ingredient_to_epicerie(
    ingredient_id: int,
    payload: RestaurantIngredientEpicerieLink,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Lier un ingrédient à un produit épicerie pour synchroniser catégorie/fournisseur."""
    return restaurant_service.link_ingredient_to_epicerie(
        tenant.id, ingredient_id, payload.produit_epicerie_id, payload.ratio
    )


@router.patch("/ingredients/{ingredient_id}/ratio", response_model=RestaurantIngredient)
def update_ingredient_ratio(
    ingredient_id: int,
    payload: RestaurantIngredientRatioUpdate,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Mettre à jour le ratio de conversion ingrédient-épicerie."""
    return restaurant_service.update_ingredient_ratio(tenant.id, ingredient_id, payload.ratio)


@router.delete("/ingredients/{ingredient_id}/link-epicerie", response_model=RestaurantIngredient)
def unlink_ingredient_from_epicerie(
    ingredient_id: int,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Supprimer le lien entre un ingrédient et un produit épicerie."""
    return restaurant_service.unlink_ingredient_from_epicerie(tenant.id, ingredient_id)


@router.post("/ingredients/sync-prices")
def sync_ingredient_prices(
    force_update: bool = Query(False, description="Force update all linked ingredients"),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Synchronise les prix des ingrédients à partir des produits épicerie liés.

    Met à jour restaurant_ingredients.cout_unitaire depuis produits.prix_achat
    pour tous les ingrédients possédant un produit_epicerie_id.

    Args:
        force_update: Si True, mettre à jour tous les ingrédients liés. Sinon, uniquement
                     ceux dont le prix épicerie diffère du prix actuel.

    Returns:
        Résumé avec nombre d'éléments mis à jour, changements de prix et erreurs éventuelles.
    """
    from backend.services.restaurant.price_sync import sync_ingredient_prices_from_epicerie
    return sync_ingredient_prices_from_epicerie(tenant.id, force_update=force_update)


@router.get("/ingredients/price-sync-status")
def get_price_sync_status(tenant: Tenant = Depends(get_restaurant_tenant)):
    """Retourne le statut de synchronisation des prix pour tous les ingrédients.

    Renvoie un résumé indiquant quels ingrédients sont synchronisés depuis l'épicerie,
    lesquels sont désynchronisés et lesquels utilisent une tarification manuelle.
    """
    from backend.services.restaurant.price_sync import get_price_sync_summary
    return get_price_sync_summary(tenant.id)


@router.post("/ingredients/audit-epicerie-links")
def audit_ingredient_epicerie_links(
    dry_run: bool = Query(True, description="Ne pas modifier; uniquement lister les liens incohérents."),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Audit des liens incohérents ingrédients ↔ épicerie (ex: ail lié à un whisky)."""
    from backend.services.restaurant.price_sync import audit_epicerie_links
    return audit_epicerie_links(tenant.id, dry_run=dry_run)


@router.get("/ingredients/with-price-source", response_model=list[dict])
def list_ingredients_with_price_source(tenant: Tenant = Depends(get_restaurant_tenant)):
    """Liste les ingrédients avec indication explicite de la source de prix.

    Retourne les ingrédients avec des champs additionnels :
    - price_source : 'epicerie' ou 'manual'
    - is_price_synced : True si le prix correspond au produit épicerie lié
    - price_diff : écart entre le prix ingrédient et le prix épicerie
    """
    from backend.services.restaurant.price_sync import get_ingredients_with_price_source
    return get_ingredients_with_price_source(tenant.id)


# ============================================================================
# STOCK RESTAURANT (indépendant de l'épicerie)
# ============================================================================

@router.get("/stock/movements")
def list_stock_movements(
    ingredient_id: Optional[int] = None,
    source: Optional[str] = None,
    type_mouvement: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(100, ge=1, le=50000),
    offset: int = Query(0, ge=0),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Liste les mouvements de stock restaurant avec filtres."""
    return restaurant_stock_service.list_stock_movements(
        tenant_id=tenant.id,
        ingredient_id=ingredient_id,
        source=source,
        type_mouvement=type_mouvement,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/stock/movements/daily-by-category")
def get_daily_movements_by_category(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    type_mouvement: str = Query("sortie", description="Type de mouvement à agréger"),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Agrégation des mouvements par jour et catégorie pour graphiques."""
    return restaurant_stock_service.get_daily_movements_by_category(
        tenant_id=tenant.id,
        date_from=date_from,
        date_to=date_to,
        type_mouvement=type_mouvement,
    )


@router.get("/stock/movements/daily-by-plat")
def get_daily_consumption_by_plat(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Agrégation des consommations (sorties) par jour et par plat pour graphiques."""
    return restaurant_stock_service.get_daily_consumption_by_plat(
        tenant_id=tenant.id,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/stock/summary")
def get_stock_summary(tenant: Tenant = Depends(get_restaurant_tenant)):
    """Résumé du stock actuel par ingrédient."""
    return restaurant_stock_service.get_stock_summary(tenant.id)


@router.get("/stock/analytics")
def get_stock_analytics(
    days: int = Query(30, ge=1, le=365),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Statistiques de stock sur une période."""
    return restaurant_stock_service.get_stock_analytics(tenant.id, days)


@router.post("/stock/movements")
def create_stock_movement(
    ingredient_id: int = Body(...),
    type_mouvement: str = Body(...),
    quantite: float = Body(...),
    source: str = Body(...),
    unite: Optional[str] = Body(None),
    cout_unitaire: Optional[float] = Body(None),
    facture_id: Optional[int] = Body(None),
    facture_ref: Optional[str] = Body(None),
    fournisseur: Optional[str] = Body(None),
    produit_epicerie_id: Optional[int] = Body(None),
    commentaire: Optional[str] = Body(None),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Crée un mouvement de stock."""
    return restaurant_stock_service.create_stock_movement(
        tenant_id=tenant.id,
        ingredient_id=ingredient_id,
        type_mouvement=type_mouvement,
        quantite=quantite,
        source=source,
        unite=unite,
        cout_unitaire=cout_unitaire,
        facture_id=facture_id,
        facture_ref=facture_ref,
        fournisseur=fournisseur,
        produit_epicerie_id=produit_epicerie_id,
        commentaire=commentaire,
    )


@router.post("/stock/transfer-from-epicerie")
def transfer_from_epicerie(
    ingredient_id: int = Body(...),
    produit_epicerie_id: int = Body(...),
    quantite: float = Body(...),
    commentaire: Optional[str] = Body(None),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Transfère du stock depuis un produit épicerie."""
    return restaurant_stock_service.transfer_from_epicerie(
        tenant_id=tenant.id,
        ingredient_id=ingredient_id,
        produit_epicerie_id=produit_epicerie_id,
        quantite=quantite,
        commentaire=commentaire,
    )


@router.post("/stock/adjustment")
def adjust_stock(
    ingredient_id: int = Body(...),
    new_quantity: float = Body(...),
    commentaire: Optional[str] = Body(None),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Ajuste le stock à une nouvelle quantité (inventaire)."""
    return restaurant_stock_service.record_adjustment(
        tenant_id=tenant.id,
        ingredient_id=ingredient_id,
        new_quantity=new_quantity,
        commentaire=commentaire,
    )


@router.post("/stock/consumption")
def record_consumption(
    ingredient_id: int = Body(...),
    quantite: float = Body(...),
    commentaire: Optional[str] = Body(None),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Enregistre une sortie de stock pour consommation."""
    return restaurant_stock_service.record_consumption(
        tenant_id=tenant.id,
        ingredient_id=ingredient_id,
        quantite=quantite,
        commentaire=commentaire,
    )


@router.get("/plats", response_model=list[RestaurantPlat])
def list_plats(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_plats(tenant.id)


@router.post("/plats", response_model=RestaurantPlat)
def create_plat(payload: RestaurantPlatCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.create_plat(tenant.id, payload.dict())


@router.delete("/plats/{plat_id}")
def delete_plat(plat_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
    """Supprimer un plat et ses ingrédients associés."""
    try:
        return restaurant_service.delete_plat(tenant.id, plat_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/plats/{plat_id}/ingredients")
def attach_ingredient(plat_id: int, payload: RestaurantPlatIngredientCreate, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.attach_ingredient_to_plat(tenant.id, plat_id, payload.dict())


@router.delete("/plats/{plat_id}/ingredients/{ingredient_id}")
def remove_ingredient(plat_id: int, ingredient_id: int, tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.remove_ingredient_from_plat(tenant.id, plat_id, ingredient_id)


@router.patch("/plats/{plat_id}/ingredients/{ingredient_id}")
def update_ingredient_on_plat(
    plat_id: int,
    ingredient_id: int,
    payload: RestaurantPlatIngredientUpdate,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Met à jour la quantité/unité d'un ingrédient sur un plat."""
    return restaurant_service.update_plat_ingredient(tenant.id, plat_id, ingredient_id, payload.dict(exclude_unset=True))


@router.patch("/plats/{plat_id}/price", response_model=RestaurantPlat)
def update_plat_price(
    plat_id: int,
    payload: RestaurantPlatPriceUpdate,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.update_plat_price(tenant.id, plat_id, payload.prix_vente_ttc)


@router.get("/plats/{plat_id}/price-history", response_model=list[RestaurantPlatPriceHistoryEntry])
def plat_price_history(
    plat_id: int,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.list_plat_price_history(tenant.id, plat_id)


@router.post("/plats/recompute-costs")
def recompute_plat_costs(
    margin_threshold: float = Body(35.0, ge=1.0, description="Seuil de marge (%) pour générer des alertes."),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    return restaurant_service.refresh_plat_costs(tenant.id, margin_threshold=margin_threshold)


@router.get("/plats/{plat_id}/composition")
def plat_composition(
    plat_id: int,
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Retourne la composition d'un plat avec coûts par ingrédient et pourcentage."""
    return restaurant_service.get_plat_cost_breakdown(tenant.id, plat_id)




@router.post("/transfer")
def transfer_from_epicerie(
    produit_restaurant_id: int = Body(..., embed=True),
    quantite: float = Body(1.0, ge=0.0001, embed=True),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """
    Transfère du stock depuis l'épicerie vers le restaurant via la fonction SQL transfer_from_epicerie.
    """
    return restaurant_service.transfer_from_epicerie(tenant.id, produit_restaurant_id, quantite)


@router.get("/consumptions", response_model=list[RestaurantConsumptionEntry])
def list_consumptions(
    period: str = Query("all", description="Période: 7d, 30d, 90d, 1y, all"),
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    """Liste des consommations avec filtre de période optionnel."""
    return restaurant_service.list_sales_consumptions(tenant.id, period=period)


@router.get("/price-history/comparison", response_model=list[RestaurantPriceHistoryComparisonEntry])
def list_price_history_comparison(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_combined_price_history(tenant.id)


@router.get("/epicerie/products")
def list_epicerie_products():
    """List all epicerie products available for mapping."""
    return restaurant_service.list_epicerie_products(tenant_epicerie=1)


@router.get("/epicerie/products/search")
def search_epicerie_products(
    q: str = Query("", description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    suggest_for: str = Query(None, description="Ingredient name to get smart suggestions"),
):
    """
    Fast search endpoint for epicerie products.
    - q: search term (searches in product name)
    - suggest_for: if provided, returns fuzzy matches for this ingredient name
    """
    return restaurant_service.search_epicerie_products(
        tenant_epicerie=1,
        query=q,
        limit=limit,
        suggest_for=suggest_for,
    )




@router.get("/alerts", response_model=list[RestaurantAlert])
def list_restaurant_alerts(tenant: Tenant = Depends(get_restaurant_tenant)):
    return restaurant_service.list_plat_alerts(tenant.id)


@router.get("/dashboard/overview", response_model=RestaurantDashboardOverview)
def restaurant_dashboard_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
    payload = restaurant_service.build_dashboard_overview(tenant.id)
    return RestaurantDashboardOverview(**payload)


@router.get("/forecasts/overview", response_model=RestaurantForecastOverview)
def restaurant_forecast_overview(
    horizon_days: int = Query(30, ge=1, le=180),
    granularity: str = Query("weekly"),
    top: int = Query(8, ge=1, le=50),
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
):
    payload = restaurant_service.list_recent_price_changes(tenant.id, limit=limit)
    return RestaurantPriceHistoryOverview(**payload)


# ========== NEW ENDPOINTS FOR UX 4.7: Restaurant Overview & Food Cost ==========


@router.get("/overview", response_model=RestaurantOverview)
def get_restaurant_overview(
    period: str = Query("30d", description="Période: 7d, 30d, 90d, 1y"),
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
def list_ingredients_enhanced(tenant: Tenant = Depends(get_restaurant_tenant)):
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
    tenant: Tenant = Depends(get_restaurant_tenant),
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
def get_restaurant_menus_overview(tenant: Tenant = Depends(get_restaurant_tenant)):
    """
    Vue d'ensemble des menus : coûts matière, food cost, alertes ingrédients.
    """
    return restaurant_menus_service.get_menu_overview(tenant.id)
