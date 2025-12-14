"""
NewCMS Finance Endpoints
========================

Endpoints agrégés pour le nouveau CMS:
- /newcms/finance/overview - Vue d'ensemble finance avec stats rapprochement, cash-flow, suggestions IA
- /newcms/finance/transactions - Proxy paginé des transactions avec filtres avancés (q, date_from/to, amount_min/max, direction IN/OUT/TRANSFER)
- /newcms/finance/reconciliation/apply - Application d'une suggestion de rapprochement IA

Format de réponse standardisé via ResponseWrapperMiddleware:
{
    "success": true/false,
    "data": {...},
    "error": null | {...},
    "meta": {"request_id": "...", "duration_ms": ..., "pagination": {...}}
}
"""

from __future__ import annotations

import logging
import json
from pathlib import Path
from uuid import uuid4
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant_or_default
from core.data_repository import query_df, exec_sql
from core.finance.bank_reconciliation import BankReconciliationEngine
from backend.services.finance import rules as finance_rules
from backend.schemas.finance_rules import FinanceRuleCreate as CoreFinanceRuleCreate
import re
from pydantic import BaseModel as PydanticBaseModel

router = APIRouter(prefix="/finance", tags=["newcms-finance"])
logger = logging.getLogger(__name__)
RULES_STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "newcms_finance_rules.json"
META_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS newcms_finance_transaction_meta (
        transaction_id BIGINT PRIMARY KEY REFERENCES finance_transactions(id) ON DELETE CASCADE,
        category TEXT,
        note TEXT,
        ignored BOOLEAN DEFAULT FALSE,
        manual_invoice_ids JSONB,
        updated_at TIMESTAMPTZ DEFAULT now()
    )
"""
CLASSIFICATION_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS finance_transaction_classification (
        id BIGSERIAL PRIMARY KEY,
        transaction_id BIGINT NOT NULL UNIQUE REFERENCES finance_transactions(id) ON DELETE CASCADE,
        category_id BIGINT NULL REFERENCES finance_categories(id),
        source TEXT NOT NULL DEFAULT 'manual',
        rule_id BIGINT NULL REFERENCES finance_rules(id),
        confidence NUMERIC(5,2),
        ignored BOOLEAN NOT NULL DEFAULT FALSE,
        note TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
"""


# =============================================================================
# SCHEMAS
# =============================================================================

class ReconciliationStats(BaseModel):
    """Stats de rapprochement bancaire."""
    matched_count: int = Field(..., description="Nombre de transactions rapprochées")
    pending_count: int = Field(..., description="Nombre de transactions en attente")
    unmatched_count: int = Field(..., description="Nombre de transactions non rapprochées")
    matched_percentage: float = Field(..., description="Pourcentage de rapprochement")
    pending_percentage: float = Field(..., description="Pourcentage en attente")
    unmatched_percentage: float = Field(..., description="Pourcentage non rapproché")
    total_amount_matched: float = Field(..., description="Montant total rapproché (€)")
    total_amount_pending: float = Field(..., description="Montant total en attente (€)")


class CashFlowPeriod(BaseModel):
    """Cash-flow sur une période."""
    period_days: int = Field(..., description="Nombre de jours de la période")
    total_inflow: float = Field(..., description="Total des entrées (€)")
    total_outflow: float = Field(..., description="Total des sorties (€)")
    net_cashflow: float = Field(..., description="Cash-flow net (€)")
    avg_daily_inflow: float = Field(..., description="Moyenne quotidienne des entrées (€)")
    avg_daily_outflow: float = Field(..., description="Moyenne quotidienne des sorties (€)")
    current_balance: float = Field(..., description="Solde actuel (€)")


class ReconciliationSuggestion(BaseModel):
    """Suggestion de rapprochement IA."""
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
    """Transaction récente."""
    id: int
    date: date
    amount: float
    label: str
    direction: str  # IN, OUT, TRANSFER
    category: Optional[str] = None
    category_id: Optional[int] = None
    reconciled: bool = False


class FinanceOverviewResponse(BaseModel):
    """Réponse complète de l'overview finance."""
    reconciliation_stats: ReconciliationStats
    cashflow_30d: CashFlowPeriod
    ai_suggestions: List[ReconciliationSuggestion] = Field(
        ..., max_length=5, description="Top 5 suggestions de rapprochement IA"
    )
    recent_transactions: List[RecentTransaction] = Field(
        ..., max_length=5, description="5 dernières transactions"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionFilter(BaseModel):
    """Filtres pour les transactions."""
    q: Optional[str] = Field(None, description="Recherche texte")
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[float] = Field(None, ge=0)
    amount_max: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    page: int = Field(1, ge=1)
    size: int = Field(50, ge=1, le=500)


class TransactionListResponse(BaseModel):
    """Réponse paginée des transactions."""
    transactions: List[RecentTransaction]
    total: int
    page: int
    size: int
    pages: int


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
# HELPER FUNCTIONS
# =============================================================================

def _get_entity_id(tenant_id: int) -> int:
    """Convertit tenant_id en entity_id pour finance_transactions."""
    # Tenant intelligence (4) accède au tenant épicerie groupe (2)
    return 2 if tenant_id == 4 else tenant_id


def _get_reconciliation_stats(tenant_id: int) -> ReconciliationStats:
    """Calcule les stats de rapprochement."""
    entity_id = _get_entity_id(tenant_id)

    sql = """
        SELECT
            COUNT(*) FILTER (WHERE fr.id IS NOT NULL) as matched,
            COUNT(*) FILTER (WHERE fr.id IS NULL) as unmatched,
            COALESCE(SUM(ABS(CAST(ft.amount AS NUMERIC))) FILTER (WHERE fr.id IS NOT NULL), 0) as matched_amount,
            COALESCE(SUM(ABS(CAST(ft.amount AS NUMERIC))) FILTER (WHERE fr.id IS NULL), 0) as unmatched_amount,
            COUNT(*) as total
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        WHERE ft.entity_id = :entity_id
          AND ft.date_operation >= CURRENT_DATE - INTERVAL '60 days'
          AND ft.direction = 'OUT'
    """

    df = query_df(sql, params={"entity_id": entity_id})

    if df.empty:
        return ReconciliationStats(
            matched_count=0,
            pending_count=0,
            unmatched_count=0,
            matched_percentage=0.0,
            pending_percentage=0.0,
            unmatched_percentage=0.0,
            total_amount_matched=0.0,
            total_amount_pending=0.0,
        )

    row = df.iloc[0]
    total = int(row['total'] or 0)
    matched = int(row['matched'] or 0)
    unmatched = int(row['unmatched'] or 0)
    matched_amount = float(row['matched_amount'] or 0)
    unmatched_amount = float(row['unmatched_amount'] or 0)

    # Pour l'instant, pending = 0 (on pourrait filtrer par status)
    pending = 0
    pending_amount = 0.0

    matched_pct = (matched / total * 100) if total > 0 else 0.0
    pending_pct = (pending / total * 100) if total > 0 else 0.0
    unmatched_pct = (unmatched / total * 100) if total > 0 else 0.0

    return ReconciliationStats(
        matched_count=matched,
        pending_count=pending,
        unmatched_count=unmatched,
        matched_percentage=round(matched_pct, 1),
        pending_percentage=round(pending_pct, 1),
        unmatched_percentage=round(unmatched_pct, 1),
        total_amount_matched=round(matched_amount, 2),
        total_amount_pending=round(pending_amount, 2),
    )


def _get_cashflow_30d(tenant_id: int) -> CashFlowPeriod:
    """Calcule le cash-flow sur 30 jours."""
    entity_id = _get_entity_id(tenant_id)

    sql = """
        SELECT
            COALESCE(SUM(CAST(amount AS NUMERIC)) FILTER (WHERE direction = 'IN'), 0) as inflow,
            COALESCE(SUM(ABS(CAST(amount AS NUMERIC))) FILTER (WHERE direction = 'OUT'), 0) as outflow,
            COUNT(*) FILTER (WHERE direction = 'IN') as inflow_count,
            COUNT(*) FILTER (WHERE direction = 'OUT') as outflow_count
        FROM finance_transactions
        WHERE entity_id = :entity_id
          AND date_operation >= CURRENT_DATE - INTERVAL '30 days'
    """

    df = query_df(sql, params={"entity_id": entity_id})

    if df.empty:
        inflow = outflow = 0.0
        inflow_count = outflow_count = 0
    else:
        row = df.iloc[0]
        inflow = float(row['inflow'] or 0)
        outflow = float(row['outflow'] or 0)
        inflow_count = int(row['inflow_count'] or 0)
        outflow_count = int(row['outflow_count'] or 0)

    net = inflow - outflow
    avg_daily_inflow = inflow / 30 if inflow > 0 else 0.0
    avg_daily_outflow = outflow / 30 if outflow > 0 else 0.0

    # Solde actuel (somme de toutes les transactions)
    balance_sql = """
        SELECT COALESCE(SUM(CAST(amount AS NUMERIC)), 0) as balance
        FROM finance_transactions
        WHERE entity_id = :entity_id
    """
    balance_df = query_df(balance_sql, params={"entity_id": entity_id})
    current_balance = float(balance_df.iloc[0]['balance'] or 0) if not balance_df.empty else 0.0

    return CashFlowPeriod(
        period_days=30,
        total_inflow=round(inflow, 2),
        total_outflow=round(outflow, 2),
        net_cashflow=round(net, 2),
        avg_daily_inflow=round(avg_daily_inflow, 2),
        avg_daily_outflow=round(avg_daily_outflow, 2),
        current_balance=round(current_balance, 2),
    )


def _ensure_meta_table() -> None:
    exec_sql(META_TABLE_SQL)


def _ensure_classification_table() -> None:
    exec_sql(CLASSIFICATION_TABLE_SQL)


def _upsert_meta(transaction_id: int, values: dict) -> None:
    _ensure_meta_table()
    # Normaliser les valeurs JSON
    norm_values = {}
    for k, v in values.items():
        if k == "manual_invoice_ids" and isinstance(v, list):
            norm_values[k] = json.dumps(v)
        else:
            norm_values[k] = v
    set_clause = ", ".join([f"{k} = :{k}" for k in values.keys()])
    sql = f"""
        INSERT INTO newcms_finance_transaction_meta (transaction_id, {', '.join(values.keys())})
        VALUES (:transaction_id, {', '.join(':'+k for k in values.keys())})
        ON CONFLICT (transaction_id) DO UPDATE SET {set_clause}, updated_at = now()
    """
    exec_sql(sql, params={"transaction_id": transaction_id, **norm_values})


def _get_meta(transaction_ids: list[int]) -> dict[int, dict]:
    if not transaction_ids:
        return {}
    _ensure_meta_table()
    df = query_df(
        """
        SELECT transaction_id, category, note, ignored, manual_invoice_ids, updated_at
        FROM newcms_finance_transaction_meta
        WHERE transaction_id = ANY(:ids)
        """,
        params={"ids": transaction_ids},
    )
    if df.empty:
        return {}
    rows = df.where(df.notna(), None).to_dict("records")
    return {int(r["transaction_id"]): r for r in rows}


def _assert_transaction_exists(entity_id: int, tx_id: int) -> None:
    exists_df = query_df(
        "SELECT id FROM finance_transactions WHERE id = :tx_id LIMIT 1",
        params={"tx_id": tx_id},
    )
    if exists_df.empty:
        raise HTTPException(status_code=404, detail=f"Transaction {tx_id} introuvable")


def _upsert_classification(
    transaction_id: int,
    *,
    category_id: int | None,
    source: str,
    rule_id: int | None = None,
    confidence: float | None = None,
    ignored: bool = False,
    note: str | None = None,
) -> None:
    _ensure_classification_table()
    sql = """
        INSERT INTO finance_transaction_classification (transaction_id, category_id, source, rule_id, confidence, ignored, note)
        VALUES (:transaction_id, :category_id, :source, :rule_id, :confidence, :ignored, :note)
        ON CONFLICT (transaction_id) DO UPDATE SET
            category_id = EXCLUDED.category_id,
            source = EXCLUDED.source,
            rule_id = EXCLUDED.rule_id,
            confidence = EXCLUDED.confidence,
            ignored = EXCLUDED.ignored,
            note = EXCLUDED.note,
            updated_at = now()
    """
    exec_sql(
        sql,
        params={
            "transaction_id": transaction_id,
            "category_id": category_id,
            "source": source,
            "rule_id": rule_id,
            "confidence": confidence,
            "ignored": ignored,
            "note": note,
        },
    )


def _get_classification_map(transaction_ids: list[int]) -> dict[int, dict]:
    if not transaction_ids:
        return {}
    _ensure_classification_table()
    df = query_df(
        """
        SELECT c.transaction_id, c.category_id, c.source, c.rule_id, c.confidence, c.ignored, c.note,
               cat.name AS category_name, cat.code AS category_code
        FROM finance_transaction_classification c
        LEFT JOIN finance_categories cat ON cat.id = c.category_id
        WHERE c.transaction_id = ANY(:ids)
        """,
        params={"ids": transaction_ids},
    )
    if df.empty:
        return {}
    rows = df.where(df.notna(), None).to_dict("records")
    return {int(r["transaction_id"]): r for r in rows}


def _get_ai_suggestions(tenant_id: int, limit: int = 5) -> List[ReconciliationSuggestion]:
    """Récupère les suggestions de rapprochement IA."""
    engine = BankReconciliationEngine(tenant_id=tenant_id)

    # Obtenir les transactions non rapprochées
    unmatched = engine.get_unmatched_transactions(limit=limit * 2)

    suggestions = []

    for tx in unmatched[:limit]:
        # Lancer le rapprochement pour cette transaction
        result = engine.reconcile_single(
            transaction={
                "id": tx["id"],
                "montant": tx["amount"],
                "date": tx["date"],
                "libelle": tx.get("description", ""),
            },
            auto_apply=False,
            min_confidence=0.5
        )

        if result.matched_invoices and result.confidence >= 0.5:
            # Récupérer les détails des factures
            invoice_details = []
            for inv_id in result.matched_invoices:
                entity_id = _get_entity_id(tenant_id)
                inv_sql = """
                    SELECT
                        i.id,
                        i.invoice_number,
                        v.name as supplier_name,
                        i.montant_ttc,
                        i.date_invoice
                    FROM finance_invoices_supplier i
                    LEFT JOIN finance_vendors v ON v.id = i.vendor_id
                    WHERE i.id = :invoice_id AND i.entity_id = :entity_id
                """
                inv_df = query_df(inv_sql, params={"invoice_id": inv_id, "entity_id": entity_id})

                if not inv_df.empty:
                    inv = inv_df.iloc[0]
                    invoice_details.append({
                        "id": int(inv['id']),
                        "invoice_number": inv['invoice_number'],
                        "supplier_name": inv['supplier_name'] or "Unknown",
                        "amount": float(inv['montant_ttc'] or 0),
                        "date": str(inv['date_invoice']),
                    })

            if invoice_details:
                suggestion = ReconciliationSuggestion(
                    suggestion_id=f"ai-{tx['id']}-{datetime.utcnow().timestamp()}",
                    transaction_id=tx['id'],
                    transaction_date=datetime.fromisoformat(tx['date']).date() if isinstance(tx['date'], str) else tx['date'],
                    transaction_amount=tx['amount'],
                    transaction_label=tx.get('description', ''),
                    matched_invoice_ids=result.matched_invoices,
                    matched_invoices_info=invoice_details,
                    confidence=result.confidence,
                    match_type=result.match_type.value if result.match_type else "unknown",
                    total_matched_amount=result.amount_covered,
                    difference=result.amount_remaining,
                    explanation=result.details.get("explanation", f"Match {result.match_type.value if result.match_type else 'unknown'} avec confiance {result.confidence:.0%}"),
                )
                suggestions.append(suggestion)

    return suggestions[:limit]


def _get_recent_transactions(tenant_id: int, limit: int = 5) -> List[RecentTransaction]:
    """Récupère les transactions récentes."""
    entity_id = _get_entity_id(tenant_id)

    sql = """
        SELECT
            ft.id,
            ft.date_operation as date,
            CAST(ft.amount AS NUMERIC) as amount,
            ft.label,
            ft.direction,
            cat.name as category,
            cat.id as category_id,
            CASE WHEN fr.id IS NOT NULL THEN true ELSE false END as reconciled
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        LEFT JOIN finance_transaction_classification class ON class.transaction_id = ft.id
        LEFT JOIN finance_categories cat ON cat.id = class.category_id
        WHERE ft.entity_id = :entity_id
        ORDER BY ft.date_operation DESC, ft.id DESC
        LIMIT :limit
    """

    df = query_df(sql, params={"entity_id": entity_id, "limit": limit})

    transactions = []
    for _, row in df.iterrows():
        transactions.append(RecentTransaction(
            id=int(row['id']),
            date=row['date'],
            amount=float(row['amount']),
            label=row['label'] or '',
            direction=row['direction'],
            category=row.get('category'),
            category_id=row.get('category_id'),
            reconciled=bool(row['reconciled']),
        ))

    return transactions


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/overview", response_model=FinanceOverviewResponse, summary="Overview Finance", tags=["newcms-finance"])
def get_finance_overview(
    tenant: Tenant = Depends(get_current_tenant_or_default)
) -> FinanceOverviewResponse:
    """
    **Finance Overview - Vue d'ensemble financière complète**

    Endpoint agrégé qui fournit toutes les métriques financières critiques en un seul appel.
    Optimisé pour le dashboard Finance du newCMS.

    ## Données retournées

    ### 1. Statistiques de rapprochement bancaire
    - **matched_count**: Nombre de transactions rapprochées
    - **pending_count**: Nombre de transactions en attente
    - **unmatched_count**: Nombre de transactions non rapprochées
    - **matched_percentage**: Taux de rapprochement (%)
    - **total_amount_matched**: Montant total rapproché (€)
    - **total_amount_pending**: Montant en attente (€)

    Période analysée: 60 derniers jours, transactions sortantes uniquement.

    ### 2. Cash-flow sur 30 jours
    - **total_inflow**: Total des entrées (€)
    - **total_outflow**: Total des sorties (€)
    - **net_cashflow**: Flux net (€)
    - **avg_daily_inflow**: Moyenne quotidienne des entrées (€)
    - **avg_daily_outflow**: Moyenne quotidienne des sorties (€)
    - **current_balance**: Solde actuel du compte (€)

    ### 3. Top 5 suggestions IA de rapprochement
    Pour chaque suggestion:
    - **transaction_id**: ID de la transaction bancaire
    - **matched_invoice_ids**: IDs des factures à rapprocher
    - **confidence**: Niveau de confiance IA (0-1)
    - **match_type**: Type de match (exact, fuzzy, multi_line, alias)
    - **difference**: Écart entre transaction et factures (€)
    - **explanation**: Explication détaillée du match

    Les suggestions sont triées par confiance décroissante.

    ### 4. 5 dernières transactions
    - Date, montant, libellé, direction (IN/OUT)
    - Statut de rapprochement (reconciled: true/false)
    - Catégorie si disponible

    ## Tags
    - newcms-finance
    """
    try:
        # 1. Stats de rapprochement
        reconciliation_stats = _get_reconciliation_stats(tenant.id)

        # 2. Cash-flow 30 jours
        cashflow_30d = _get_cashflow_30d(tenant.id)

        # 3. Suggestions IA (top 5)
        ai_suggestions = _get_ai_suggestions(tenant.id, limit=5)

        # 4. Transactions récentes (5 dernières)
        recent_transactions = _get_recent_transactions(tenant.id, limit=5)

        return FinanceOverviewResponse(
            reconciliation_stats=reconciliation_stats,
            cashflow_30d=cashflow_30d,
            ai_suggestions=ai_suggestions,
            recent_transactions=recent_transactions,
            generated_at=datetime.utcnow(),
        )

    except Exception as exc:
        logger.exception("Error generating finance overview")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération de l'overview: {str(exc)}"
        ) from exc


@router.get("/transactions", response_model=TransactionListResponse, summary="Liste des transactions", tags=["newcms-finance"])
def get_transactions(
    q: Optional[str] = Query(None, description="Recherche texte sur libellé"),
    date_from: Optional[date] = Query(None, description="Date de début"),
    date_to: Optional[date] = Query(None, description="Date de fin"),
    amount_min: Optional[float] = Query(None, ge=0, description="Montant minimum"),
    amount_max: Optional[float] = Query(None, ge=0, description="Montant maximum"),
    direction: Optional[str] = Query(None, description="Direction (IN/OUT/TRANSFER)"),
    category: Optional[str] = Query(None, description="Catégorie"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(50, ge=1, le=100, description="Nombre d'items par page"),
    tenant: Tenant = Depends(get_current_tenant_or_default)
) -> TransactionListResponse:
    """
    **Liste paginée des transactions bancaires**

    Endpoint de listing avec filtrage avancé et pagination performante.
    Permet de rechercher et filtrer les transactions selon plusieurs critères.

    ## Filtres disponibles

    - **q**: Recherche textuelle sur le libellé (ILIKE, insensible à la casse)
    - **date_from, date_to**: Plage de dates (format: YYYY-MM-DD)
    - **amount_min, amount_max**: Plage de montants en valeur absolue (€)
    - **direction**: IN (entrée), OUT (sortie), TRANSFER
    - **category**: Filtrage par catégorie (si disponible)

    ## Pagination

    - **page**: Numéro de page (défaut: 1)
    - **per_page**: Taille de page (1-100, défaut: 50)
    - Retourne: total, page, size, pages

    ## Informations retournées

    Pour chaque transaction:
    - **id**: ID unique de la transaction
    - **date**: Date de l'opération
    - **amount**: Montant (€, négatif pour les sorties)
    - **label**: Libellé de la transaction
    - **direction**: IN, OUT, TRANSFER
    - **category**: Catégorie si disponible
    - **reconciled**: true si rapprochée avec une facture

    Les transactions sont triées par date décroissante (plus récentes d'abord).

    ## Tags
    - newcms-finance
    """
    entity_id = _get_entity_id(tenant.id)

    # Construction de la requête SQL
    conditions = ["ft.entity_id = :entity_id"]
    params = {"entity_id": entity_id, "limit": per_page, "offset": (page - 1) * per_page}

    if q:
        conditions.append("ft.label ILIKE :q")
        params["q"] = f"%{q}%"

    if date_from:
        conditions.append("ft.date_operation >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("ft.date_operation <= :date_to")
        params["date_to"] = date_to

    if amount_min is not None:
        conditions.append("ABS(CAST(ft.amount AS NUMERIC)) >= :amount_min")
        params["amount_min"] = amount_min

    if amount_max is not None:
        conditions.append("ABS(CAST(ft.amount AS NUMERIC)) <= :amount_max")
        params["amount_max"] = amount_max

    if direction:
        # Validation du paramètre direction
        direction_upper = direction.upper()
        if direction_upper in ('IN', 'OUT', 'TRANSFER'):
            conditions.append("ft.direction = :direction")
            params["direction"] = direction_upper
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Direction invalide: '{direction}'. Valeurs acceptées: IN, OUT, TRANSFER"
            )

    if category:
        conditions.append("ft.category = :category")
        params["category"] = category

    where_clause = " AND ".join(conditions)

    # Count total
    count_sql = f"""
        SELECT COUNT(*) as total
        FROM finance_transactions ft
        LEFT JOIN finance_transaction_classification class ON class.transaction_id = ft.id
        LEFT JOIN finance_categories cat ON cat.id = class.category_id
        WHERE {where_clause}
    """
    count_df = query_df(count_sql, params=params)
    total = int(count_df.iloc[0]['total']) if not count_df.empty else 0

    # Récupération des données
    sql = f"""
        SELECT
            ft.id,
            ft.date_operation as date,
            CAST(ft.amount AS NUMERIC) as amount,
            ft.label,
            ft.direction,
            cat.name as category,
            cat.id as category_id,
            CASE WHEN fr.id IS NOT NULL THEN true ELSE false END as reconciled
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        LEFT JOIN finance_transaction_classification class ON class.transaction_id = ft.id
        LEFT JOIN finance_categories cat ON cat.id = class.category_id
        WHERE {where_clause}
        ORDER BY ft.date_operation DESC, ft.id DESC
        LIMIT :limit OFFSET :offset
    """

    df = query_df(sql, params=params)

    transactions = []
    for _, row in df.iterrows():
        transactions.append(RecentTransaction(
            id=int(row['id']),
            date=row['date'],
            amount=float(row['amount']),
            label=row['label'] or '',
            direction=row['direction'],
            category=row.get('category'),
            category_id=row.get('category_id'),
            reconciled=bool(row['reconciled']),
        ))

    pages = (total + per_page - 1) // per_page if per_page > 0 else 0

    return TransactionListResponse(
        transactions=transactions,
        total=total,
        page=page,
        size=per_page,
        pages=pages,
    )


@router.post("/reconciliation/apply", response_model=ApplyReconciliationResponse, summary="Appliquer un rapprochement", tags=["newcms-finance"])
def apply_reconciliation_suggestion(
    request: ApplyReconciliationRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default)
) -> ApplyReconciliationResponse:
    """
    **Appliquer une suggestion de rapprochement IA**

    Endpoint pour valider et appliquer une suggestion de rapprochement générée par l'IA.
    Crée les liens dans la base de données et met à jour le statut des factures.

    ## Fonctionnement

    1. Vérifie l'existence de la transaction bancaire
    2. Vérifie l'existence de toutes les factures
    3. Crée les entrées dans `finance_reconciliations`
    4. Marque les factures comme PAID
    5. Retourne le résultat de l'opération

    ## Body de la requête

    - **suggestion_id**: ID de la suggestion (pour traçabilité)
    - **transaction_id**: ID de la transaction bancaire
    - **invoice_ids**: Liste des IDs de factures à rapprocher (min: 1)
    - **user_comment**: Commentaire optionnel de l'utilisateur (max: 500 caractères)

    ## Validations

    - Transaction doit exister
    - Toutes les factures doivent exister
    - Si facture déjà rapprochée, pas de duplication (ON CONFLICT DO NOTHING)

    ## Exemple de requête

    ```json
    {
      "suggestion_id": "ai-12345-1234567890",
      "transaction_id": 42,
      "invoice_ids": [100, 101],
      "user_comment": "Validation manuelle après vérification"
    }
    ```

    ## Tags
    - newcms-finance
    """
    try:
        entity_id = _get_entity_id(tenant.id)

        # Vérifier que la transaction existe
        tx_sql = """
            SELECT id, CAST(amount AS NUMERIC) as amount, label
            FROM finance_transactions
            WHERE id = :tx_id AND entity_id = :entity_id
        """
        tx_df = query_df(tx_sql, params={"tx_id": request.transaction_id, "entity_id": entity_id})

        if tx_df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {request.transaction_id} non trouvée"
            )

        # Vérifier que les factures existent
        inv_sql = """
            SELECT id, montant_ttc
            FROM finance_invoices_supplier
            WHERE id = ANY(:invoice_ids) AND entity_id = :entity_id
        """
        inv_df = query_df(inv_sql, params={"invoice_ids": request.invoice_ids, "entity_id": entity_id})

        if len(inv_df) != len(request.invoice_ids):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Une ou plusieurs factures non trouvées"
            )

        # Créer les rapprochements
        for invoice_id in request.invoice_ids:
            reconcile_sql = """
                INSERT INTO finance_reconciliations (transaction_id, invoice_id, matched_at, match_type)
                VALUES (:tx_id, :invoice_id, NOW(), 'ai_suggested')
                ON CONFLICT (transaction_id, invoice_id) DO NOTHING
            """
            exec_sql(reconcile_sql, params={
                "tx_id": request.transaction_id,
                "invoice_id": invoice_id,
            })

        # Marquer les factures comme payées
        update_inv_sql = """
            UPDATE finance_invoices_supplier
            SET status = 'PAID'
            WHERE id = ANY(:invoice_ids) AND entity_id = :entity_id
        """
        exec_sql(update_inv_sql, params={
            "invoice_ids": request.invoice_ids,
            "entity_id": entity_id,
        })

        return ApplyReconciliationResponse(
            success=True,
            transaction_id=request.transaction_id,
            invoice_ids=request.invoice_ids,
            reconciled_at=datetime.utcnow(),
            message=f"Rapprochement appliqué avec succès: {len(request.invoice_ids)} facture(s) rapprochée(s)",
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error applying reconciliation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'application du rapprochement: {str(exc)}"
        ) from exc


# =============================================================================
# Actions lignes transactions (catégoriser / ignorer / rapprochement manuel / export)
# =============================================================================


class CategorizeRequest(BaseModel):
    category: Optional[str] = None
    category_id: Optional[int] = None
    note: Optional[str] = None


class IgnoreRequest(BaseModel):
    reason: Optional[str] = None
    reversible: bool = True


class ManualReconcileRequest(BaseModel):
    invoice_ids: List[int]
    comment: Optional[str] = None


class ExportFilter(BaseModel):
    q: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    category: Optional[str] = None
    direction: Optional[str] = None


@router.post("/transactions/{transaction_id}/categorize", summary="Catégoriser une transaction", tags=["newcms-finance"])
def categorize_transaction(
    transaction_id: int,
    payload: CategorizeRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    _assert_transaction_exists(entity_id, transaction_id)
    if payload.category_id is None:
        raise HTTPException(status_code=400, detail="category_id requis")
    _upsert_classification(
        transaction_id,
        category_id=payload.category_id,
        source="manual",
        note=payload.note,
    )
    return {
        "success": True,
        "transaction_id": transaction_id,
        "category_id": payload.category_id,
        "category": payload.category,
        "note": payload.note,
        "tenant_id": tenant.id,
        "message": "Catégorie mise à jour",
    }


@router.post("/transactions/{transaction_id}/ignore", summary="Ignorer une transaction", tags=["newcms-finance"])
def ignore_transaction(
    transaction_id: int,
    payload: IgnoreRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    _assert_transaction_exists(entity_id, transaction_id)
    _upsert_classification(
        transaction_id,
        category_id=None,
        source="manual",
        ignored=True,
        note=payload.reason,
    )
    return {
        "success": True,
        "transaction_id": transaction_id,
        "ignored": True,
        "reversible": payload.reversible,
        "reason": payload.reason,
        "tenant_id": tenant.id,
        "message": "Transaction ignorée",
    }


@router.post("/transactions/{transaction_id}/reconcile-manual", summary="Rapprochement manuel", tags=["newcms-finance"])
def manual_reconcile_transaction(
    transaction_id: int,
    payload: ManualReconcileRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    if not payload.invoice_ids:
        raise HTTPException(status_code=400, detail="Au moins une facture est requise")
    entity_id = _get_entity_id(tenant.id)
    _assert_transaction_exists(entity_id, transaction_id)
    _upsert_classification(
        transaction_id,
        category_id=None,
        source="manual",
        rule_id=None,
        confidence=None,
        ignored=False,
        note=payload.comment,
    )
    _upsert_meta(transaction_id, {"manual_invoice_ids": payload.invoice_ids, "note": payload.comment})
    return {
        "success": True,
        "transaction_id": transaction_id,
        "invoice_ids": payload.invoice_ids,
        "comment": payload.comment,
        "tenant_id": tenant.id,
        "message": "Rapprochement manuel enregistré (simulation)",
    }


@router.post("/transactions/bulk-export", summary="Export CSV filtré", tags=["newcms-finance"])
def export_transactions(
    filters: ExportFilter,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    conditions = ["ft.entity_id = :entity_id"]
    params: dict[str, Any] = {"entity_id": entity_id}
    if filters.q:
        conditions.append("ft.label ILIKE :q")
        params["q"] = f"%{filters.q}%"
    if filters.date_from:
        conditions.append("ft.date_operation >= :date_from")
        params["date_from"] = filters.date_from
    if filters.date_to:
        conditions.append("ft.date_operation <= :date_to")
        params["date_to"] = filters.date_to
    if filters.amount_min is not None:
        conditions.append("ABS(CAST(ft.amount AS NUMERIC)) >= :amount_min")
        params["amount_min"] = filters.amount_min
    if filters.amount_max is not None:
        conditions.append("ABS(CAST(ft.amount AS NUMERIC)) <= :amount_max")
        params["amount_max"] = filters.amount_max
    if filters.direction:
        conditions.append("ft.direction = :direction")
        params["direction"] = filters.direction

    where_clause = " AND ".join(conditions)
    sql = f"""
        SELECT
            ft.id,
            ft.date_operation AS date,
            ft.label,
            ft.amount,
            ft.direction,
            cat.name AS category_name,
            cat.code AS category_code,
            class.ignored,
            CASE WHEN fr.id IS NOT NULL THEN true ELSE false END AS reconciled
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        LEFT JOIN finance_transaction_classification class ON class.transaction_id = ft.id
        LEFT JOIN finance_categories cat ON cat.id = class.category_id
        WHERE {where_clause}
        ORDER BY ft.date_operation DESC, ft.id DESC
        LIMIT 1000
    """
    _ensure_classification_table()
    df = query_df(sql, params=params)
    header = ["id", "date", "label", "amount", "direction", "category", "reconciled", "ignored"]
    rows = []
    for _, row in df.iterrows():
        category_value = row.get("category_name") or row.get("category_code") or ""
        rows.append([
            row.get("id"),
            row.get("date"),
            row.get("label"),
            row.get("amount"),
            row.get("direction"),
            category_value,
            row.get("reconciled"),
            row.get("ignored"),
        ])
    csv_lines = [",".join(header)]
    for r in rows:
        csv_lines.append(",".join([str(x) for x in r]))
    csv_content = "\n".join(csv_lines)
    return {
        "success": True,
        "tenant_id": tenant.id,
        "filters": filters.dict(),
        "csv": csv_content,
    }


# =============================================================================
# Règles de catégorisation (CRUD + apply) - stockage léger JSON
# =============================================================================


class FinanceRule(BaseModel):
    id: str
    name: str
    pattern: str
    category: str
    priority: int = 100
    enabled: bool = True


class FinanceRuleCreate(BaseModel):
    name: str
    pattern: Optional[str] = None
    category: str
    category_id: Optional[int] = None
    keywords: List[str] = Field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    apply_to_autre_only: bool = True
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    regex_pattern: Optional[str] = None


class ApplyRulesRequest(BaseModel):
    rule_ids: Optional[List[str]] = None
    dry_run: bool = True
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None


class FinanceCategoryResponse(PydanticBaseModel):
    id: int
    name: str
    code: Optional[str] = None
    type: Optional[str] = None


@router.get("/rules", summary="Lister les règles finance", tags=["newcms-finance"])
def list_finance_rules(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    rules = finance_rules.list_rules(entity_id=entity_id)
    return {"success": True, "rules": rules, "tenant_id": tenant.id}


@router.post("/rules", summary="Créer une règle finance", tags=["newcms-finance"])
def create_finance_rule(
    payload: FinanceRuleCreate,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    category_id = payload.category_id
    if category_id is None:
        raise HTTPException(status_code=400, detail="category_id requis pour créer une règle")
    db_rule = finance_rules.create_rule(
        CoreFinanceRuleCreate(
            entity_id=entity_id,
            category_id=category_id,
            name=payload.name,
            keywords=payload.keywords if hasattr(payload, "keywords") else [],
            apply_to_autre_only=getattr(payload, "apply_to_autre_only", True),
            is_active=getattr(payload, "enabled", True),
            amount_min=payload.amount_min,
            amount_max=payload.amount_max,
            regex_pattern=payload.regex_pattern,
        )
    )
    return {"success": True, "rule": db_rule}


@router.put("/rules/{rule_id}", summary="Mettre à jour une règle", tags=["newcms-finance"])
def update_finance_rule(
    rule_id: str,
    payload: FinanceRuleCreate,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    fields = payload.dict()
    try:
        updated = finance_rules.update_rule(int(rule_id), fields)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"success": True, "rule": updated}


@router.delete("/rules/{rule_id}", summary="Supprimer une règle", tags=["newcms-finance"])
def delete_finance_rule(
    rule_id: str,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    try:
        finance_rules.delete_rule(int(rule_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"success": True, "deleted": rule_id}


@router.post("/rules/apply", summary="Appliquer des règles de catégorisation", tags=["newcms-finance"])
def apply_finance_rules(
    payload: ApplyRulesRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    rules = finance_rules.list_rules(entity_id=entity_id, is_active=True)
    if payload.rule_ids:
        rules = [r for r in rules if str(r.get("id")) in set(payload.rule_ids)]

    # Pré-compiler les regex
    compiled_regex: dict[int, re.Pattern] = {}
    for rule in rules:
        pattern = rule.get("regex_pattern")
        if pattern:
            try:
                compiled_regex[rule["id"]] = re.compile(pattern, re.IGNORECASE)
            except re.error:
                continue

    # Cible: transactions; on récupère label/note/IBAN pour matcher
    tx_df = query_df(
        """
        SELECT
            ft.id,
            ft.label,
            ft.note,
            ft.amount,
            acc.iban AS account_iban,
            cacc.iban AS counterparty_iban
        FROM finance_transactions ft
        LEFT JOIN finance_accounts acc ON acc.id = ft.account_id
        LEFT JOIN finance_accounts cacc ON cacc.id = ft.counterparty_account_id
        WHERE ft.entity_id = :entity_id
        ORDER BY ft.date_operation DESC
        """,
        params={"entity_id": entity_id},
    )
    class_map = _get_classification_map([int(x) for x in tx_df["id"].tolist()]) if not tx_df.empty else {}

    applied: list[str] = []
    for _, row in tx_df.iterrows():
        tx_id = int(row["id"])
        label = (row.get("label") or "").lower()
        note = (row.get("note") or "").lower()
        iban = (row.get("account_iban") or "").lower()
        iban_cp = (row.get("counterparty_iban") or "").lower()
        existing_category = (class_map.get(tx_id, {}).get("category_code") or class_map.get(tx_id, {}).get("category_name") or "").lower()
        for rule in rules:
            # apply_to_autre_only: ne s'applique que si aucune catégorie ou catégorie AUTRE
            if rule.get("apply_to_autre_only") and existing_category not in ("", "autre"):
                continue
            matched = False
            amount = abs(float(row.get("amount") or 0))
            if rule.get("amount_min") is not None and amount < float(rule.get("amount_min")):
                continue
            if rule.get("amount_max") is not None and amount > float(rule.get("amount_max")):
                continue

            kws = rule.get("keywords") or []
            for kw in kws:
                kwl = kw.lower()
                if kwl in label or kwl in note or kwl in iban or kwl in iban_cp:
                    matched = True
                    break
            pattern = (rule.get("pattern") or rule.get("name") or "").lower()
            if pattern and (pattern in label or pattern in note or pattern in iban or pattern in iban_cp):
                matched = True
            if not matched and rule.get("id") in compiled_regex:
                regex = compiled_regex[rule["id"]]
                if regex.search(label) or regex.search(note) or regex.search(iban) or regex.search(iban_cp):
                    matched = True

            if matched:
                applied.append(str(rule.get("id")))
                if not payload.dry_run:
                    category_id = rule.get("category_id")
                    _upsert_classification(
                        tx_id,
                        category_id=category_id,
                        source="rule",
                        rule_id=rule.get("id"),
                        confidence=None,
                        ignored=False,
                        note=None,
                    )
                break

    return {
        "success": True,
        "applied_rule_ids": applied,
        "dry_run": payload.dry_run,
        "tenant_id": tenant.id,
        "processed_transactions": len(tx_df),
        "message": "Application des règles exécutée" if not payload.dry_run else "Simulation des règles exécutée",
    }


# =============================================================================
# Comptes bancaires (mock) pour CTA comptes
# =============================================================================


@router.get("/accounts", summary="Lister les comptes bancaires", tags=["newcms-finance"])
def list_accounts(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    accounts_df = query_df(
        """
        SELECT id, label, iban, currency, metadata
        FROM finance_accounts
        WHERE entity_id = :entity_id AND is_active = TRUE
        ORDER BY updated_at DESC
        """,
        params={"entity_id": entity_id},
    )
    balances_df = query_df(
        """
        SELECT DISTINCT ON (account_id) account_id, balance, date
        FROM finance_account_balances
        ORDER BY account_id, date DESC
        """
    )
    balance_map = {}
    if not balances_df.empty:
        for _, row in balances_df.iterrows():
            balance_map[int(row["account_id"])] = {"balance": float(row["balance"]), "date": str(row["date"])}
    accounts = []
    for _, row in accounts_df.iterrows():
        acc_id = int(row["id"])
        meta = row.get("metadata") or {}
        bal = balance_map.get(acc_id, {"balance": 0.0})
        accounts.append(
            {
                "id": acc_id,
                "name": row.get("label"),
                "iban": row.get("iban"),
                "currency": row.get("currency") or "EUR",
                "balance": bal.get("balance", 0.0),
                "balance_date": bal.get("date"),
                "metadata": meta,
            }
        )
    return {"success": True, "accounts": accounts, "tenant_id": tenant.id}


@router.post("/accounts/refresh", summary="Rafraîchir la synchro comptes", tags=["newcms-finance"])
def refresh_accounts(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    # Placeholder: marquer un timestamp de dernière synchro dans metadata
    return {"success": True, "tenant_id": tenant.id, "message": "Synchronisation lancée"}


@router.post("/accounts/simulate-cashflow", summary="Simuler un cashflow", tags=["newcms-finance"])
def simulate_cashflow(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> dict:
    entity_id = _get_entity_id(tenant.id)
    df = query_df(
        """
        SELECT date_operation as date, SUM(CAST(amount AS NUMERIC)) as delta
        FROM finance_transactions
        WHERE entity_id = :entity_id
          AND date_operation >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY date_operation
        ORDER BY date_operation
        """,
        params={"entity_id": entity_id},
    )
    balance = 0.0
    forecast = []
    for _, row in df.iterrows():
        balance += float(row["delta"] or 0)
        forecast.append({"date": str(row["date"]), "balance": round(balance, 2)})
    return {"success": True, "tenant_id": tenant.id, "forecast": forecast}


@router.get("/categories", summary="Lister les catégories finance", tags=["newcms-finance"], response_model=list[FinanceCategoryResponse])
def list_finance_categories(
    tenant: Tenant = Depends(get_current_tenant_or_default),
) -> list[FinanceCategoryResponse]:
    entity_id = _get_entity_id(tenant.id)
    entity_ids = {entity_id, 2, 3}
    df = query_df(
        """
        SELECT id, name, code, type
        FROM finance_categories
        WHERE entity_id IS NULL OR entity_id = ANY(:entity_ids)
        ORDER BY name
        """,
        params={"entity_ids": list(entity_ids)},
    )
    if df.empty:
        return []
    return [FinanceCategoryResponse(**row) for row in df.where(df.notna(), None).to_dict("records")]
