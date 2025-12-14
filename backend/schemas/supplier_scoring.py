"""
Schémas Pydantic pour Supplier Scoring.

Définit les structures de données pour:
- Scores fournisseurs
- Historique des scores
- Critères de scoring
- Alertes
- Statistiques et tendances
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Any, Dict, List, Optional
from datetime import datetime, date
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ScoreDimensionEnum(str, Enum):
    """Dimensions du score fournisseur."""
    PRICE_STABILITY = "price_stability"
    DELIVERY_RELIABILITY = "delivery_reliability"
    INVOICE_ACCURACY = "invoice_accuracy"
    STOCK_ACCURACY = "stock_accuracy"
    PAYMENT_TERMS = "payment_terms"
    RESPONSIVENESS = "responsiveness"
    PRODUCT_QUALITY = "product_quality"


class TrendEnum(str, Enum):
    """Tendance du score."""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UP = "up"
    DOWN = "down"


class AlertSeverityEnum(str, Enum):
    """Niveau de sévérité d'une alerte."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertTypeEnum(str, Enum):
    """Type d'alerte."""
    SCORE_DROP = "score_drop"
    DELIVERY_ISSUES = "delivery_issues"
    QUALITY_DEGRADATION = "quality_degradation"
    PRICE_SPIKE = "price_spike"


# ============================================================================
# MODELS - Score & Metrics
# ============================================================================

class DimensionScore(BaseModel):
    """Score d'une dimension spécifique."""
    dimension: ScoreDimensionEnum
    score: float = Field(..., ge=0, le=100, description="Score de 0 à 100")
    weight: float = Field(..., ge=0, le=1, description="Poids de la dimension (0-1)")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Métriques détaillées")


class SupplierScore(BaseModel):
    """Score complet d'un fournisseur."""
    supplier_id: Optional[int] = Field(None, description="ID du fournisseur")
    supplier_name: str = Field(..., min_length=1, description="Nom du fournisseur")
    overall_score: float = Field(..., ge=0, le=100, description="Score global (0-100)")
    grade: str = Field(..., description="Note de A à F")
    delivery_score: float = Field(..., ge=0, le=100)
    quality_score: float = Field(..., ge=0, le=100)
    price_score: float = Field(..., ge=0, le=100)
    reliability_score: float = Field(..., ge=0, le=100)
    trend: TrendEnum = Field(..., description="Tendance du score")
    last_updated: datetime = Field(..., description="Date de dernière mise à jour")
    dimensions: Dict[str, float] = Field(default_factory=dict, description="Scores par dimension")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Métriques détaillées")

    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v: str) -> str:
        """Valide que le grade est A, B, C, D ou F."""
        if v not in ['A', 'B', 'C', 'D', 'F']:
            raise ValueError('Grade must be A, B, C, D, or F')
        return v


class ScoreHistoryItem(BaseModel):
    """Élément de l'historique des scores."""
    date: datetime = Field(..., description="Date du score")
    score: float = Field(..., ge=0, le=100, description="Score global")
    grade: str = Field(..., description="Note A-F")
    breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Détail des scores par dimension"
    )


class ScoreHistory(BaseModel):
    """Historique complet des scores d'un fournisseur."""
    supplier_id: Optional[int] = None
    supplier_name: str
    history: List[ScoreHistoryItem] = Field(default_factory=list)
    trend_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Analyse de tendance (pente, variations, etc.)"
    )


# ============================================================================
# MODELS - Scoring Criteria
# ============================================================================

class ScoringCriterion(BaseModel):
    """Critère de scoring configurable."""
    criterion_id: str = Field(..., description="Identifiant du critère")
    name: str = Field(..., description="Nom du critère")
    weight: float = Field(..., ge=0, le=1, description="Poids (0-1)")
    description: str = Field(..., description="Description du critère")
    enabled: bool = Field(default=True, description="Critère activé/désactivé")


class ScoringCriteriaList(BaseModel):
    """Liste des critères de scoring."""
    criteria: List[ScoringCriterion] = Field(default_factory=list)
    total_weight: float = Field(default=1.0, description="Poids total (doit être 1.0)")

    @field_validator('total_weight')
    @classmethod
    def validate_total_weight(cls, v: float) -> float:
        """Valide que le poids total est proche de 1.0."""
        if abs(v - 1.0) > 0.01:
            raise ValueError('Total weight must be approximately 1.0')
        return v


class UpdateScoringCriteriaRequest(BaseModel):
    """Requête de mise à jour des pondérations."""
    weights: Dict[str, float] = Field(
        ...,
        description="Map criterion_id -> weight"
    )

    @field_validator('weights')
    @classmethod
    def validate_weights(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Valide que tous les poids sont entre 0 et 1 et que leur somme fait ~1.0."""
        for criterion_id, weight in v.items():
            if not 0 <= weight <= 1:
                raise ValueError(f'Weight for {criterion_id} must be between 0 and 1')

        total = sum(v.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f'Total weight must be approximately 1.0, got {total}')

        return v


# ============================================================================
# MODELS - Alerts
# ============================================================================

class SupplierAlert(BaseModel):
    """Alerte sur un score fournisseur dégradé."""
    alert_id: str = Field(..., description="ID de l'alerte")
    supplier_id: Optional[int] = None
    supplier_name: str = Field(..., description="Nom du fournisseur")
    alert_type: AlertTypeEnum = Field(..., description="Type d'alerte")
    message: str = Field(..., description="Message d'alerte")
    severity: AlertSeverityEnum = Field(..., description="Niveau de sévérité")
    created_at: datetime = Field(..., description="Date de création")
    acknowledged: bool = Field(default=False, description="Alerte acquittée")
    details: Optional[Dict[str, Any]] = Field(None, description="Détails supplémentaires")


class AlertsList(BaseModel):
    """Liste des alertes."""
    alerts: List[SupplierAlert] = Field(default_factory=list)
    total_count: int = Field(default=0, description="Nombre total d'alertes")
    unacknowledged_count: int = Field(default=0, description="Alertes non acquittées")


# ============================================================================
# MODELS - Overview & Rankings
# ============================================================================

class SupplierOverview(BaseModel):
    """Vue d'ensemble des scores fournisseurs."""
    total_suppliers: int = Field(..., description="Nombre total de fournisseurs")
    average_score: float = Field(..., ge=0, le=100, description="Score moyen")
    score_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="Distribution des grades (A:10, B:5, etc.)"
    )
    top_suppliers: List[SupplierScore] = Field(
        default_factory=list,
        description="Top 5 fournisseurs"
    )
    bottom_suppliers: List[SupplierScore] = Field(
        default_factory=list,
        description="5 fournisseurs à améliorer"
    )
    trends: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tendances globales"
    )
    alerts_summary: Dict[str, int] = Field(
        default_factory=dict,
        description="Résumé des alertes par type"
    )


class SupplierRankingItem(BaseModel):
    """Élément du classement fournisseurs."""
    rank: int = Field(..., ge=1, description="Position dans le classement")
    supplier_id: Optional[int] = None
    supplier_name: str
    score: float = Field(..., ge=0, le=100)
    grade: str
    dimensions: Dict[str, float] = Field(default_factory=dict)
    last_updated: Optional[datetime] = None
    trend: Optional[TrendEnum] = None


class SuppliersList(BaseModel):
    """Liste paginée des fournisseurs avec scores."""
    suppliers: List[SupplierRankingItem] = Field(default_factory=list)
    total_count: int = Field(default=0)
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    total_pages: int = Field(default=0, ge=0)  # Permet 0 si aucune donnée


# ============================================================================
# MODELS - Comparison
# ============================================================================

class SupplierComparisonRequest(BaseModel):
    """Requête de comparaison fournisseurs."""
    suppliers: List[str] = Field(..., min_length=2, max_length=10)


class SupplierComparisonItem(BaseModel):
    """Données d'un fournisseur dans la comparaison."""
    supplier_name: str
    overall_score: float
    grade: str
    dimensions: Dict[str, float] = Field(default_factory=dict)
    rank_overall: int = Field(..., ge=1)
    ranks_by_dimension: Dict[str, int] = Field(default_factory=dict)


class SupplierComparisonResponse(BaseModel):
    """Résultat de comparaison."""
    suppliers: List[SupplierComparisonItem] = Field(default_factory=list)
    best_overall: Optional[str] = None
    best_by_dimension: Dict[str, str] = Field(
        default_factory=dict,
        description="Meilleur fournisseur par dimension"
    )
    comparison_matrix: Optional[Dict[str, Any]] = Field(
        None,
        description="Matrice de comparaison détaillée"
    )


# ============================================================================
# MODELS - Actions & Recording
# ============================================================================

class DeliveryRecordRequest(BaseModel):
    """Enregistrement d'une livraison."""
    supplier_name: str = Field(..., min_length=1)
    expected_date: date
    actual_date: date
    invoice_id: Optional[int] = None


class InvoiceIssueRequest(BaseModel):
    """Enregistrement d'un problème de facture."""
    supplier_name: str = Field(..., min_length=1)
    issue_type: str = Field(
        ...,
        description="Type: price_error, quantity_error, missing_item, duplicate"
    )
    severity: str = Field(..., description="Severité: low, medium, high")
    invoice_id: Optional[int] = None
    description: Optional[str] = Field(None, description="Description du problème")

    @field_validator('issue_type')
    @classmethod
    def validate_issue_type(cls, v: str) -> str:
        """Valide le type de problème."""
        valid_types = ["price_error", "quantity_error", "missing_item", "duplicate"]
        if v not in valid_types:
            raise ValueError(f'issue_type must be one of {valid_types}')
        return v

    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v: str) -> str:
        """Valide la sévérité."""
        valid_severities = ["low", "medium", "high"]
        if v not in valid_severities:
            raise ValueError(f'severity must be one of {valid_severities}')
        return v


class RecalculateScoresRequest(BaseModel):
    """Requête de recalcul des scores."""
    supplier_names: Optional[List[str]] = Field(
        None,
        description="Liste des fournisseurs (None = tous)"
    )
    period_days: int = Field(
        default=90,
        ge=7,
        le=365,
        description="Période d'analyse en jours"
    )
    force: bool = Field(
        default=False,
        description="Forcer le recalcul même si récent"
    )


class RecalculateScoresResponse(BaseModel):
    """Résultat du recalcul des scores."""
    success: bool
    suppliers_processed: int = Field(default=0)
    suppliers_failed: int = Field(default=0)
    duration_seconds: float = Field(default=0.0)
    errors: List[str] = Field(default_factory=list)


# ============================================================================
# MODELS - Details
# ============================================================================

class SupplierDetails(BaseModel):
    """Détails complets d'un fournisseur."""
    supplier_id: Optional[int] = None
    supplier_name: str
    current_score: SupplierScore
    history: List[ScoreHistoryItem] = Field(default_factory=list)
    recent_deliveries: List[Dict[str, Any]] = Field(default_factory=list)
    recent_issues: List[Dict[str, Any]] = Field(default_factory=list)
    alerts: List[SupplierAlert] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistiques additionnelles"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Recommandations d'amélioration"
    )
