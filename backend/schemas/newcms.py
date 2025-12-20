"""
Schemas Pydantic pour newCMS - Morning Brief Cockpit.

Schemas optimises pour l'affichage rapide du Morning Brief avec toutes
les informations necessaires en un seul appel API.
"""

from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# KPIs et Metriques
# =============================================================================

class KPIMetric(BaseModel):
    """KPI individuel pour le cockpit."""
    key: str
    label: str
    value: float
    unit: Optional[str] = None
    trend: Optional[float] = None  # Pourcentage de variation
    trend_direction: Optional[str] = None  # "up", "down", "stable"
    status: str = "info"  # "success", "warning", "error", "info"
    icon: Optional[str] = None
    description: Optional[str] = None


class CockpitKPIs(BaseModel):
    """Ensemble des KPIs principaux du cockpit."""
    stock_value: KPIMetric
    stock_alerts: KPIMetric
    margin_avg: KPIMetric
    cash_flow_7d: KPIMetric
    anomalies_count: KPIMetric
    match_rate: KPIMetric


# =============================================================================
# Alertes
# =============================================================================

class CockpitAlert(BaseModel):
    """Alerte critique ou warning pour le Morning Brief."""
    id: str
    severity: str  # "critical", "warning", "info"
    category: str  # "stock", "finance", "margin", "anomaly", "forecast"
    title: str
    message: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    created_at: datetime
    acknowledged: bool = False
    action_url: Optional[str] = None
    impact_value: Optional[float] = None


# =============================================================================
# Anomalies Top 5
# =============================================================================

class AnomalyItem(BaseModel):
    """Anomalie individuelle (top 5)."""
    id: str
    type: str
    severity: str
    description: str
    impact: float
    detected_at: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None


# =============================================================================
# Previsions
# =============================================================================

class ForecastPoint(BaseModel):
    """Point de prevision pour les graphiques."""
    date: date
    value: float
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None


class CashFlowForecast(BaseModel):
    """Prevision de tresorerie 7 jours."""
    period_start: date
    period_end: date
    predictions: List[ForecastPoint]
    total_inflows: float
    total_outflows: float
    net_flow: float
    ending_balance: float
    alerts: List[str]


class StockForecast(BaseModel):
    """Prevision d'epuisement stock - top produits critiques."""
    product_id: int
    product_name: str
    current_stock: int
    days_until_depletion: Optional[float]
    predicted_depletion_date: Optional[date]
    recommended_reorder_date: Optional[date]
    confidence: float


# =============================================================================
# Suggestions IA
# =============================================================================

class AISuggestion(BaseModel):
    """Suggestion actionnable de l'IA."""
    id: str
    type: str  # "reorder", "price_optimization", "dead_stock", "reconciliation"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    impact_estimate: Optional[str] = None
    action_url: Optional[str] = None
    confidence: float
    created_at: datetime


# =============================================================================
# Call-to-Actions
# =============================================================================

class CallToAction(BaseModel):
    """Action actionnable pour l'utilisateur."""
    id: str
    type: str  # "acknowledge_alert", "import_invoice", "reconcile_transaction", "reorder_product"
    category: str  # "urgent", "important", "suggested"
    title: str
    description: str
    action_url: str
    action_label: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    deadline: Optional[datetime] = None
    estimated_duration: Optional[str] = None  # "2 min", "5 min", etc.


# =============================================================================
# Response Principal - Morning Brief Cockpit
# =============================================================================

class MorningBriefCockpitResponse(BaseModel):
    """
    Reponse complete du Morning Brief - toutes les donnees en un appel.

    Agrege:
    - KPIs principaux (6 metriques cles)
    - Alertes critiques (top 10)
    - Anomalies top 5
    - Previsions tresorerie 7j
    - Previsions stock critique
    - Suggestions IA actionnables
    """
    timestamp: datetime
    tenant_id: int
    tenant_name: str

    # KPIs principaux
    kpis: CockpitKPIs

    # Alertes actives
    alerts: List[CockpitAlert]
    alerts_summary: dict  # {"critical": 3, "warning": 5, "info": 2}

    # Top 5 anomalies
    top_anomalies: List[AnomalyItem]

    # Previsions
    cash_flow_forecast_7d: CashFlowForecast
    stock_depletion_forecast: List[StockForecast]

    # Suggestions IA
    ai_suggestions: List[AISuggestion]

    # Sante globale
    health_score: float  # 0-100
    health_status: str  # "healthy", "warning", "critical"


# =============================================================================
# Response Actions - Liste des CTAs
# =============================================================================

class ActionsResponse(BaseModel):
    """Liste des actions actionnables pour l'utilisateur."""
    timestamp: datetime
    total_actions: int
    urgent_count: int
    important_count: int
    suggested_count: int
    actions: List[CallToAction]


# =============================================================================
# Imports factures (workflow dropzone / corrections)
# =============================================================================


class InvoiceImportUploadRequest(BaseModel):
    filename: str
    content_base64: str
    content_type: Optional[str] = None
    supplier: Optional[str] = None
    source: Optional[str] = None  # upload, scanner, email
    invoice_date: Optional[date] = None


class InvoiceImportLine(BaseModel):
    line_id: str
    description: str
    quantity: float
    unit_price: float
    tax_rate: float | None = None
    product_id: Optional[int] = None
    status: str = "pending"  # pending | corrected | confirmed
    notes: Optional[str] = None
    invoice_date: Optional[datetime] = None
    error: Optional[str] = None


class InvoiceImportJob(BaseModel):
    job_id: str
    tenant_id: int
    filename: str
    supplier: Optional[str] = None
    status: str  # pending | ready | confirmed | canceled
    progress: float = 0.0
    errors: List[str] = Field(default_factory=list)
    lines: List[InvoiceImportLine] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    source: Optional[str] = None
    invoice_date: Optional[date] = None


class InvoiceImportStatusResponse(BaseModel):
    success: bool = True
    job: InvoiceImportJob


class InvoiceImportLineUpdateRequest(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    tax_rate: Optional[float] = None
    product_id: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    invoice_date: Optional[date] = None
    error: Optional[str] = None


class InvoiceImportActionResponse(BaseModel):
    success: bool = True
    job: InvoiceImportJob
    message: Optional[str] = None


class PriceAnomalyResolveRequest(BaseModel):
    reason: Optional[str] = None
    new_price: Optional[float] = None
    previous_price: Optional[float] = None
    notes: Optional[str] = None


class PriceAnomalyResolveResponse(BaseModel):
    success: bool = True
    product_id: int
    applied: bool
    message: str


class CreateOrderItem(BaseModel):
    product_id: int
    quantity: float
    unit_price: Optional[float] = None
    label: Optional[str] = None


class CreateOrderRequest(BaseModel):
    supplier: str
    items: List[CreateOrderItem]
    currency: str = "EUR"
    notes: Optional[str] = None


class CreateOrderResponse(BaseModel):
    success: bool = True
    order_id: str
    supplier: str
    item_count: int
    total_estimated: float


# =============================================================================
# Modèles de requête (si besoin de paramètres)
# =============================================================================

class CockpitFilters(BaseModel):
    """Filtres optionnels pour le cockpit."""
    severity_min: Optional[str] = Field(default="warning", description="Severite minimale des alertes")
    days_forecast: Optional[int] = Field(default=7, ge=1, le=30, description="Horizon de prevision en jours")
    top_anomalies_limit: Optional[int] = Field(default=5, ge=1, le=20, description="Nombre d'anomalies a afficher")


# =============================================================================
# Schémas du module Finance
# =============================================================================

class ReconciliationStats(BaseModel):
    """Statistiques de rapprochement bancaire."""
    matched_count: int = Field(..., description="Nombre de transactions rapprochées")
    pending_count: int = Field(..., description="Nombre de transactions en attente")
    unmatched_count: int = Field(..., description="Nombre de transactions non rapprochées")
    matched_percentage: float = Field(..., description="Pourcentage de rapprochement")
    pending_percentage: float = Field(..., description="Pourcentage en attente")
    unmatched_percentage: float = Field(..., description="Pourcentage non rapproché")
    total_amount_matched: float = Field(..., description="Montant total rapproché (€)")
    total_amount_pending: float = Field(..., description="Montant total en attente (€)")


class CashFlowPeriod(BaseModel):
    """Cash-flow sur une période donnée."""
    period_days: int = Field(..., description="Nombre de jours de la période")
    total_inflow: float = Field(..., description="Total des entrées (€)")
    total_outflow: float = Field(..., description="Total des sorties (€)")
    net_cashflow: float = Field(..., description="Cash-flow net (€)")
    avg_daily_inflow: float = Field(..., description="Moyenne quotidienne des entrées (€)")
    avg_daily_outflow: float = Field(..., description="Moyenne quotidienne des sorties (€)")
    current_balance: float = Field(..., description="Solde actuel (€)")


class ReconciliationSuggestion(BaseModel):
    """Suggestion de rapprochement générée par l'IA."""
    suggestion_id: str = Field(..., description="ID unique de la suggestion")
    transaction_id: int = Field(..., description="ID de la transaction bancaire")
    transaction_date: date = Field(..., description="Date de la transaction")
    transaction_amount: float = Field(..., description="Montant de la transaction (€)")
    transaction_label: str = Field(..., description="Libellé de la transaction")
    matched_invoice_ids: List[int] = Field(..., description="IDs des factures matchées")
    matched_invoices_info: List[dict] = Field(..., description="Détails des factures matchées")
    confidence: float = Field(..., ge=0, le=1, description="Niveau de confiance IA (0-1)")
    match_type: str = Field(..., description="Type de match (exact, fuzzy, multi_line, alias)")
    total_matched_amount: float = Field(..., description="Montant total des factures (€)")
    difference: float = Field(..., description="Différence transaction-factures (€)")
    explanation: str = Field(..., description="Explication du match")


class RecentTransaction(BaseModel):
    """Transaction récente pour l'overview finance."""
    id: int
    date: date
    amount: float
    label: str
    direction: str = Field(..., description="Direction: IN, OUT, TRANSFER")
    category: Optional[str] = None
    reconciled: bool = False


class FinanceOverviewResponse(BaseModel):
    """
    Réponse complète de l'overview finance.

    Agrège toutes les informations financières en un seul appel:
    - Statistiques de rapprochement bancaire
    - Cash-flow sur 30 jours
    - Top 5 suggestions de rapprochement IA
    - 5 dernières transactions
    """
    reconciliation_stats: ReconciliationStats
    cashflow_30d: CashFlowPeriod
    ai_suggestions: List[ReconciliationSuggestion] = Field(
        ..., max_length=5, description="Top 5 suggestions de rapprochement IA"
    )
    recent_transactions: List[RecentTransaction] = Field(
        ..., max_length=5, description="5 dernières transactions"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionListResponse(BaseModel):
    """Réponse paginée des transactions."""
    transactions: List[RecentTransaction]
    total: int = Field(..., description="Nombre total de transactions")
    page: int = Field(..., ge=1, description="Numéro de page actuelle")
    size: int = Field(..., ge=1, le=500, description="Taille de la page")
    pages: int = Field(..., description="Nombre total de pages")


class ApplyReconciliationRequest(BaseModel):
    """Requête pour appliquer une suggestion de rapprochement."""
    suggestion_id: str = Field(..., description="ID de la suggestion")
    transaction_id: int = Field(..., description="ID de la transaction")
    invoice_ids: List[int] = Field(..., min_length=1, description="IDs des factures à rapprocher")
    user_comment: Optional[str] = Field(None, max_length=500, description="Commentaire utilisateur")


class ApplyReconciliationResponse(BaseModel):
    """Réponse après application d'un rapprochement."""
    success: bool
    transaction_id: int
    invoice_ids: List[int]
    reconciled_at: datetime
    message: str


# =============================================================================
# Schémas du module Intelligence
# =============================================================================

class PriorityLevel(str):
    """Niveaux de priorité des recommandations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationType(str):
    """Types de recommandations IA."""
    REORDER_STOCK = "reorder_stock"
    CHANGE_SUPPLIER = "change_supplier"
    ADJUST_PRICE = "adjust_price"
    REDUCE_STOCK = "reduce_stock"
    OPTIMIZE_MARGIN = "optimize_margin"
    RESOLVE_ANOMALY = "resolve_anomaly"
    IMPROVE_CASHFLOW = "improve_cashflow"
    NEGOTIATE_TERMS = "negotiate_terms"


class ActionPayload(BaseModel):
    """Payload d'une action actionnable."""
    label: str = Field(..., description="Label de l'action")
    endpoint: str = Field(..., description="Endpoint API à appeler")
    method: str = Field(default="POST", description="Méthode HTTP")
    payload: dict = Field(..., description="Payload de l'action")
    confirmation_required: bool = Field(default=False, description="Nécessite confirmation utilisateur")
    confirmation_message: Optional[str] = Field(None, description="Message de confirmation")


class RecommendationResponse(BaseModel):
    """Recommandation IA actionnable."""
    id: str
    type: str = Field(..., description="Type de recommandation")
    priority: str = Field(..., description="Niveau de priorité")
    title: str
    description: str
    impact_estimate: str = Field(..., description="Estimation de l'impact")
    confidence: float = Field(..., ge=0, le=1, description="Niveau de confiance (0-1)")
    actions: List[ActionPayload] = Field(..., description="Actions actionnables")
    metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None


class HealthScoreResponse(BaseModel):
    """
    Score de santé global de l'entreprise.

    Le score est calculé comme une moyenne pondérée:
    - 30% score stock
    - 30% score cash
    - 20% score anomalies
    - 20% score marges
    """
    overall_score: float = Field(..., ge=0, le=10, description="Score global (0-10)")
    stock_score: float = Field(..., ge=0, le=10, description="Score stock (0-10)")
    cash_score: float = Field(..., ge=0, le=10, description="Score trésorerie (0-10)")
    anomaly_score: float = Field(..., ge=0, le=10, description="Score anomalies (0-10)")
    margin_score: float = Field(..., ge=0, le=10, description="Score marges (0-10)")
    grade: str = Field(..., description="Grade: A, B, C, D, F")
    trend: str = Field(..., description="Tendance: up, down, stable")
    details: dict = Field(default_factory=dict, description="Détails des métriques")


class IntelligenceAnomalyItem(BaseModel):
    """Item d'anomalie critique."""
    id: str
    type: str
    severity: str = Field(..., description="critical, high, medium, low")
    description: str
    impact: float
    detected_at: datetime


class ForecastItem(BaseModel):
    """Item de prévision clé."""
    type: str = Field(..., description="Type: stockout, cashflow_negative")
    date: date
    description: str
    severity: str = Field(..., description="critical, high, medium, low")
    value: float


class SupplierScoreItem(BaseModel):
    """Item de scoring fournisseur."""
    supplier_name: str
    score: float = Field(..., ge=0, le=10, description="Score (0-10)")
    grade: str = Field(..., description="Grade: A, B, C, D, F")
    trend: str = Field(..., description="up, down, stable")
    issues_count: int = Field(..., description="Nombre de problèmes détectés")


class IntelligenceOverviewResponse(BaseModel):
    """
    Vue d'ensemble de l'intelligence.

    Agrège:
    - Score de santé global
    - Top anomalies critiques
    - Prévisions clés (ruptures, cash-flow)
    - Scoring fournisseurs
    - Recommandations IA actionnables
    """
    health_score: HealthScoreResponse
    critical_anomalies: List[IntelligenceAnomalyItem]
    key_forecasts: List[ForecastItem]
    supplier_scoring: dict = Field(..., description="Top et bottom 5 fournisseurs")
    recommendations: List[RecommendationResponse]
    generated_at: datetime = Field(default_factory=datetime.now)


class ApplyRecommendationResponse(BaseModel):
    """Résultat de l'application d'une recommandation."""
    success: bool
    recommendation_id: str
    action_taken: str
    result: dict
    message: str


# =============================================================================
# Schémas du module Restaurant
# =============================================================================

class RestaurantPlatCost(BaseModel):
    """Coût d'un plat avec food cost et marge."""
    plat_id: int
    nom: str
    prix_vente_ttc: float = Field(..., description="Prix de vente TTC (€)")
    cout_matiere: float = Field(..., description="Coût matière (€)")
    food_cost_pct: float = Field(..., description="Food cost en % du prix de vente")
    marge_pct: float = Field(..., description="Marge en %")


class RestaurantIngredientAlert(BaseModel):
    """Alerte sur un ingrédient (stock bas ou rupture)."""
    ingredient_id: int
    nom: str
    stock_actuel: float
    cout_unitaire: float
    status: str = Field(..., description="rupture, bas, ok")


class RestaurantStockLocation(BaseModel):
    """Stock par localisation."""
    location: str
    valeur: float = Field(..., description="Valeur totale du stock (€)")
    count: int = Field(..., description="Nombre d'ingrédients")


class RestaurantTopPlat(BaseModel):
    """Top plat par marge."""
    plat_id: int
    nom: str
    marge_pct: float
    prix_vente_ttc: float
    cout_matiere: float


class RestaurantOverviewMetrics(BaseModel):
    """Métriques agrégées restaurant."""
    total_plats: int = Field(..., description="Nombre total de plats actifs")
    avg_food_cost_pct: float = Field(..., description="Food cost moyen (%)")
    alerts_count: int = Field(..., description="Nombre d'alertes ingrédients")
    top_plats: List[RestaurantTopPlat] = Field(..., description="Top 5 plats par marge")


class RestaurantOverviewResponse(BaseModel):
    """
    Vue d'ensemble restaurant.

    Agrège:
    - Métriques globales (total plats, food cost moyen, alertes)
    - Coûts de tous les plats avec food cost %
    - Stock par localisation
    - Alertes ingrédients (ruptures et stock bas)
    """
    success: bool = True
    metrics: RestaurantOverviewMetrics
    plat_costs: List[RestaurantPlatCost]
    stock_locations: List[RestaurantStockLocation]
    ingredient_alerts: List[RestaurantIngredientAlert]


# =============================================================================
# Schémas du module Mobile
# =============================================================================

class MobileInventoryItem(BaseModel):
    """Item d'inventaire pour l'app mobile."""
    id: int
    nom: str
    ean: Optional[str] = Field(None, description="Code-barres EAN")
    stock_actuel: float
    seuil_alerte: float
    categorie: Optional[str] = None


class MobileInventoryListResponse(BaseModel):
    """Réponse paginée de l'inventaire mobile."""
    success: bool = True
    items: List[MobileInventoryItem]
    total: int
    page: int
    page_size: int


class MobileScanRequest(BaseModel):
    """Requête de scan de code-barres."""
    ean: str = Field(..., description="Code-barres EAN à scanner")


class MobileScanResponse(BaseModel):
    """Réponse du scan de code-barres."""
    success: bool = True
    found: bool = Field(..., description="Produit trouvé ou non")
    product: Optional[MobileInventoryItem] = None
    message: Optional[str] = None


class MobileAdjustRequest(BaseModel):
    """Requête d'ajustement de stock depuis mobile."""
    product_id: int
    adjustment: float = Field(..., description="Quantité d'ajustement")
    adjustment_type: str = Field(default="delta", description="Type: delta ou absolute")
    reason: str = Field(..., description="Raison: breakage, theft, error, expiry, other")
    notes: Optional[str] = Field(None, max_length=500, description="Notes optionnelles")


class MobileAdjustResponse(BaseModel):
    """Réponse après ajustement de stock."""
    success: bool = True
    product_id: int
    product_name: str
    old_stock: float
    new_stock: float
    adjustment: float
    reason: str
    timestamp: datetime


# =============================================================================
# Operations Module - ResponseWrapper Pattern
# =============================================================================

class ResponseMeta(BaseModel):
    """Metadata pour les réponses paginées."""
    page: int = Field(default=1, ge=1, description="Numéro de page actuelle")
    per_page: int = Field(default=20, ge=1, le=100, description="Éléments par page")
    total: int = Field(default=0, ge=0, description="Nombre total d'éléments")


class BaseOperationsResponse(BaseModel):
    """Réponse de base pour tous les endpoints Operations."""
    success: bool = Field(default=True, description="Indique si la requête a réussi")
    data: dict = Field(default_factory=dict, description="Données de la réponse")
    meta: dict = Field(default_factory=dict, description="Métadonnées de pagination")


class OperationsOverviewResponse(BaseOperationsResponse):
    """
    Réponse agrégée pour /newcms/operations/overview.

    Données retournées dans 'data':
    - critical_stock: List[Dict] - Produits avec stock <= 0
    - low_stock: List[Dict] - Produits avec stock < seuil_alerte
    - recent_invoices: List[Dict] - 5 dernières factures traitées
    - price_anomalies: List[Dict] - Anomalies de prix récentes (14j)
    - pending_imports: int - Nombre d'imports en attente
    - alert_count: int - Nombre total d'alertes
    - timestamp: str - Timestamp ISO de la réponse
    """
    pass


class CatalogProxyResponse(BaseOperationsResponse):
    """
    Réponse paginée pour /newcms/operations/catalog.

    Données retournées dans 'data':
    - items: List[Dict] - Liste des produits du catalogue

    Métadonnées dans 'meta':
    - page: int
    - per_page: int
    - total: int
    """
    pass


class StockProxyResponse(BaseOperationsResponse):
    """
    Réponse paginée pour /newcms/operations/stock.

    Données retournées dans 'data':
    - items: List[Dict] - Liste des produits avec informations de stock

    Métadonnées dans 'meta':
    - page: int
    - per_page: int
    - total: int

    Filtres supportés:
    - status: "critical" (stock <= 0), "low" (stock < seuil), "ok" (stock >= seuil)
    - q: recherche textuelle sur le nom
    """
    pass


class InvoicesProxyResponse(BaseOperationsResponse):
    """
    Réponse paginée pour /newcms/operations/invoices.

    Données retournées dans 'data':
    - items: List[Dict] - Liste des factures traitées

    Métadonnées dans 'meta':
    - page: int
    - per_page: int
    - total: int

    Filtres supportés:
    - date_from: date de début (YYYY-MM-DD)
    - date_to: date de fin (YYYY-MM-DD)
    - status: (à implémenter)
    """
    pass


__all__ = [
    # Cockpit schemas
    "KPIMetric",
    "CockpitKPIs",
    "CockpitAlert",
    "AnomalyItem",
    "ForecastPoint",
    "CashFlowForecast",
    "StockForecast",
    "AISuggestion",
    "CallToAction",
    "MorningBriefCockpitResponse",
    "ActionsResponse",
    "CockpitFilters",
    # Finance schemas
    "ReconciliationStats",
    "CashFlowPeriod",
    "ReconciliationSuggestion",
    "RecentTransaction",
    "FinanceOverviewResponse",
    "TransactionListResponse",
    "ApplyReconciliationRequest",
    "ApplyReconciliationResponse",
    # Intelligence schemas
    "PriorityLevel",
    "RecommendationType",
    "ActionPayload",
    "RecommendationResponse",
    "HealthScoreResponse",
    "IntelligenceAnomalyItem",
    "ForecastItem",
    "SupplierScoreItem",
    "IntelligenceOverviewResponse",
    "ApplyRecommendationResponse",
    # Restaurant schemas
    "RestaurantPlatCost",
    "RestaurantIngredientAlert",
    "RestaurantStockLocation",
    "RestaurantTopPlat",
    "RestaurantOverviewMetrics",
    "RestaurantOverviewResponse",
    # Mobile schemas
    "MobileInventoryItem",
    "MobileInventoryListResponse",
    "MobileScanRequest",
    "MobileScanResponse",
    "MobileAdjustRequest",
    "MobileAdjustResponse",
    # Operations schemas
    "ResponseMeta",
    "BaseOperationsResponse",
    "OperationsOverviewResponse",
    "CatalogProxyResponse",
    "StockProxyResponse",
    "InvoicesProxyResponse",
]
