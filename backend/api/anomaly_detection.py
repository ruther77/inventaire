"""
API Endpoints pour Anomaly Detection
====================================

Endpoints pour:
- Détection d'anomalies sur transactions
- Détection de doublons factures
- Détection de gaps dans séquences
- Alertes de montants suspects
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant
from core.data_repository import query_df
from core.finance.anomaly_detection import (
    AnomalyDetector,
    AnomalyType,
    Severity,
)

router = APIRouter(prefix="/anomaly-detection", tags=["anomaly-detection"])


# =============================================================================
# SCHEMAS
# =============================================================================

class AnomalyResponse(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    entity_type: str
    entity_id: Optional[int]
    description: str
    detected_value: Optional[float]
    expected_range: Optional[str]
    confidence: float
    detected_at: datetime
    resolved: bool = False
    metadata: Optional[dict] = None


class AnomalyScanRequest(BaseModel):
    entity_types: List[str] = Field(default=["transactions", "invoices"])
    severity_threshold: str = Field(default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    days_back: int = Field(default=30, ge=1, le=365)


class AnomalyItemResponse(BaseModel):
    """Format attendu par le frontend pour les items d'anomalies."""
    id: str
    title: str
    type: str
    severity: str
    description: str
    impact: Optional[float] = 0
    detected_at: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    details: Optional[dict] = None


class AnomalySummaryResponse(BaseModel):
    """Format attendu par le frontend pour le summary."""
    total: int
    critical: int
    high: int
    medium: int
    low: int
    total_impact: float
    items: List[AnomalyItemResponse]
    # Anciens champs pour compatibilité
    total_anomalies: Optional[int] = None
    by_type: Optional[dict] = None
    by_severity: Optional[dict] = None
    recent_critical: Optional[List[AnomalyResponse]] = None


class DuplicateInvoiceResponse(BaseModel):
    invoice_id_1: int
    invoice_id_2: int
    supplier: str
    amount: float
    date_1: datetime
    date_2: datetime
    similarity_score: float
    reason: str


class SequenceGapResponse(BaseModel):
    sequence_name: str
    expected_value: str
    missing_before: str
    missing_after: str
    gap_size: int
    detected_at: datetime


class RoundAmountResponse(BaseModel):
    entity_type: str
    entity_id: int
    amount: float
    description: str
    suspicion_score: float
    reason: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_transactions(tenant_id: int, days: int = 30) -> List[dict]:
    """Récupère les transactions pour analyse depuis finance_transactions.

    Note: finance_transactions utilise entity_id (pas tenant_id).
    Mapping: tenant 4 (intelligence) -> entity 2 (restaurant)
    """
    # Mapper tenant vers entity: restaurant=2, trésorerie=3
    entity_id = 2 if tenant_id == 4 else tenant_id
    sql = """
        SELECT
            id,
            date_operation as date,
            amount as amount,
            COALESCE(label, note) as description,
            NULL as category_id
        FROM finance_transactions
        WHERE entity_id = :entity_id
          AND date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY date_operation DESC
    """
    df = query_df(sql, params={"entity_id": entity_id, "days": days})
    if df.empty:
        return []
    return df.to_dict('records')


def _get_invoices(tenant_id: int, days: int = 90) -> List[dict]:
    """Récupère les factures pour analyse depuis finance_invoices_supplier.

    Note: finance_invoices_supplier utilise entity_id (pas tenant_id).
    Mapping: tenant 4 (intelligence) -> entity 2 (restaurant)
    """
    # Mapper tenant vers entity: restaurant=2, trésorerie=3
    entity_id = 2 if tenant_id == 4 else tenant_id
    sql = """
        SELECT
            i.id,
            i.date_invoice as date,
            i.montant_ttc as amount,
            i.invoice_number as invoice_number,
            v.name as supplier_name,
            i.vendor_id as supplier_id
        FROM finance_invoices_supplier i
        LEFT JOIN finance_vendors v ON v.id = i.vendor_id
        WHERE i.entity_id = :entity_id
          AND i.date_invoice >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY i.date_invoice DESC
    """
    df = query_df(sql, params={"entity_id": entity_id, "days": days})
    if df.empty:
        return []
    return df.to_dict('records')


def _severity_to_string(severity: Severity) -> str:
    """Convertit severity enum en string"""
    return severity.value if hasattr(severity, 'value') else str(severity)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/scan", response_model=List[AnomalyResponse])
def scan_for_anomalies(
    entity_types: str = Query(default="transactions,invoices"),
    severity_threshold: str = Query(default="LOW"),
    days_back: int = Query(default=30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Scanne les données pour détecter des anomalies.

    Types d'entités supportés:
    - transactions: Transactions bancaires
    - invoices: Factures fournisseurs

    Seuils de sévérité: LOW, MEDIUM, HIGH, CRITICAL
    """
    entity_list = [e.strip() for e in entity_types.split(",")]

    transactions = None
    invoices = None

    if "transactions" in entity_list:
        transactions = _get_transactions(tenant.id, days_back)

    if "invoices" in entity_list:
        invoices = _get_invoices(tenant.id, days_back)

    anomalies = []

    try:
        detector = AnomalyDetector(tenant_id=tenant.id)
        # Utiliser les méthodes individuelles plutôt que detect_all (qui fait des requêtes supplémentaires)
        if transactions:
            detected_tx = detector.detect_transaction_anomalies(transactions)
            for d in detected_tx:
                anomalies.append(AnomalyResponse(
                    id=d.anomaly_id,
                    anomaly_type=d.anomaly_type.value.upper(),
                    severity=d.severity.value.upper(),
                    entity_type=d.entity_type,
                    entity_id=int(d.entity_id) if d.entity_id.isdigit() else None,
                    description=d.description,
                    detected_value=d.details.get('amount'),
                    expected_range=d.details.get('expected_range'),
                    confidence=d.confidence,
                    detected_at=d.detected_at,
                    resolved=d.resolved,
                    metadata=d.details
                ))

        if invoices:
            detected_inv = detector.detect_invoice_anomalies(invoices)
            for d in detected_inv:
                anomalies.append(AnomalyResponse(
                    id=d.anomaly_id,
                    anomaly_type=d.anomaly_type.value.upper(),
                    severity=d.severity.value.upper(),
                    entity_type=d.entity_type,
                    entity_id=int(d.entity_id) if d.entity_id.isdigit() else None,
                    description=d.description,
                    detected_value=d.details.get('amount'),
                    expected_range=d.details.get('expected_range'),
                    confidence=d.confidence,
                    detected_at=d.detected_at,
                    resolved=d.resolved,
                    metadata=d.details
                ))
    except Exception as e:
        # En cas d'erreur dans le module core, retourner les anomalies détectées jusqu'ici
        import logging
        logging.warning(f"Erreur détection anomalies: {e}")

    # Filtrer par seuil de sévérité
    severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    threshold_level = severity_order.get(severity_threshold.upper(), 0)

    filtered = [
        a for a in anomalies
        if severity_order.get(a.severity, 0) >= threshold_level
    ]

    return filtered


@router.get("/transactions/outliers", response_model=List[AnomalyResponse])
def detect_transaction_outliers(
    days_back: int = Query(default=30, ge=1, le=365),
    z_score_threshold: float = Query(default=2.5, ge=1.5, le=5.0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Détecte les transactions avec des montants anormalement élevés ou bas
    en utilisant le Z-score statistique.
    """
    detector = AnomalyDetector(tenant_id=tenant.id)
    # Ajuster le seuil Z-score
    detector.Z_SCORE_THRESHOLD = z_score_threshold

    transactions = _get_transactions(tenant.id, days_back)

    if not transactions:
        return []

    # Utiliser detect_transaction_anomalies
    detected = detector.detect_transaction_anomalies(transactions)

    # Filtrer uniquement les outliers de montant
    anomalies = []
    for d in detected:
        if d.anomaly_type == AnomalyType.AMOUNT_OUTLIER:
            anomalies.append(AnomalyResponse(
                id=d.anomaly_id,
                anomaly_type="AMOUNT_OUTLIER",
                severity=d.severity.value.upper(),
                entity_type=d.entity_type,
                entity_id=int(d.entity_id) if d.entity_id.isdigit() else None,
                description=d.description,
                detected_value=d.details.get('amount'),
                expected_range=d.details.get('expected_range'),
                confidence=d.confidence,
                detected_at=d.detected_at,
                metadata=d.details
            ))

    return anomalies


@router.get("/invoices/duplicates", response_model=List[DuplicateInvoiceResponse])
def detect_duplicate_invoices(
    days_back: int = Query(default=90, ge=1, le=365),
    similarity_threshold: float = Query(default=0.9, ge=0.7, le=1.0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Détecte les factures potentiellement en double.

    Critères de détection:
    - Même fournisseur
    - Montant identique ou très proche
    - Dates proches (< 7 jours)
    """
    invoices = _get_invoices(tenant.id, days_back)
    duplicates = []

    for i, inv1 in enumerate(invoices):
        for inv2 in invoices[i+1:]:
            # Même fournisseur?
            if inv1.get('supplier_id') != inv2.get('supplier_id'):
                continue

            amount1 = float(inv1.get('amount') or 0)
            amount2 = float(inv2.get('amount') or 0)

            # Montant similaire?
            if amount1 == 0 or amount2 == 0:
                continue

            amount_similarity = 1 - abs(amount1 - amount2) / max(amount1, amount2)
            if amount_similarity < similarity_threshold:
                continue

            # Dates proches?
            date1 = inv1.get('date')
            date2 = inv2.get('date')
            if not date1 or not date2:
                continue

            date_diff = abs((date1 - date2).days)
            if date_diff > 7:
                continue

            # Calculer score de similarité global
            date_similarity = 1 - (date_diff / 7)
            overall_similarity = (amount_similarity + date_similarity) / 2

            duplicates.append(DuplicateInvoiceResponse(
                invoice_id_1=inv1['id'],
                invoice_id_2=inv2['id'],
                supplier=inv1.get('supplier_name', 'Unknown'),
                amount=amount1,
                date_1=date1,
                date_2=date2,
                similarity_score=overall_similarity,
                reason=f"Même fournisseur, montant identique à {amount_similarity*100:.0f}%, {date_diff}j d'écart"
            ))

    # Trier par score de similarité décroissant
    duplicates.sort(key=lambda x: x.similarity_score, reverse=True)

    return duplicates


@router.get("/invoices/sequence-gaps", response_model=List[SequenceGapResponse])
def detect_invoice_sequence_gaps(
    days_back: int = Query(default=90, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Détecte les trous dans les séquences de numéros de factures.
    Utile pour identifier des factures manquantes.
    """
    # Récupérer les factures groupées par fournisseur
    sql = """
        SELECT
            vendor_id as supplier_id,
            v.name as supplier_name,
            ARRAY_AGG(invoice_number ORDER BY date_invoice) as invoice_numbers,
            ARRAY_AGG(date_invoice ORDER BY date_invoice) as dates
        FROM finance_invoices_supplier i
        LEFT JOIN finance_vendors v ON v.id = i.vendor_id
        WHERE i.tenant_id = :tenant_id
          AND i.date_invoice >= CURRENT_DATE - :days * INTERVAL '1 day'
          AND invoice_number IS NOT NULL
        GROUP BY vendor_id, v.name
        HAVING COUNT(*) > 3
    """
    df = query_df(sql, params={"tenant_id": tenant.id, "days": days_back})

    gaps = []
    import re

    for _, row in df.iterrows():
        numbers = row['invoice_numbers']
        supplier = row['supplier_name'] or f"Supplier {row['supplier_id']}"

        # Extraire les parties numériques
        numeric_parts = []
        for num in numbers:
            if num:
                match = re.search(r'(\d+)$', str(num))
                if match:
                    numeric_parts.append((int(match.group(1)), num))

        # Trier et chercher les gaps
        numeric_parts.sort(key=lambda x: x[0])

        for i in range(len(numeric_parts) - 1):
            current = numeric_parts[i][0]
            next_num = numeric_parts[i + 1][0]

            if next_num - current > 1:
                gap_size = next_num - current - 1
                gaps.append(SequenceGapResponse(
                    sequence_name=f"{supplier} - Factures",
                    expected_value=str(current + 1),
                    missing_before=numeric_parts[i][1],
                    missing_after=numeric_parts[i + 1][1],
                    gap_size=gap_size,
                    detected_at=datetime.now()
                ))

    return gaps


@router.get("/transactions/round-amounts", response_model=List[RoundAmountResponse])
def detect_round_amounts(
    days_back: int = Query(default=30, ge=1, le=365),
    min_amount: float = Query(default=100.0, ge=0),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Détecte les transactions avec des montants ronds suspects.

    Les montants parfaitement ronds (ex: 1000.00, 500.00) peuvent indiquer:
    - Estimations plutôt que montants réels
    - Fraude potentielle
    - Erreurs de saisie
    """
    sql = """
        SELECT
            id,
            date_operation as date,
            amount as amount,
            COALESCE(label, note) as description
        FROM finance_transactions
        WHERE tenant_id = :tenant_id
          AND date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
          AND ABS(amount) >= :min_amount
        ORDER BY ABS(amount) DESC
    """
    df = query_df(sql, params={"tenant_id": tenant.id, "days": days_back, "min_amount": min_amount})

    suspicious = []
    for _, row in df.iterrows():
        amount = abs(float(row['amount']))

        # Vérifier si le montant est "trop rond"
        is_round_100 = amount % 100 == 0
        is_round_1000 = amount % 1000 == 0
        is_round_10000 = amount % 10000 == 0

        if is_round_10000:
            score = 0.9
            reason = "Montant rond à 10000€ près"
        elif is_round_1000:
            score = 0.7
            reason = "Montant rond à 1000€ près"
        elif is_round_100 and amount >= 500:
            score = 0.5
            reason = "Montant rond à 100€ près"
        else:
            continue

        suspicious.append(RoundAmountResponse(
            entity_type="transaction",
            entity_id=row['id'],
            amount=float(row['amount']),
            description=row['description'],
            suspicion_score=score,
            reason=reason
        ))

    # Trier par score de suspicion
    suspicious.sort(key=lambda x: x.suspicion_score, reverse=True)

    return suspicious


@router.get("/summary", response_model=AnomalySummaryResponse)
def get_anomaly_summary(
    days_back: int = Query(default=30, ge=1, le=365),
    severity: Optional[str] = Query(default=None, description="Filtrer par sévérité (critical, high, medium, low)"),
    type: Optional[str] = Query(default=None, description="Filtrer par type d'anomalie"),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Résumé des anomalies détectées avec filtrage optionnel.
    """
    # Scanner toutes les anomalies
    all_anomalies = scan_for_anomalies(
        entity_types="transactions,invoices",
        severity_threshold="LOW",
        days_back=days_back,
        tenant=tenant
    )

    # Compter par sévérité AVANT filtrage
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    total_impact = 0.0
    for a in all_anomalies:
        sev = a.severity.upper() if a.severity else "LOW"
        if sev in severity_counts:
            severity_counts[sev] += 1
        # Estimation impact basée sur detected_value
        if a.detected_value:
            total_impact += abs(float(a.detected_value))

    # Filtrer si demandé
    filtered_anomalies = all_anomalies
    if severity:
        filtered_anomalies = [a for a in filtered_anomalies if a.severity.lower() == severity.lower()]
    if type:
        filtered_anomalies = [a for a in filtered_anomalies if a.anomaly_type.lower() == type.lower()]

    # Trier par date
    filtered_anomalies.sort(key=lambda x: x.detected_at, reverse=True)

    # Convertir au format frontend
    items = []
    for a in filtered_anomalies[:50]:  # Limiter à 50 items
        items.append(AnomalyItemResponse(
            id=a.id,
            title=a.description[:80] if a.description else "Anomalie détectée",
            type=a.anomaly_type.lower() if a.anomaly_type else "unknown",
            severity=a.severity.lower() if a.severity else "low",
            description=a.description or "",
            impact=float(a.detected_value) if a.detected_value else 0,
            detected_at=a.detected_at.isoformat() if a.detected_at else "",
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            details=a.metadata
        ))

    # Agréger par type (pour compatibilité)
    by_type = {}
    for a in all_anomalies:
        by_type[a.anomaly_type] = by_type.get(a.anomaly_type, 0) + 1

    # Agréger par sévérité (pour compatibilité)
    by_severity = {}
    for a in all_anomalies:
        by_severity[a.severity] = by_severity.get(a.severity, 0) + 1

    # Critiques récentes (pour compatibilité)
    critical_list = [a for a in all_anomalies if a.severity in ["CRITICAL", "HIGH"]]
    critical_list.sort(key=lambda x: x.detected_at, reverse=True)

    return AnomalySummaryResponse(
        # Nouveaux champs pour frontend
        total=len(filtered_anomalies),
        critical=severity_counts["CRITICAL"],
        high=severity_counts["HIGH"],
        medium=severity_counts["MEDIUM"],
        low=severity_counts["LOW"],
        total_impact=total_impact,
        items=items,
        # Anciens champs pour compatibilité
        total_anomalies=len(all_anomalies),
        by_type=by_type,
        by_severity=by_severity,
        recent_critical=critical_list[:10]
    )


@router.post("/resolve/{anomaly_id}")
def resolve_anomaly(
    anomaly_id: str,
    resolution_note: str = Query(..., min_length=5),
    tenant: Tenant = Depends(get_current_tenant)
):
    """
    Marque une anomalie comme résolue avec une note explicative.
    """
    # En prod, ceci serait persisté en DB
    # Pour l'instant, on retourne juste un statut de succès
    return {
        "status": "resolved",
        "anomaly_id": anomaly_id,
        "resolution_note": resolution_note,
        "resolved_at": datetime.now().isoformat()
    }
