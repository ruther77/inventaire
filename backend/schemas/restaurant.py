"""Pydantic schemas for restaurant-specific endpoints."""

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


class RestaurantPlatIngredient(BaseModel):
    id: int
    ingredient_id: int
    nom: str
    quantite: float
    unite: Optional[str] = None


class RestaurantPlat(BaseModel):
    id: int
    nom: str
    categorie: Optional[str] = None
    prix_vente_ttc: float
    actif: bool
    cout_matiere: float
    marge_brute: float
    marge_pct: float
    ingredients: List[RestaurantPlatIngredient] = []


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


class RestaurantPlatEpicerieLink(BaseModel):
    plat_id: int
    plat_nom: str
    plat_categorie: str | None = None
    produit_epicerie_id: int | None = None
    epicerie_nom: str | None = None
    epicerie_categorie: str | None = None
    prix_achat: float | None = None
    prix_vente: float | None = None
    ratio: float | None = None


class RestaurantPlatMappingCreate(BaseModel):
    produit_epicerie_id: int
    ratio: float = Field(default=1.0, ge=0.0001)


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
