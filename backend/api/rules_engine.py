"""
API Router pour le moteur de règles financières.

Expose les fonctionnalités de catégorisation automatique:
- Classification de transactions
- Gestion des règles
- Feedback et apprentissage
- Détection d'anomalies
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from datetime import datetime

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.finance.rules_engine import (
    FinancialRulesEngine,
    RuleType,
    bootstrap_default_rules,
)

router = APIRouter(prefix="/rules-engine", tags=["Rules Engine"])


# ============================================================================
# SCHEMAS
# ============================================================================

class TransactionInput(BaseModel):
    """Transaction à classifier."""
    id: Optional[str] = None
    description: Optional[str] = Field(None, alias="libelle")
    amount: Optional[float] = Field(None, alias="montant")
    supplier: Optional[str] = Field(None, alias="fournisseur")
    date: Optional[str] = None
    type: Optional[str] = None  # debit, credit

    class Config:
        populate_by_name = True


class ClassificationResponse(BaseModel):
    """Résultat de classification."""
    category: str
    confidence: float
    rule_id: Optional[int] = None
    rule_name: Optional[str] = None
    method: str
    alternatives: List[Dict[str, Any]] = []
    anomalies: List[Dict[str, Any]] = []


class BatchClassificationRequest(BaseModel):
    """Requête de classification en batch."""
    transactions: List[TransactionInput]
    detect_anomalies: bool = True


class BatchClassificationResponse(BaseModel):
    """Réponse de classification batch."""
    results: List[ClassificationResponse]
    total: int
    classified: int
    unclassified: int
    with_anomalies: int


class RuleCreate(BaseModel):
    """Création d'une règle."""
    name: str
    rule_type: str  # regex, keyword, amount_range, supplier, combined
    category: str
    conditions: Dict[str, Any]
    priority: int = 0
    weight: float = 1.0


class RuleResponse(BaseModel):
    """Règle retournée."""
    id: int
    name: str
    rule_type: str
    category: str
    conditions: Dict[str, Any]
    priority: int
    weight: float
    hits: int
    accuracy: float
    active: bool


class FeedbackRequest(BaseModel):
    """Feedback sur une classification."""
    transaction_id: str
    predicted_category: str
    actual_category: str
    feedback: str  # correct, incorrect, adjusted
    rule_id: Optional[int] = None
    confidence: float = 0.0


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/classify", response_model=ClassificationResponse)
async def classify_transaction(
    transaction: TransactionInput,
    detect_anomalies: bool = Query(True, description="Détecter les anomalies"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Classifie une transaction unique.

    Le moteur applique les règles configurées pour déterminer la catégorie:
    - Regex sur description
    - Mots-clés
    - Plage de montant
    - Fournisseur

    Retourne la catégorie avec un score de confiance.
    """
    engine = FinancialRulesEngine(tenant.id)

    tx_dict = {
        "description": transaction.description or "",
        "amount": transaction.amount or 0,
        "supplier": transaction.supplier or "",
        "date": transaction.date,
        "type": transaction.type,
    }

    result = engine.classify(tx_dict, detect_anomalies=detect_anomalies)

    return ClassificationResponse(
        category=result.category,
        confidence=result.confidence,
        rule_id=result.rule_id,
        rule_name=result.rule_name,
        method=result.method,
        alternatives=[{"category": cat, "confidence": conf} for cat, conf in result.alternatives],
        anomalies=result.anomalies,
    )


@router.post("/classify/batch", response_model=BatchClassificationResponse)
async def classify_batch(
    request: BatchClassificationRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Classifie un lot de transactions.

    Optimisé pour le traitement de masse, retourne des statistiques globales
    en plus des résultats individuels.
    """
    engine = FinancialRulesEngine(tenant.id)

    results = []
    classified = 0
    with_anomalies = 0

    for tx in request.transactions:
        tx_dict = {
            "description": tx.description or "",
            "amount": tx.amount or 0,
            "supplier": tx.supplier or "",
            "date": tx.date,
            "type": tx.type,
        }

        result = engine.classify(tx_dict, detect_anomalies=request.detect_anomalies)

        results.append(ClassificationResponse(
            category=result.category,
            confidence=result.confidence,
            rule_id=result.rule_id,
            rule_name=result.rule_name,
            method=result.method,
            alternatives=[{"category": cat, "confidence": conf} for cat, conf in result.alternatives],
            anomalies=result.anomalies,
        ))

        if result.category != "Non catégorisé":
            classified += 1
        if result.anomalies:
            with_anomalies += 1

    return BatchClassificationResponse(
        results=results,
        total=len(results),
        classified=classified,
        unclassified=len(results) - classified,
        with_anomalies=with_anomalies,
    )


@router.get("/rules", response_model=List[RuleResponse])
async def list_rules(
    active_only: bool = Query(True, description="Uniquement les règles actives"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Liste toutes les règles de catégorisation.
    """
    engine = FinancialRulesEngine(tenant.id)
    rules = engine.get_rules()

    if active_only:
        rules = [r for r in rules if r.get("active", True)]

    return rules


@router.post("/rules", response_model=RuleResponse)
async def create_rule(
    rule: RuleCreate,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Crée une nouvelle règle de catégorisation.

    Types de règles supportés:
    - regex: Pattern regex sur la description
    - keyword: Mots-clés à rechercher
    - amount_range: Plage de montant (amount_min, amount_max)
    - supplier: Liste de fournisseurs
    - combined: Combinaison de plusieurs conditions
    """
    try:
        rule_type = RuleType(rule.rule_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Type de règle invalide. Valeurs acceptées: {[t.value for t in RuleType]}"
        )

    engine = FinancialRulesEngine(tenant.id)

    rule_id = engine.add_rule(
        name=rule.name,
        rule_type=rule_type,
        category=rule.category,
        conditions=rule.conditions,
        priority=rule.priority,
        weight=rule.weight,
    )

    # Récupérer la règle créée
    rules = engine.get_rules()
    created_rule = next((r for r in rules if r["id"] == rule_id), None)

    if not created_rule:
        raise HTTPException(status_code=500, detail="Erreur lors de la création")

    return created_rule


@router.post("/feedback")
async def record_feedback(
    feedback: FeedbackRequest,
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Enregistre un feedback sur une classification.

    Ce feedback est utilisé pour améliorer l'apprentissage du moteur:
    - correct: La catégorisation était correcte
    - incorrect: La catégorisation était fausse
    - adjusted: L'utilisateur a modifié la catégorie
    """
    engine = FinancialRulesEngine(tenant.id)

    engine.record_feedback(
        transaction_id=feedback.transaction_id,
        predicted_category=feedback.predicted_category,
        actual_category=feedback.actual_category,
        feedback=feedback.feedback,
        rule_id=feedback.rule_id,
        confidence=feedback.confidence,
    )

    return {"status": "ok", "message": "Feedback enregistré"}


@router.post("/bootstrap")
async def bootstrap_rules(
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Initialise les règles par défaut pour le tenant.

    Crée un ensemble de règles prédéfinies couvrant:
    - Approvisionnement (Metro, Promocash, etc.)
    - Charges locatives
    - Énergie
    - Télécom
    - Salaires
    - Charges sociales (URSSAF)
    - Impôts
    - Frais bancaires
    - Assurance
    """
    bootstrap_default_rules(tenant.id)

    engine = FinancialRulesEngine(tenant.id)
    rules = engine.get_rules()

    return {
        "status": "ok",
        "message": f"{len(rules)} règles initialisées",
        "rules_count": len(rules),
    }


@router.get("/stats")
async def get_classification_stats(
    days: int = Query(30, description="Nombre de jours d'historique"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Retourne des statistiques sur les classifications.
    """
    from core.data_repository import get_engine
    from sqlalchemy import text

    db_engine = get_engine()

    with db_engine.connect() as conn:
        # Stats par méthode
        result = conn.execute(
            text("""
                SELECT
                    method,
                    COUNT(*) as total,
                    AVG(confidence) as avg_confidence,
                    SUM(CASE WHEN feedback = 'correct' THEN 1 ELSE 0 END) as correct,
                    SUM(CASE WHEN feedback = 'incorrect' THEN 1 ELSE 0 END) as incorrect
                FROM classification_history
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY method
            """ % days),
            {"tenant_id": tenant.id}
        )

        by_method = []
        for row in result:
            by_method.append({
                "method": row.method,
                "total": row.total,
                "avg_confidence": round(row.avg_confidence or 0, 3),
                "correct": row.correct or 0,
                "incorrect": row.incorrect or 0,
                "accuracy": round((row.correct or 0) / row.total * 100, 1) if row.total > 0 else 0,
            })

        # Stats par catégorie
        result2 = conn.execute(
            text("""
                SELECT
                    actual_category,
                    COUNT(*) as count
                FROM classification_history
                WHERE tenant_id = :tenant_id
                  AND created_at >= NOW() - INTERVAL '%s days'
                  AND actual_category IS NOT NULL
                GROUP BY actual_category
                ORDER BY count DESC
                LIMIT 10
            """ % days),
            {"tenant_id": tenant.id}
        )

        by_category = [{"category": row.actual_category, "count": row.count} for row in result2]

    return {
        "period_days": days,
        "by_method": by_method,
        "top_categories": by_category,
    }


@router.get("/suggest")
async def suggest_category(
    description: str = Query(..., description="Description de la transaction"),
    amount: Optional[float] = Query(None, description="Montant"),
    supplier: Optional[str] = Query(None, description="Fournisseur"),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Suggère une catégorie pour une transaction (endpoint léger).

    Utile pour l'autocomplétion dans l'UI.
    """
    engine = FinancialRulesEngine(tenant.id)

    tx_dict = {
        "description": description,
        "amount": amount or 0,
        "supplier": supplier or "",
    }

    result = engine.classify(tx_dict, detect_anomalies=False)

    suggestions = [{"category": result.category, "confidence": result.confidence}]

    for cat, conf in result.alternatives:
        suggestions.append({"category": cat, "confidence": conf})

    return {
        "suggestions": suggestions[:5],
        "best_match": result.category,
        "confidence": result.confidence,
    }
