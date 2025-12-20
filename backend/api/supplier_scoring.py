"""
API Router pour le scoring des fournisseurs.

Expose les fonctionnalités de notation des fournisseurs:
- Vue d'ensemble et statistiques
- Scores individuels et classements
- Historique et tendances
- Critères de scoring configurables
- Alertes et notifications
- Enregistrement des événements (livraisons, incidents)
- Recalcul des scores

Toutes les réponses utilisent le format ResponseWrapper standardisé.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Any, Dict, List, Optional
from datetime import datetime, date, timedelta
import logging

from backend.dependencies.tenant import Tenant, get_current_tenant, get_current_tenant_or_default
from backend.middleware.response_wrapper import build_success_response, build_error_response
from backend.schemas.supplier_scoring import (
    SupplierScore,
    SupplierRankingItem,
    SuppliersList,
    SupplierOverview,
    ScoreHistory,
    ScoreHistoryItem,
    ScoringCriterion,
    ScoringCriteriaList,
    UpdateScoringCriteriaRequest,
    SupplierAlert,
    AlertsList,
    DeliveryRecordRequest,
    InvoiceIssueRequest,
    RecalculateScoresRequest,
    RecalculateScoresResponse,
    SupplierComparisonRequest,
    SupplierComparisonResponse,
    SupplierDetails,
    TrendEnum,
    AlertSeverityEnum,
    AlertTypeEnum,
)

from core.finance.supplier_scoring import (
    SupplierScoreCalculator,
    ScoreDimension,
)

router = APIRouter(prefix="/supplier-scoring", tags=["Supplier Scoring"])
logger = logging.getLogger(__name__)


# ============================================================================
# POINT D'ENTRÉE 1 : GET /supplier-scoring/overview
# ============================================================================

@router.get("/overview")
async def get_suppliers_overview(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Vue d'ensemble des scores fournisseurs.

    Retourne:
    - Nombre total de fournisseurs
    - Score moyen
    - Distribution des grades (A, B, C, D, F)
    - Top 5 fournisseurs
    - 5 fournisseurs à améliorer
    - Tendances globales
    - Résumé des alertes

    Format de réponse: ResponseWrapper avec SupplierOverview dans data.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)

        # Récupérer tous les classements
        all_suppliers_ranking = calculator.get_all_suppliers_ranking()

        if not all_suppliers_ranking:
            # Retourner des données mockées si aucun fournisseur
            overview = SupplierOverview(
                total_suppliers=0,
                average_score=0.0,
                score_distribution={"A": 0, "B": 0, "C": 0, "D": 0, "F": 0},
                top_suppliers=[],
                bottom_suppliers=[],
                trends={"message": "Aucune donnée disponible"},
                alerts_summary={"info": 0, "warning": 0, "critical": 0},
            )
            return build_success_response(overview.model_dump())

        # Calculer les statistiques
        total_suppliers = len(all_suppliers_ranking)
        average_score = sum(s["score"] for s in all_suppliers_ranking) / total_suppliers

        # Distribution des grades
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for supplier in all_suppliers_ranking:
            grade = supplier["grade"]
            if grade in grade_distribution:
                grade_distribution[grade] += 1

        # Top 5 et Bottom 5
        top_5 = all_suppliers_ranking[:5]
        bottom_5 = all_suppliers_ranking[-5:]

        # Convertir en SupplierScore
        def to_supplier_score(item: Dict[str, Any], rank: int) -> SupplierScore:
            dims = item.get("dimensions", {})
            return SupplierScore(
                supplier_id=item.get("supplier_id"),
                supplier_name=item["supplier_name"],
                overall_score=item["score"],
                grade=item["grade"],
                delivery_score=dims.get("delivery_reliability", 80.0),
                quality_score=dims.get("product_quality", 80.0),
                price_score=dims.get("price_stability", 80.0),
                reliability_score=dims.get("invoice_accuracy", 80.0),
                trend=TrendEnum.STABLE,
                last_updated=datetime.fromisoformat(item["last_updated"]) if item.get("last_updated") else datetime.utcnow(),
                dimensions=dims,
                metrics={},
            )

        top_suppliers = [to_supplier_score(s, i+1) for i, s in enumerate(top_5)]
        bottom_suppliers = [to_supplier_score(s, total_suppliers-len(bottom_5)+i+1) for i, s in enumerate(bottom_5)]

        # Alertes mockées (à implémenter avec vraie logique)
        alerts_summary = {
            "score_drop": 2,
            "delivery_issues": 1,
            "quality_degradation": 0,
            "price_spike": 3,
        }

        overview = SupplierOverview(
            total_suppliers=total_suppliers,
            average_score=round(average_score, 1),
            score_distribution=grade_distribution,
            top_suppliers=top_suppliers,
            bottom_suppliers=bottom_suppliers,
            trends={
                "overall_trend": "stable",
                "improving_count": sum(1 for s in all_suppliers_ranking if s.get("trend") == "improving"),
                "declining_count": sum(1 for s in all_suppliers_ranking if s.get("trend") == "declining"),
            },
            alerts_summary=alerts_summary,
        )

        return build_success_response(
            overview.model_dump(),
            meta={"generated_at": datetime.utcnow().isoformat()}
        )

    except Exception as e:
        logger.error(f"Error in get_suppliers_overview: {e}", exc_info=True)
        return build_error_response(
            code="OVERVIEW_ERROR",
            message=f"Erreur lors de la récupération de la vue d'ensemble: {str(e)}",
            suggestion="Vérifiez les logs serveur"
        )


# ============================================================================
# POINT D'ENTRÉE 2 : GET /supplier-scoring/suppliers
# ============================================================================

@router.get("/suppliers")
async def get_suppliers_list(
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    sort_by: str = Query("score", description="Tri: score, name, grade"),
    order: str = Query("desc", description="Ordre: asc, desc"),
    min_score: Optional[float] = Query(None, ge=0, le=100, description="Score minimum"),
    grade_filter: Optional[str] = Query(None, description="Filtrer par grade (A, B, C, D, F)"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Liste paginée des fournisseurs avec scores.

    Paramètres:
    - page: Numéro de page (défaut: 1)
    - per_page: Résultats par page (défaut: 20, max: 100)
    - sort_by: Tri par score, name ou grade (défaut: score)
    - order: Ordre asc ou desc (défaut: desc)
    - min_score: Score minimum (optionnel)
    - grade_filter: Filtrer par grade A/B/C/D/F (optionnel)

    Format de réponse: ResponseWrapper avec SuppliersList dans data.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)
        all_suppliers = calculator.get_all_suppliers_ranking()

        # Filtrage
        filtered = all_suppliers
        if min_score is not None:
            filtered = [s for s in filtered if s["score"] >= min_score]
        if grade_filter:
            filtered = [s for s in filtered if s["grade"] == grade_filter.upper()]

        # Tri
        reverse = (order.lower() == "desc")
        if sort_by == "name":
            filtered = sorted(filtered, key=lambda x: x["supplier_name"], reverse=reverse)
        elif sort_by == "grade":
            grade_order = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}
            filtered = sorted(filtered, key=lambda x: grade_order.get(x["grade"], 0), reverse=reverse)
        else:  # score
            filtered = sorted(filtered, key=lambda x: x["score"], reverse=reverse)

        # Pagination
        total_count = len(filtered)
        total_pages = (total_count + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_suppliers = filtered[start_idx:end_idx]

        # Convertir en SupplierRankingItem
        ranking_items = []
        for idx, supplier in enumerate(page_suppliers):
            dims = supplier.get("dimensions", {})
            ranking_items.append(SupplierRankingItem(
                rank=start_idx + idx + 1,
                supplier_id=supplier.get("supplier_id"),
                supplier_name=supplier["supplier_name"],
                score=supplier["score"],
                grade=supplier["grade"],
                dimensions=dims,
                last_updated=datetime.fromisoformat(supplier["last_updated"]) if supplier.get("last_updated") else None,
                trend=TrendEnum.STABLE,
            ))

        suppliers_list = SuppliersList(
            suppliers=ranking_items,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )

        return build_success_response(
            suppliers_list.model_dump(),
            meta={
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_pages": total_pages,
                    "total_count": total_count,
                }
            }
        )

    except Exception as e:
        logger.error(f"Error in get_suppliers_list: {e}", exc_info=True)
        return build_error_response(
            code="LIST_ERROR",
            message=f"Erreur lors de la récupération de la liste: {str(e)}",
            suggestion="Vérifiez les paramètres de pagination"
        )


# ============================================================================
# POINT D'ENTRÉE 3 : GET /supplier-scoring/suppliers/{supplier_id}
# ============================================================================

@router.get("/suppliers/{supplier_id}")
async def get_supplier_details(
    supplier_id: int = Path(..., description="ID du fournisseur"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Détails complets d'un fournisseur.

    Retourne:
    - Score actuel avec toutes les dimensions
    - Historique des scores (10 dernières entrées)
    - Livraisons récentes (10 dernières)
    - Incidents récents (10 derniers)
    - Alertes actives
    - Statistiques additionnelles
    - Recommandations d'amélioration

    Format de réponse: ResponseWrapper avec SupplierDetails dans data.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)

        # Trouver le fournisseur par ID (mockée pour l'instant)
        # En production, récupérer le nom depuis la DB
        supplier_name = f"Supplier_{supplier_id}"  # Mockée

        # Calculer le score actuel
        score_obj = calculator.calculate_score(
            supplier_name=supplier_name,
            supplier_id=supplier_id,
            period_days=90,
        )

        # Convertir en SupplierScore
        dims = score_obj.dimensions
        current_score = SupplierScore(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            overall_score=score_obj.overall_score,
            grade=score_obj.grade,
            delivery_score=dims.get(ScoreDimension.DELIVERY_RELIABILITY, 80.0),
            quality_score=dims.get(ScoreDimension.PRODUCT_QUALITY, 80.0),
            price_score=dims.get(ScoreDimension.PRICE_STABILITY, 80.0),
            reliability_score=dims.get(ScoreDimension.INVOICE_ACCURACY, 80.0),
            trend=TrendEnum(score_obj.trend) if score_obj.trend in ["improving", "stable", "declining"] else TrendEnum.STABLE,
            last_updated=score_obj.last_updated,
            dimensions={k.value: v for k, v in dims.items()},
            metrics=score_obj.metrics,
        )

        # Historique
        history = [
            ScoreHistoryItem(
                date=datetime.fromisoformat(h["date"]) if h.get("date") else datetime.utcnow(),
                score=h["score"],
                grade=h["grade"],
                breakdown={}
            )
            for h in score_obj.history
        ]

        # Données mockées pour les autres sections
        recent_deliveries = [
            {
                "delivery_id": i,
                "expected_date": (datetime.utcnow() - timedelta(days=i*7)).date().isoformat(),
                "actual_date": (datetime.utcnow() - timedelta(days=i*7+1)).date().isoformat(),
                "delay_days": 1,
                "on_time": False,
            }
            for i in range(1, 6)
        ]

        recent_issues = [
            {
                "issue_id": i,
                "invoice_id": 1000 + i,
                "issue_type": "price_error",
                "severity": "low",
                "created_at": (datetime.utcnow() - timedelta(days=i*5)).isoformat(),
            }
            for i in range(1, 4)
        ]

        alerts = [
            SupplierAlert(
                alert_id=f"alert_{i}",
                supplier_id=supplier_id,
                supplier_name=supplier_name,
                alert_type=AlertTypeEnum.DELIVERY_ISSUES,
                message=f"Retards de livraison fréquents détectés",
                severity=AlertSeverityEnum.WARNING,
                created_at=datetime.utcnow() - timedelta(days=i),
                acknowledged=False,
            )
            for i in range(2)
        ]

        # Recommandations basées sur les scores
        recommendations = []
        if current_score.delivery_score < 70:
            recommendations.append("Améliorer la ponctualité des livraisons")
        if current_score.price_score < 70:
            recommendations.append("Stabiliser les prix pratiqués")
        if current_score.quality_score < 70:
            recommendations.append("Renforcer le contrôle qualité")

        details = SupplierDetails(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            current_score=current_score,
            history=history,
            recent_deliveries=recent_deliveries,
            recent_issues=recent_issues,
            alerts=alerts,
            statistics={
                "total_orders": 156,
                "total_invoices": 234,
                "average_order_value": 1250.50,
                "partnership_duration_days": 365,
            },
            recommendations=recommendations,
        )

        return build_success_response(details.model_dump())

    except Exception as e:
        logger.error(f"Error in get_supplier_details: {e}", exc_info=True)
        return build_error_response(
            code="DETAILS_ERROR",
            message=f"Erreur lors de la récupération des détails: {str(e)}",
            suggestion="Vérifiez que le fournisseur existe"
        )


# ============================================================================
# POINT D'ENTRÉE 4 : GET /supplier-scoring/suppliers/{supplier_id}/history
# ============================================================================

@router.get("/suppliers/{supplier_id}/history")
async def get_supplier_history(
    supplier_id: int = Path(..., description="ID du fournisseur"),
    limit: int = Query(20, ge=1, le=100, description="Nombre d'entrées"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Historique des scores d'un fournisseur.

    Retourne:
    - Liste chronologique des scores
    - Analyse de tendance (pente, variance)
    - Évolution par dimension

    Format de réponse: ResponseWrapper avec ScoreHistory dans data.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)

        # Mockée: récupérer le nom du fournisseur
        supplier_name = f"Supplier_{supplier_id}"

        # Récupérer l'historique
        history_data = calculator._get_score_history(supplier_name, limit=limit)

        history_items = [
            ScoreHistoryItem(
                date=datetime.fromisoformat(h["date"]) if h.get("date") else datetime.utcnow(),
                score=h["score"],
                grade=h["grade"],
                breakdown={},
            )
            for h in history_data
        ]

        # Analyse de tendance
        if len(history_items) >= 2:
            scores = [h.score for h in history_items]
            avg_score = sum(scores) / len(scores)
            recent_avg = sum(scores[:min(5, len(scores))]) / min(5, len(scores))
            trend_direction = "improving" if recent_avg > avg_score else "declining" if recent_avg < avg_score else "stable"

            trend_analysis = {
                "direction": trend_direction,
                "average_score": round(avg_score, 1),
                "recent_average": round(recent_avg, 1),
                "variation": round(recent_avg - avg_score, 1),
            }
        else:
            trend_analysis = {"direction": "stable", "note": "Données insuffisantes"}

        score_history = ScoreHistory(
            supplier_id=supplier_id,
            supplier_name=supplier_name,
            history=history_items,
            trend_analysis=trend_analysis,
        )

        return build_success_response(score_history.model_dump())

    except Exception as e:
        logger.error(f"Error in get_supplier_history: {e}", exc_info=True)
        return build_error_response(
            code="HISTORY_ERROR",
            message=f"Erreur lors de la récupération de l'historique: {str(e)}",
            suggestion="Vérifiez que le fournisseur existe"
        )


# ============================================================================
# POINT D'ENTRÉE 5 : GET /supplier-scoring/criteria
# ============================================================================

@router.get("/criteria")
async def get_scoring_criteria() -> Dict[str, Any]:
    """
    Critères de scoring configurables.

    Retourne la liste des dimensions de scoring avec:
    - Nom et description
    - Poids actuel
    - État (activé/désactivé)

    Format de réponse: ResponseWrapper avec ScoringCriteriaList dans data.
    """
    try:
        criteria = [
            ScoringCriterion(
                criterion_id="price_stability",
                name="Stabilité des prix",
                weight=0.25,
                description="Volatilité et tendance des prix pratiqués",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="delivery_reliability",
                name="Fiabilité livraisons",
                weight=0.20,
                description="Ponctualité et respect des dates de livraison",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="invoice_accuracy",
                name="Exactitude factures",
                weight=0.15,
                description="Taux d'erreurs sur les factures",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="stock_accuracy",
                name="Exactitude stock",
                weight=0.15,
                description="Écarts entre quantités commandées et reçues",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="payment_terms",
                name="Conditions paiement",
                weight=0.10,
                description="Flexibilité des délais de paiement",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="responsiveness",
                name="Réactivité",
                weight=0.10,
                description="Rapidité de réponse aux demandes",
                enabled=True,
            ),
            ScoringCriterion(
                criterion_id="product_quality",
                name="Qualité produits",
                weight=0.05,
                description="Qualité générale des produits livrés",
                enabled=True,
            ),
        ]

        criteria_list = ScoringCriteriaList(
            criteria=criteria,
            total_weight=1.0,
        )

        return build_success_response(criteria_list.model_dump())

    except Exception as e:
        logger.error(f"Error in get_scoring_criteria: {e}", exc_info=True)
        return build_error_response(
            code="CRITERIA_ERROR",
            message=f"Erreur lors de la récupération des critères: {str(e)}",
        )


# ============================================================================
# POINT D'ENTRÉE 6 : PUT /supplier-scoring/criteria
# ============================================================================

@router.put("/criteria")
async def update_scoring_criteria(
    request: UpdateScoringCriteriaRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Mettre à jour les pondérations des critères de scoring.

    Corps de requête:
    {
        "weights": {
            "price_stability": 0.30,
            "delivery_reliability": 0.25,
            "invoice_accuracy": 0.15,
            "stock_accuracy": 0.10,
            "payment_terms": 0.10,
            "responsiveness": 0.05,
            "product_quality": 0.05
        }
    }

    La somme des poids doit être égale à 1.0 (±0.01).

    Format de réponse: ResponseWrapper avec les nouveaux critères dans data.
    """
    try:
        # Validation déjà faite par Pydantic
        # Ici on sauvegarderait normalement dans la DB
        # Pour l'instant, on retourne juste les nouveaux critères

        updated_criteria = []
        criterion_names = {
            "price_stability": "Stabilité des prix",
            "delivery_reliability": "Fiabilité livraisons",
            "invoice_accuracy": "Exactitude factures",
            "stock_accuracy": "Exactitude stock",
            "payment_terms": "Conditions paiement",
            "responsiveness": "Réactivité",
            "product_quality": "Qualité produits",
        }

        criterion_descriptions = {
            "price_stability": "Volatilité et tendance des prix pratiqués",
            "delivery_reliability": "Ponctualité et respect des dates de livraison",
            "invoice_accuracy": "Taux d'erreurs sur les factures",
            "stock_accuracy": "Écarts entre quantités commandées et reçues",
            "payment_terms": "Flexibilité des délais de paiement",
            "responsiveness": "Rapidité de réponse aux demandes",
            "product_quality": "Qualité générale des produits livrés",
        }

        for criterion_id, weight in request.weights.items():
            updated_criteria.append(ScoringCriterion(
                criterion_id=criterion_id,
                name=criterion_names.get(criterion_id, criterion_id),
                weight=weight,
                description=criterion_descriptions.get(criterion_id, ""),
                enabled=True,
            ))

        criteria_list = ScoringCriteriaList(
            criteria=updated_criteria,
            total_weight=sum(request.weights.values()),
        )

        logger.info(f"Tenant {tenant.id} updated scoring criteria: {request.weights}")

        return build_success_response(
            criteria_list.model_dump(),
            meta={"message": "Pondérations mises à jour avec succès"}
        )

    except Exception as e:
        logger.error(f"Error in update_scoring_criteria: {e}", exc_info=True)
        return build_error_response(
            code="UPDATE_ERROR",
            message=f"Erreur lors de la mise à jour: {str(e)}",
            suggestion="Vérifiez que la somme des poids est égale à 1.0"
        )


# ============================================================================
# POINT D'ENTRÉE 7 : GET /supplier-scoring/alerts
# ============================================================================

@router.get("/alerts")
async def get_supplier_alerts(
    severity: Optional[str] = Query(None, description="Filtrer par sévérité: info, warning, critical"),
    acknowledged: Optional[bool] = Query(None, description="Filtrer par état d'acquittement"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum d'alertes"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Alertes sur les scores fournisseurs dégradés.

    Retourne:
    - Liste des alertes actives
    - Nombre total et par type
    - Alertes non acquittées

    Paramètres:
    - severity: Filtrer par sévérité (info, warning, critical)
    - acknowledged: Filtrer par état d'acquittement
    - limit: Nombre max d'alertes (défaut: 50)

    Format de réponse: ResponseWrapper avec AlertsList dans data.
    """
    try:
        # Données mockées pour l'instant
        # En production, récupérer depuis la DB
        all_alerts = [
            SupplierAlert(
                alert_id=f"alert_001",
                supplier_id=101,
                supplier_name="Fournisseur Alpha",
                alert_type=AlertTypeEnum.SCORE_DROP,
                message="Score global en baisse de 15 points ce mois",
                severity=AlertSeverityEnum.CRITICAL,
                created_at=datetime.utcnow() - timedelta(days=1),
                acknowledged=False,
                details={"previous_score": 85.0, "current_score": 70.0},
            ),
            SupplierAlert(
                alert_id=f"alert_002",
                supplier_id=102,
                supplier_name="Fournisseur Beta",
                alert_type=AlertTypeEnum.DELIVERY_ISSUES,
                message="Retards répétés sur les livraisons (5 sur 7 dernières)",
                severity=AlertSeverityEnum.WARNING,
                created_at=datetime.utcnow() - timedelta(days=2),
                acknowledged=False,
                details={"late_deliveries": 5, "total_deliveries": 7},
            ),
            SupplierAlert(
                alert_id=f"alert_003",
                supplier_id=103,
                supplier_name="Fournisseur Gamma",
                alert_type=AlertTypeEnum.PRICE_SPIKE,
                message="Augmentation de prix de 12% détectée",
                severity=AlertSeverityEnum.WARNING,
                created_at=datetime.utcnow() - timedelta(days=5),
                acknowledged=True,
                details={"price_increase_pct": 12.5},
            ),
            SupplierAlert(
                alert_id=f"alert_004",
                supplier_id=104,
                supplier_name="Fournisseur Delta",
                alert_type=AlertTypeEnum.QUALITY_DEGRADATION,
                message="Augmentation des erreurs de factures",
                severity=AlertSeverityEnum.INFO,
                created_at=datetime.utcnow() - timedelta(days=7),
                acknowledged=False,
                details={"error_rate_increase": 3.2},
            ),
        ]

        # Filtrage
        filtered_alerts = all_alerts
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
        if acknowledged is not None:
            filtered_alerts = [a for a in filtered_alerts if a.acknowledged == acknowledged]

        # Limiter
        filtered_alerts = filtered_alerts[:limit]

        # Compter
        total_count = len(filtered_alerts)
        unacknowledged_count = sum(1 for a in filtered_alerts if not a.acknowledged)

        alerts_list = AlertsList(
            alerts=filtered_alerts,
            total_count=total_count,
            unacknowledged_count=unacknowledged_count,
        )

        return build_success_response(alerts_list.model_dump())

    except Exception as e:
        logger.error(f"Error in get_supplier_alerts: {e}", exc_info=True)
        return build_error_response(
            code="ALERTS_ERROR",
            message=f"Erreur lors de la récupération des alertes: {str(e)}",
        )


# ============================================================================
# POINT D'ENTRÉE 7.1 : POST /supplier-scoring/alerts/{alert_id}/acknowledge
# ============================================================================

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_supplier_alert(
    alert_id: str = Path(..., description="ID de l'alerte à acquitter"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Acquitter une alerte fournisseur.

    Marque l'alerte comme acquittée par l'utilisateur.
    En production, ceci met à jour le statut dans la base de données.

    Format de réponse: ResponseWrapper avec les détails de l'acquittement.
    """
    try:
        # En production, mettre à jour la DB:
        # UPDATE supplier_alerts
        # SET acknowledged = true, acknowledged_at = NOW(), acknowledged_by = user_id
        # WHERE alert_id = alert_id AND tenant_id = tenant.id

        logger.info(f"Tenant {tenant.id} acknowledged alert {alert_id}")

        return build_success_response(
            {
                "alert_id": alert_id,
                "acknowledged": True,
                "acknowledged_at": datetime.utcnow().isoformat(),
            },
            meta={"message": "Alerte acquittée avec succès"}
        )

    except Exception as e:
        logger.error(f"Error in acknowledge_supplier_alert: {e}", exc_info=True)
        return build_error_response(
            code="ACKNOWLEDGE_ERROR",
            message=f"Erreur lors de l'acquittement de l'alerte: {str(e)}",
            suggestion="Vérifiez que l'alerte existe"
        )


# ============================================================================
# POINT D'ENTRÉE 8 : POST /supplier-scoring/recalculate
# ============================================================================

@router.post("/recalculate")
async def recalculate_supplier_scores(
    request: RecalculateScoresRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Recalculer tous les scores fournisseurs.

    Corps de requête:
    {
        "supplier_names": ["Fournisseur A", "Fournisseur B"],  // Optionnel (null = tous)
        "period_days": 90,  // Période d'analyse
        "force": false  // Forcer le recalcul même si récent
    }

    Format de réponse: ResponseWrapper avec RecalculateScoresResponse dans data.
    """
    try:
        import time
        start_time = time.time()

        calculator = SupplierScoreCalculator(tenant.id)

        # Déterminer quels fournisseurs recalculer
        if request.supplier_names:
            suppliers_to_process = request.supplier_names
        else:
            # Récupérer tous les fournisseurs
            all_suppliers = calculator.get_all_suppliers_ranking()
            suppliers_to_process = [s["supplier_name"] for s in all_suppliers]

        # Recalculer
        processed = 0
        failed = 0
        errors = []

        for supplier_name in suppliers_to_process:
            try:
                calculator.calculate_score(
                    supplier_name=supplier_name,
                    period_days=request.period_days,
                )
                processed += 1
            except Exception as e:
                failed += 1
                errors.append(f"{supplier_name}: {str(e)}")
                logger.error(f"Failed to calculate score for {supplier_name}: {e}")

        duration = time.time() - start_time

        response = RecalculateScoresResponse(
            success=(failed == 0),
            suppliers_processed=processed,
            suppliers_failed=failed,
            duration_seconds=round(duration, 2),
            errors=errors,
        )

        logger.info(
            f"Tenant {tenant.id} recalculated scores: "
            f"{processed} processed, {failed} failed in {duration:.2f}s"
        )

        return build_success_response(
            response.model_dump(),
            meta={"message": f"Recalcul terminé: {processed} fournisseurs traités"}
        )

    except Exception as e:
        logger.error(f"Error in recalculate_supplier_scores: {e}", exc_info=True)
        return build_error_response(
            code="RECALCULATE_ERROR",
            message=f"Erreur lors du recalcul: {str(e)}",
        )


# ============================================================================
# POINTS D'ENTRÉE LEGACY (conservés pour compatibilité)
# ============================================================================

@router.get("/score/{supplier_name}")
async def get_supplier_score_legacy(
    supplier_name: str,
    period_days: int = Query(90, ge=7, le=365, description="Période d'analyse en jours"),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    [LEGACY] Calcule et retourne le score complet d'un fournisseur.

    Note: Utiliser /suppliers/{supplier_id} pour la nouvelle API.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)
        score = calculator.calculate_score(
            supplier_name=supplier_name,
            period_days=period_days,
        )

        return build_success_response({
            "supplier_id": score.supplier_id,
            "supplier_name": score.supplier_name,
            "overall_score": score.overall_score,
            "grade": score.grade,
            "dimensions": {k.value: v for k, v in score.dimensions.items()},
            "metrics": score.metrics,
            "trend": score.trend,
            "last_updated": score.last_updated.isoformat(),
            "history": score.history,
        })

    except Exception as e:
        logger.error(f"Error in get_supplier_score_legacy: {e}", exc_info=True)
        return build_error_response(
            code="SCORE_ERROR",
            message=f"Erreur lors du calcul du score: {str(e)}",
        )


@router.get("/ranking")
async def get_suppliers_ranking_legacy(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    [LEGACY] Retourne le classement de tous les fournisseurs.

    Note: Utiliser /suppliers pour la nouvelle API avec pagination.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)
        ranking = calculator.get_all_suppliers_ranking()

        return build_success_response(ranking)

    except Exception as e:
        logger.error(f"Error in get_suppliers_ranking_legacy: {e}", exc_info=True)
        return build_error_response(
            code="RANKING_ERROR",
            message=f"Erreur lors du classement: {str(e)}",
        )


@router.post("/compare")
async def compare_suppliers(
    request: SupplierComparisonRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Compare plusieurs fournisseurs sur toutes les dimensions.

    Retourne:
    - Score de chaque fournisseur
    - Classement par dimension
    - Meilleur fournisseur global et par dimension
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)
        comparison = calculator.get_supplier_comparison(request.suppliers)

        # Enrichir avec les rangs
        suppliers_with_ranks = []
        for idx, supplier in enumerate(comparison["suppliers"]):
            ranks_by_dim = {}
            for dim_key, ranked_names in comparison["rankings"].items():
                rank = ranked_names.index(supplier["supplier"]) + 1 if supplier["supplier"] in ranked_names else 99
                ranks_by_dim[dim_key] = rank

            suppliers_with_ranks.append({
                "supplier_name": supplier["supplier"],
                "overall_score": supplier["overall_score"],
                "grade": supplier["grade"],
                "dimensions": supplier["dimensions"],
                "rank_overall": idx + 1,
                "ranks_by_dimension": ranks_by_dim,
            })

        # Meilleur par dimension
        best_by_dimension = {}
        for dim_key, ranked_names in comparison["rankings"].items():
            if ranked_names:
                best_by_dimension[dim_key] = ranked_names[0]

        response = SupplierComparisonResponse(
            suppliers=[SupplierComparisonItem(**s) for s in suppliers_with_ranks],
            best_overall=comparison["best_overall"],
            best_by_dimension=best_by_dimension,
        )

        return build_success_response(response.model_dump())

    except Exception as e:
        logger.error(f"Error in compare_suppliers: {e}", exc_info=True)
        return build_error_response(
            code="COMPARISON_ERROR",
            message=f"Erreur lors de la comparaison: {str(e)}",
        )


@router.post("/delivery")
async def record_delivery(
    request: DeliveryRecordRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Enregistre une livraison pour le suivi de ponctualité.

    Permet de tracker:
    - Date prévue vs date réelle
    - Retards
    - Livraisons en avance
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)

        expected_dt = datetime.combine(request.expected_date, datetime.min.time())
        actual_dt = datetime.combine(request.actual_date, datetime.min.time())

        calculator.record_delivery(
            supplier_name=request.supplier_name,
            expected_date=expected_dt,
            actual_date=actual_dt,
            invoice_id=request.invoice_id,
        )

        delay = (actual_dt - expected_dt).days

        return build_success_response({
            "status": "ok",
            "message": "Livraison enregistrée",
            "delay_days": delay,
            "on_time": delay <= 0,
        })

    except Exception as e:
        logger.error(f"Error in record_delivery: {e}", exc_info=True)
        return build_error_response(
            code="DELIVERY_ERROR",
            message=f"Erreur lors de l'enregistrement: {str(e)}",
        )


@router.post("/issue")
async def record_invoice_issue(
    request: InvoiceIssueRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    Enregistre un problème de facture.

    Types de problèmes:
    - price_error: Erreur de prix
    - quantity_error: Erreur de quantité
    - missing_item: Article manquant
    - duplicate: Facture en double

    Sévérités: low, medium, high
    """
    try:
        # Validation déjà faite par Pydantic
        calculator = SupplierScoreCalculator(tenant.id)
        calculator.record_invoice_issue(
            supplier_name=request.supplier_name,
            issue_type=request.issue_type,
            severity=request.severity,
            invoice_id=request.invoice_id,
        )

        return build_success_response({
            "status": "ok",
            "message": "Problème enregistré",
        })

    except Exception as e:
        logger.error(f"Error in record_invoice_issue: {e}", exc_info=True)
        return build_error_response(
            code="ISSUE_ERROR",
            message=f"Erreur lors de l'enregistrement: {str(e)}",
        )


@router.get("/dimensions")
async def list_dimensions() -> Dict[str, Any]:
    """
    [LEGACY] Liste les dimensions de scoring avec leurs poids.

    Note: Utiliser /criteria pour la nouvelle API.
    """
    try:
        dimensions = [
            {
                "id": ScoreDimension.PRICE_STABILITY.value,
                "name": "Stabilité des prix",
                "weight": 0.25,
                "description": "Volatilité et tendance des prix pratiqués",
            },
            {
                "id": ScoreDimension.DELIVERY_RELIABILITY.value,
                "name": "Fiabilité livraisons",
                "weight": 0.20,
                "description": "Ponctualité et respect des dates de livraison",
            },
            {
                "id": ScoreDimension.INVOICE_ACCURACY.value,
                "name": "Exactitude factures",
                "weight": 0.15,
                "description": "Taux d'erreurs sur les factures",
            },
            {
                "id": ScoreDimension.STOCK_ACCURACY.value,
                "name": "Exactitude stock",
                "weight": 0.15,
                "description": "Écarts entre quantités commandées et reçues",
            },
            {
                "id": ScoreDimension.PAYMENT_TERMS.value,
                "name": "Conditions paiement",
                "weight": 0.10,
                "description": "Flexibilité des délais de paiement",
            },
            {
                "id": ScoreDimension.RESPONSIVENESS.value,
                "name": "Réactivité",
                "weight": 0.10,
                "description": "Rapidité de réponse aux demandes",
            },
            {
                "id": ScoreDimension.PRODUCT_QUALITY.value,
                "name": "Qualité produits",
                "weight": 0.05,
                "description": "Qualité générale des produits livrés",
            },
        ]

        return build_success_response({"dimensions": dimensions})

    except Exception as e:
        logger.error(f"Error in list_dimensions: {e}", exc_info=True)
        return build_error_response(
            code="DIMENSIONS_ERROR",
            message=f"Erreur lors de la récupération: {str(e)}",
        )


@router.get("/history/{supplier_name}")
async def get_supplier_history_by_name(
    supplier_name: str,
    limit: int = Query(20, ge=1, le=100),
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> Dict[str, Any]:
    """
    [LEGACY] Retourne l'historique des scores d'un fournisseur par nom.

    Note: Utiliser /suppliers/{supplier_id}/history pour la nouvelle API.
    """
    try:
        calculator = SupplierScoreCalculator(tenant.id)
        history = calculator._get_score_history(supplier_name, limit=limit)

        return build_success_response({
            "supplier_name": supplier_name,
            "history": history,
            "count": len(history),
        })

    except Exception as e:
        logger.error(f"Error in get_supplier_history_by_name: {e}", exc_info=True)
        return build_error_response(
            code="HISTORY_ERROR",
            message=f"Erreur lors de la récupération: {str(e)}",
        )
