"""Schémas Pydantic pour les endpoints spécifiques au restaurant."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class RestaurantCategory(BaseModel):
    id: int
    nom: str


class RestaurantCategoryCreate(BaseModel):
    nom: str = Field(..., min_length=1)


class RestaurantCostCenter(BaseModel):
    id: int
    nom: str


class RestaurantCostCenterCreate(BaseModel):
    nom: str = Field(..., min_length=1)


class RestaurantExpense(BaseModel):
    id: int
    libelle: str
    categorie: Optional[str] = None
    cost_center: Optional[str] = None
    fournisseur: Optional[str] = None
    montant_ht: float
    montant_ttc: float
    date_operation: date


class RestaurantExpenseCreate(BaseModel):
    libelle: str = Field(..., min_length=1)
    categorie_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    fournisseur_id: Optional[int] = None
    unite: Optional[str] = None
    quantite: Optional[float] = None
    prix_unitaire: Optional[float] = None
    montant_ht: Optional[float] = None
    tva_pct: Optional[float] = None
    date_operation: date = Field(default_factory=date.today)
    source: Optional[str] = None
    ref_externe: Optional[str] = None


class RestaurantExpenseSummary(BaseModel):
    label: str
    total_ht: float


class RestaurantIngredient(BaseModel):
    id: int
    nom: str
    unite_base: str
    cout_unitaire: float
    stock_actuel: float
    stock_min: Optional[float] = None
    categorie: Optional[str] = None
    fournisseur: Optional[str] = None
    produit_epicerie_id: Optional[int] = None
    ratio_epicerie: float = 1.0
    price_trend: Optional[str] = None
    price_evolution: Optional[float] = None
    price_history: Optional[List[dict]] = None


class RestaurantIngredientPriceUpdate(BaseModel):
    cout_unitaire: float = Field(..., ge=0)


class RestaurantIngredientPriceHistoryEntry(BaseModel):
    id: int
    ingredient_id: int
    ingredient_nom: str
    cout_unitaire: float
    changed_at: datetime


class RestaurantIngredientCreate(BaseModel):
    nom: str = Field(..., min_length=1)
    unite_base: str = Field(default="kg")
    cout_unitaire: float = 0
    stock_actuel: float = 0
    categorie: Optional[str] = None
    fournisseur: Optional[str] = None
    produit_epicerie_id: Optional[int] = None


class RestaurantIngredientEpicerieLink(BaseModel):
    produit_epicerie_id: int = Field(..., description="ID du produit épicerie à lier")
    ratio: float = Field(default=1.0, ge=0.0001, description="Ratio de conversion")


class RestaurantIngredientRatioUpdate(BaseModel):
    ratio: float = Field(..., ge=0.0001, description="Ratio de conversion")


class RestaurantIngredientUpdate(BaseModel):
    """Schema pour mise à jour d'un ingrédient."""
    nom: Optional[str] = Field(None, min_length=1)
    unite_base: Optional[str] = None
    cout_unitaire: Optional[float] = Field(None, ge=0)
    stock_actuel: Optional[float] = Field(None, ge=0)
    stock_min: Optional[float] = Field(None, ge=0)
    categorie: Optional[str] = None
    fournisseur: Optional[str] = None


class RestaurantPlatIngredient(BaseModel):
    id: int
    ingredient_id: int
    nom: str
    quantite: float
    unite: Optional[str] = None
    unit_price: Optional[float] = None
    total_cost: Optional[float] = None


class RestaurantPlatPriceHistoryItem(BaseModel):
    prix: float
    date: str


class RestaurantPlat(BaseModel):
    id: int
    nom: str
    categorie: Optional[str] = None
    prix_vente_ttc: float
    actif: bool
    cout_matiere: float
    marge_brute: float
    marge_pct: float
    food_cost_pct: Optional[float] = None
    ingredients: List[RestaurantPlatIngredient] = []
    price_history: List[RestaurantPlatPriceHistoryItem] = []


class RestaurantPlatCreate(BaseModel):
    nom: str = Field(..., min_length=1)
    categorie: Optional[str] = None
    prix_vente_ttc: float = 0
    actif: bool = True


class RestaurantPlatPriceUpdate(BaseModel):
    prix_vente_ttc: float = Field(..., ge=0)


class RestaurantPlatPriceHistoryEntry(BaseModel):
    id: int
    plat_id: int
    plat_nom: str
    prix_vente_ttc: float
    changed_at: datetime


class RestaurantPlatIngredientCreate(BaseModel):
    ingredient_id: int
    quantite: float
    unite: Optional[str] = None


class RestaurantPlatIngredientUpdate(BaseModel):
    """Schema pour mise à jour d'un ingrédient sur un plat (quantité/unité)."""
    quantite: Optional[float] = None
    unite: Optional[str] = None


class RestaurantAlert(BaseModel):
    id: int
    plat_id: Optional[int] = None
    plat_nom: Optional[str] = None
    severity: str
    message: str
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime


class RestaurantBankStatementEntry(BaseModel):
    id: int
    account: str
    date: date
    libelle: str
    categorie: Optional[str] = None
    montant: float
    type: str
    mois: str
    depense_id: Optional[int] = None


class RestaurantBankStatementCreate(BaseModel):
    account: str
    date: date
    libelle: str
    categorie: Optional[str] = None
    montant: float
    type: str
    mois: str


class RestaurantBankStatementUpdate(BaseModel):
    account: Optional[str] = None
    date: Optional[date] = None
    libelle: Optional[str] = None
    categorie: Optional[str] = None
    montant: Optional[float] = None
    type: Optional[str] = None
    mois: Optional[str] = None
    depense_id: Optional[int] = None


class RestaurantExpenseFromStatement(BaseModel):
    categorie_id: Optional[int] = None
    fournisseur_id: Optional[int] = None
    cost_center_id: Optional[int] = None
    libelle: Optional[str] = None
    unite: Optional[str] = None
    quantite: Optional[float] = None
    prix_unitaire: Optional[float] = None
    montant_ht: Optional[float] = None
    tva_pct: Optional[float] = None
    date_operation: Optional[date] = None


class RestaurantBankStatementMonthlySummary(BaseModel):
    mois: str
    entrees: float
    sorties: float
    net: float


class RestaurantBankStatementWeeklySummary(BaseModel):
    semaine: str
    start_date: date
    end_date: date
    entrees: float
    sorties: float
    net: float


class RestaurantBankStatementDailySummary(BaseModel):
    jour: date
    entrees: float
    sorties: float
    net: float


class RestaurantBankStatementGroupSummary(BaseModel):
    group: str
    entrees: float
    sorties: float
    net: float


class RestaurantConsumptionEntry(BaseModel):
    tenant_id: int
    produit_restaurant_id: int
    restaurant_plat: str | None = None
    ingredient_id: int | None = None
    produit_epicerie_id: int | None = None
    epicerie_nom: str
    epicerie_categorie: str
    prix_achat: float
    prix_vente: float
    stock_actuel: float
    quantity_consumed: float
    bottles_required: float
    cost_spent: float
    stock_after_sales: float
    last_sale_at: Optional[datetime] = None


class RestaurantPriceHistoryComparisonEntry(BaseModel):
    plat_id: int
    plat_nom: str
    prix_vente_ttc: float
    plat_changed_at: datetime
    epicerie_id: int | None = None
    epicerie_nom: str | None = None
    prix_achat: float | None = None
    epicerie_changed_at: Optional[datetime] = None


class RestaurantBankStatementSummaryPreset(BaseModel):
    name: str
    label: str
    groups: List[str]


class RestaurantBankAccountOverview(BaseModel):
    account: Optional[str]
    display_name: Optional[str]
    provider: Optional[str]
    status: str
    balance: float
    inflow: float
    outflow: float
    operations: int
    last_activity: Optional[date]
    currency: Optional[str]


class RestaurantBankStatementSummary(BaseModel):
    account: Optional[str]
    months: int
    grouping: str
    monthly: List[RestaurantBankStatementMonthlySummary]
    weekly: List[RestaurantBankStatementWeeklySummary]
    daily: List[RestaurantBankStatementDailySummary]
    groups: List[RestaurantBankStatementGroupSummary]
    forecast_next_month: Optional[float]
    presets: List[RestaurantBankStatementSummaryPreset]


class RestaurantBankStatementExpenseLink(BaseModel):
    expense: RestaurantExpense
    statement: RestaurantBankStatementEntry


class RestaurantForecastMetrics(BaseModel):
    total_daily_units: float
    total_daily_value: float
    at_risk_items: int
    median_cover_days: Optional[float]


class RestaurantForecastTimelineEntry(BaseModel):
    period_start: date
    period_end: date
    expected_units: float
    expected_value: float


class RestaurantForecastTopProduct(BaseModel):
    product_id: int
    nom: str
    categorie: Optional[str]
    ean: Optional[str]
    forecast_daily: float
    forecast_value: float
    stock_actuel: float
    stock_cover_days: Optional[float]
    risk_level: str


class RestaurantForecastCategoryEntry(BaseModel):
    categorie: str
    forecast_daily: float
    forecast_value: float


class RestaurantForecastOverview(BaseModel):
    horizon_days: int
    granularity: str
    generated_at: datetime
    metrics: RestaurantForecastMetrics
    timeline: List[RestaurantForecastTimelineEntry]
    top_products: List[RestaurantForecastTopProduct]
    categories: List[RestaurantForecastCategoryEntry]


class RestaurantTvaSummaryEntry(BaseModel):
    periode: date
    taux: float
    montant_ht: float
    montant_tva: float
    montant_ttc: float


class RestaurantChargeBreakdown(BaseModel):
    label: str
    total_ht: float


class RestaurantDashboardMetrics(BaseModel):
    current_month_charges: float
    avg_margin_pct: float
    active_menu_items: int
    margin_alerts: int


class RestaurantDashboardOverview(BaseModel):
    metrics: RestaurantDashboardMetrics
    charges_monthly: List[RestaurantExpenseSummary]
    charges_by_center: List[RestaurantChargeBreakdown]
    menu_costs: List[RestaurantPlat]
    low_stock_ingredients: List[RestaurantIngredient]


class RestaurantPriceHistoryOverview(BaseModel):
    ingredients: List[RestaurantIngredientPriceHistoryEntry]
    plats: List[RestaurantPlatPriceHistoryEntry]


# === NEW SCHEMAS FOR SCÉNARIO UX 4.7 ===


class RestaurantOverviewMetrics(BaseModel):
    """Métriques globales du restaurant."""
    revenue: float = Field(default=0.0, description="Chiffre d'affaires période")
    food_cost_pct: float = Field(default=0.0, description="Food cost % global")
    active_plats_count: int = Field(default=0, description="Nombre de plats actifs")
    total_plats_count: int = Field(default=0, description="Nombre total de plats")
    avg_margin_pct: float = Field(default=0.0, description="Marge moyenne %")


class RestaurantTopPlat(BaseModel):
    """Plat dans le top ventes."""
    plat_id: int
    nom: str
    sales_count: int = Field(default=0, description="Nombre de ventes")
    revenue: float = Field(default=0.0, description="CA généré")
    margin_pct: float = Field(default=0.0, description="Marge %")


class RestaurantOverviewAlert(BaseModel):
    """Alerte condensée pour overview."""
    alert_type: str
    severity: str
    message: str
    count: int = Field(default=1, description="Nombre d'items concernés")


class RestaurantOverview(BaseModel):
    """Vue d'ensemble restaurant - Endpoint principal."""
    period: str = Field(default="30d", description="Période analysée")
    metrics: RestaurantOverviewMetrics
    top_plats: List[RestaurantTopPlat] = Field(default_factory=list)
    alerts: List[RestaurantOverviewAlert] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now())


class PlatListItem(BaseModel):
    """Plat dans la liste avec filtres."""
    id: int
    nom: str
    categorie: Optional[str] = None
    selling_price: float = Field(..., alias="prix_vente_ttc")
    cost: float = Field(..., alias="cout_matiere")
    margin: float = Field(..., alias="marge_brute")
    margin_pct: float = Field(..., alias="marge_pct")
    food_cost_pct: float = Field(default=0.0, description="Food cost %")
    is_active: bool = Field(..., alias="actif")
    sales_count: Optional[int] = Field(default=None, description="Nombre de ventes")

    class Config:
        populate_by_name = True


class PlatListResponse(BaseModel):
    """Réponse paginée de la liste de plats."""
    items: List[PlatListItem]
    total: int
    page: int = 1
    page_size: int = 50


class PlatIngredientDetail(BaseModel):
    """Ingrédient avec coût dans un plat."""
    ingredient_id: int
    nom: str
    quantite: float
    unite: Optional[str] = None
    unit_price: float = Field(default=0.0, description="Prix unitaire")
    total_cost: float = Field(default=0.0, description="Coût total = quantite * unit_price")
    cost_percentage: float = Field(default=0.0, description="% du coût total du plat")


class PlatDetail(BaseModel):
    """Détails complets d'un plat."""
    id: int
    nom: str
    categorie: Optional[str] = None
    selling_price: float
    cost: float
    margin: float
    margin_pct: float
    food_cost_pct: float
    is_active: bool
    ingredients: List[PlatIngredientDetail] = Field(default_factory=list)
    price_history: List[RestaurantPlatPriceHistoryEntry] = Field(default_factory=list)


class CostBreakdownItem(BaseModel):
    """Item dans la décomposition du coût."""
    ingredient_id: int
    nom: str
    cost: float
    cost_percentage: float
    price_trend_30d: Optional[float] = Field(default=None, description="Tendance prix sur 30j en %")


class CostBreakdownResponse(BaseModel):
    """Décomposition du coût d'un plat."""
    plat_id: int
    plat_nom: str
    total_cost: float
    items: List[CostBreakdownItem]


class IngredientListItem(BaseModel):
    """Ingrédient dans la liste."""
    id: int
    nom: str
    unit: str = Field(..., alias="unite_base")
    unit_price: float = Field(..., alias="cout_unitaire")
    stock_qty: float = Field(..., alias="stock_actuel")
    main_supplier: Optional[str] = Field(default=None, description="Fournisseur principal")
    price_trend_30d: Optional[float] = Field(default=None, description="Tendance prix 30j en %")

    class Config:
        populate_by_name = True


class IngredientPriceHistoryResponse(BaseModel):
    """Historique des prix d'un ingrédient."""
    ingredient_id: int
    ingredient_nom: str
    history: List[RestaurantIngredientPriceHistoryEntry]


class FoodCostByCategoryItem(BaseModel):
    """Food cost par catégorie."""
    categorie: str
    avg_food_cost_pct: float
    plat_count: int
    total_revenue: float = Field(default=0.0)


class FoodCostTrendItem(BaseModel):
    """Évolution du food cost."""
    period: str
    food_cost_pct: float
    revenue: float = Field(default=0.0)


class FoodCostRecommendation(BaseModel):
    """Recommandation IA."""
    priority: str = Field(..., description="high, medium, low")
    category: str = Field(..., description="pricing, cost, supplier, etc.")
    message: str
    estimated_impact: Optional[float] = Field(default=None, description="Impact estimé en €")


class FoodCostAnalysis(BaseModel):
    """Analyse complète du food cost."""
    period: str = Field(default="30d")
    global_food_cost_pct: float
    target_food_cost_pct: float = Field(default=30.0)
    by_category: List[FoodCostByCategoryItem] = Field(default_factory=list)
    trend: List[FoodCostTrendItem] = Field(default_factory=list)
    recommendations: List[FoodCostRecommendation] = Field(default_factory=list)


class PriceSimulationInput(BaseModel):
    """Input pour simulation de prix."""
    new_price: Optional[float] = Field(default=None, ge=0)
    target_margin_pct: Optional[float] = Field(default=None, ge=0, le=100)


class PriceSimulationCurrent(BaseModel):
    """État actuel."""
    selling_price: float
    cost: float
    margin: float
    margin_pct: float
    food_cost_pct: float


class PriceSimulationSimulated(BaseModel):
    """État simulé."""
    selling_price: float
    cost: float
    margin: float
    margin_pct: float
    food_cost_pct: float


class PriceSimulationImpact(BaseModel):
    """Impact du changement."""
    margin_change: float = Field(..., description="Changement de marge en €")
    margin_pct_change: float = Field(..., description="Changement de marge en %")
    food_cost_change: float = Field(..., description="Changement de food cost en %")
    annual_impact: float = Field(default=0.0, description="Impact annuel estimé en €")


class PriceSimulation(BaseModel):
    """Simulation de changement de prix."""
    plat_id: int
    plat_nom: str
    current: PriceSimulationCurrent
    simulated: PriceSimulationSimulated
    impact: PriceSimulationImpact


class RestaurantAlertDetail(BaseModel):
    """Alerte détaillée."""
    id: int
    alert_type: str
    severity: str
    message: str
    plat_id: Optional[int] = None
    plat_nom: Optional[str] = None
    ingredient_id: Optional[int] = None
    ingredient_nom: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    created_at: datetime


# === NEW SCHEMAS FOR SCÉNARIO 3.6 (Menus & Coûts) ===


class RestaurantMenuPlatCost(BaseModel):
    plat_id: int
    nom: str
    prix_vente_ttc: float
    cout_matiere: float
    food_cost_pct: float
    marge_pct: float


class RestaurantMenuTopPlat(BaseModel):
    plat_id: int
    nom: str
    marge_pct: float
    prix_vente_ttc: float
    cout_matiere: float


class RestaurantMenuMetrics(BaseModel):
    total_plats: int
    avg_food_cost_pct: float
    alerts_count: int
    top_plats: list[RestaurantMenuTopPlat]


class RestaurantMenuIngredientAlert(BaseModel):
    ingredient_id: int
    nom: str
    stock_actuel: float
    cout_unitaire: float
    status: str


class RestaurantMenuOverview(BaseModel):
    metrics: RestaurantMenuMetrics
    plat_costs: list[RestaurantMenuPlatCost]
    ingredient_alerts: list[RestaurantMenuIngredientAlert]
