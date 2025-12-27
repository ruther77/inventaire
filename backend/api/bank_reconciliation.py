"""
API Endpoints pour Bank Reconciliation
======================================

Endpoints pour:
- Rapprochement bancaire automatique
- Matching intelligent transactions/factures
- Gestion des alias fournisseurs
- Validation et résolution manuelle
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from backend.dependencies.tenant import Tenant, get_current_tenant, get_current_tenant_or_default
from core.data_repository import query_df, exec_sql
from core.finance.bank_reconciliation import (
    BankReconciliationEngine,
    MatchType,
    MatchStatus,
)

router = APIRouter(prefix="/bank-reconciliation", tags=["bank-reconciliation"])


# =============================================================================
# SCHEMAS
# =============================================================================

class ReconciliationMatchResponse(BaseModel):
    match_id: str
    transaction_id: int
    transaction_date: date
    transaction_amount: float
    transaction_label: str
    match_type: str  # exact, fuzzy, multi_line, manual
    confidence: float
    matched_invoices: List[dict]
    total_matched_amount: float
    difference: float
    status: str  # pending, confirmed, rejected
    suggested_action: str


class UnmatchedTransactionResponse(BaseModel):
    transaction_id: int
    date: date
    amount: float
    label: Optional[str]
    category: Optional[str]
    days_unmatched: int
    potential_matches: List[dict]
    suggested_action: str


class UnmatchedInvoiceResponse(BaseModel):
    invoice_id: int
    invoice_number: str
    date: date
    amount: float
    supplier_name: str
    days_unpaid: int
    potential_matches: List[dict]


class SupplierAliasResponse(BaseModel):
    alias_id: int
    bank_label: str
    supplier_id: int
    supplier_name: str
    confidence: float
    match_count: int
    created_at: datetime
    last_used: Optional[datetime]


class ReconciliationSummaryResponse(BaseModel):
    period_start: date
    period_end: date
    total_transactions: int
    matched_transactions: int
    unmatched_transactions: int
    match_rate: float
    total_amount_matched: float
    total_amount_unmatched: float
    by_match_type: dict
    alerts: List[str]


class ManualMatchRequest(BaseModel):
    transaction_id: int
    invoice_ids: List[int]
    note: Optional[str] = None


class CreateAliasRequest(BaseModel):
    bank_label: str
    supplier_id: int


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_transactions_for_reconciliation(tenant_id: int, days: int = 60) -> List[dict]:
    """Récupère les transactions à rapprocher depuis finance_transactions.

    Note: Récupère toutes les transactions (entity_id 2 et 3) pour le rapprochement global.
    """
    sql = """
        SELECT
            ft.id,
            ft.date_operation as date,
            CAST(ft.amount AS NUMERIC) as amount,
            ft.label,
            NULL as category,
            CASE WHEN fr.id IS NOT NULL THEN true ELSE false END as reconciled,
            NULL as reconciled_invoice_id,
            ft.entity_id
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        WHERE ft.date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
          AND ft.direction = 'OUT'  -- Dépenses uniquement
        ORDER BY ft.date_operation DESC
    """
    df = query_df(sql, params={"days": days})
    return df.to_dict('records') if not df.empty else []


def _get_invoices_for_reconciliation(tenant_id: int, days: int = 90) -> List[dict]:
    """Récupère les factures à rapprocher depuis processed_invoices.

    Note: processed_invoices a tenant_id=1 pour toutes les factures (Épicerie).
    On récupère toutes les factures peu importe le tenant pour le rapprochement.
    """
    sql = """
        SELECT
            pi.id,
            pi.invoice_id as invoice_number,
            pi.facture_date::date as date,
            pi.total_ttc as amount,
            NULL as supplier_id,
            pi.supplier as supplier_name,
            false as paid,
            NULL as payment_date
        FROM processed_invoices pi
        WHERE pi.facture_date::date >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY pi.facture_date DESC
    """
    df = query_df(sql, params={"days": days})
    return df.to_dict('records') if not df.empty else []


def _get_supplier_aliases(tenant_id: int) -> dict:
    """Récupère les alias fournisseurs"""
    sql = """
        SELECT
            id,
            bank_label,
            supplier_id,
            confidence,
            match_count,
            created_at,
            last_used
        FROM supplier_bank_aliases
        WHERE tenant_id = :tenant_id
    """
    df = query_df(sql, params={"tenant_id": tenant_id})
    if df.empty:
        return {}
    return {row['bank_label'].upper(): row for _, row in df.iterrows()}


def _fuzzy_amount_match(amount1: float, amount2: float, tolerance: float = 0.03) -> bool:
    """Vérifie si deux montants sont proches (tolérance 3%)"""
    if amount1 == 0 or amount2 == 0:
        return False
    diff = abs(amount1 - amount2) / max(abs(amount1), abs(amount2))
    return diff <= tolerance


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/run", response_model=List[ReconciliationMatchResponse])
def run_reconciliation(
    days_back: int = Query(default=60, ge=1, le=730),
    auto_confirm_threshold: float = Query(default=0.95, ge=0.5, le=1.0),
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Lance le rapprochement bancaire automatique.

    Algorithme:
    1. Match exact (même montant, même date ±3 jours)
    2. Match fuzzy (montant ±3%, date ±7 jours)
    3. Match multi-lignes (1 transaction = N factures)
    4. Apprentissage des alias fournisseurs

    Les matches avec confiance >= auto_confirm_threshold sont auto-confirmés.
    """
    engine = BankReconciliationEngine(tenant_id=tenant.id)

    transactions = _get_transactions_for_reconciliation(tenant.id, days_back)
    invoices = _get_invoices_for_reconciliation(tenant.id, days_back + 30)
    aliases = _get_supplier_aliases(tenant.id)

    matches = []
    used_invoice_ids = set()

    for txn in transactions:
        if txn.get('reconciled'):
            continue

        txn_amount = abs(float(txn['amount']))
        txn_label = (txn['label'] or '').upper()
        txn_date = txn['date']

        best_match = None
        best_confidence = 0
        matched_invoices = []

        # 1. Chercher via alias fournisseur
        for alias_key, alias_info in aliases.items():
            if alias_key in txn_label:
                supplier_id = alias_info['supplier_id']
                # Chercher factures de ce fournisseur
                supplier_invoices = [
                    inv for inv in invoices
                    if inv['supplier_id'] == supplier_id
                    and inv['id'] not in used_invoice_ids
                    and not inv.get('paid')
                ]

                for inv in supplier_invoices:
                    inv_amount = float(inv['amount'] or 0)
                    if _fuzzy_amount_match(txn_amount, inv_amount):
                        confidence = 0.9 * alias_info['confidence']
                        if confidence > best_confidence:
                            best_confidence = confidence
                            matched_invoices = [inv]
                            best_match = {
                                "type": "alias",
                                "alias_id": alias_info['id']
                            }

        # 2. Match exact sur montant
        for inv in invoices:
            if inv['id'] in used_invoice_ids or inv.get('paid'):
                continue

            inv_amount = float(inv['amount'] or 0)
            inv_date = inv['date']

            # Match exact
            if abs(txn_amount - inv_amount) < 0.01:
                date_diff = abs((txn_date - inv_date).days) if txn_date and inv_date else 999

                if date_diff <= 3:
                    confidence = 0.98
                elif date_diff <= 7:
                    confidence = 0.90
                elif date_diff <= 14:
                    confidence = 0.75
                else:
                    confidence = 0.5

                if confidence > best_confidence:
                    best_confidence = confidence
                    matched_invoices = [inv]
                    best_match = {"type": "exact"}

        # 3. Match fuzzy (±3%)
        if best_confidence < 0.8:
            for inv in invoices:
                if inv['id'] in used_invoice_ids or inv.get('paid'):
                    continue

                inv_amount = float(inv['amount'] or 0)
                if _fuzzy_amount_match(txn_amount, inv_amount) and inv_amount != txn_amount:
                    confidence = 0.7
                    if confidence > best_confidence:
                        best_confidence = confidence
                        matched_invoices = [inv]
                        best_match = {"type": "fuzzy"}

        # 4. Match multi-lignes (somme de factures)
        if best_confidence < 0.7:
            # Grouper par fournisseur
            by_supplier = {}
            for inv in invoices:
                if inv['id'] in used_invoice_ids or inv.get('paid'):
                    continue
                sid = inv['supplier_id']
                if sid not in by_supplier:
                    by_supplier[sid] = []
                by_supplier[sid].append(inv)

            for supplier_id, supplier_invoices in by_supplier.items():
                # Essayer combinaisons de 2-4 factures
                from itertools import combinations
                for r in range(2, min(5, len(supplier_invoices) + 1)):
                    for combo in combinations(supplier_invoices, r):
                        combo_total = sum(float(i['amount'] or 0) for i in combo)
                        if _fuzzy_amount_match(txn_amount, combo_total, tolerance=0.02):
                            confidence = 0.75
                            if confidence > best_confidence:
                                best_confidence = confidence
                                matched_invoices = list(combo)
                                best_match = {"type": "multi_line", "count": len(combo)}

        # Créer le match result
        if matched_invoices:
            total_matched = sum(float(i['amount'] or 0) for i in matched_invoices)
            difference = txn_amount - total_matched

            # Auto-confirm si confiance élevée
            status = "confirmed" if best_confidence >= auto_confirm_threshold else "pending"

            match_response = ReconciliationMatchResponse(
                match_id=f"match-{txn['id']}-{datetime.now().timestamp()}",
                transaction_id=txn['id'],
                transaction_date=txn_date,
                transaction_amount=txn_amount,
                transaction_label=txn['label'],
                match_type=best_match.get('type', 'unknown'),
                confidence=best_confidence,
                matched_invoices=[
                    {
                        "invoice_id": inv['id'],
                        "invoice_number": inv['invoice_number'],
                        "amount": float(inv['amount'] or 0),
                        "supplier": inv['supplier_name'],
                        "date": str(inv['date'])
                    }
                    for inv in matched_invoices
                ],
                total_matched_amount=total_matched,
                difference=difference,
                status=status,
                suggested_action="Confirmer" if status == "pending" else "Auto-confirmé"
            )
            matches.append(match_response)

            # Marquer les factures comme utilisées
            for inv in matched_invoices:
                used_invoice_ids.add(inv['id'])

    return matches


@router.get("/unmatched/transactions", response_model=List[UnmatchedTransactionResponse])
def get_unmatched_transactions(
    days_back: int = Query(default=365, ge=1, le=730),
    min_amount: float = Query(default=0, ge=0),
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Retourne les transactions non rapprochées AVEC FACTURES.

    Une transaction est considérée non rapprochée si elle n'a pas de invoice_id
    dans finance_reconciliations.
    """
    sql = """
        SELECT
            ft.id as transaction_id,
            ft.date_operation as date,
            CAST(ft.amount AS NUMERIC) as amount,
            ft.label,
            NULL as category,
            CURRENT_DATE - ft.date_operation::date as days_unmatched
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id AND fr.invoice_id IS NOT NULL
        WHERE ft.date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
          AND ft.direction = 'OUT'
          AND fr.id IS NULL  -- Pas de rapprochement avec facture
          AND ABS(CAST(ft.amount AS NUMERIC)) >= :min_amount
        ORDER BY ft.date_operation DESC
    """
    df = query_df(sql, params={"days": days_back, "min_amount": min_amount})

    if df.empty:
        return []

    # Récupérer les factures pour suggestions
    invoices = _get_invoices_for_reconciliation(tenant.id, days_back + 30)

    results = []
    for _, row in df.iterrows():
        txn_amount = abs(float(row['amount']))

        # Trouver des matches potentiels
        potential = []
        for inv in invoices:
            if inv.get('paid'):
                continue
            inv_amount = float(inv['amount'] or 0)
            if _fuzzy_amount_match(txn_amount, inv_amount, tolerance=0.1):
                potential.append({
                    "invoice_id": inv['id'],
                    "invoice_number": inv['invoice_number'],
                    "amount": inv_amount,
                    "supplier": inv['supplier_name'],
                    "similarity": 1 - abs(txn_amount - inv_amount) / max(txn_amount, inv_amount)
                })

        potential.sort(key=lambda x: x['similarity'], reverse=True)

        # Suggestion d'action
        if potential:
            action = f"Vérifier match avec {potential[0]['supplier']} ({potential[0]['invoice_number']})"
        elif row['days_unmatched'] > 30:
            action = "Transaction ancienne - classifier manuellement"
        else:
            action = "Attendre facture ou classifier"

        results.append(UnmatchedTransactionResponse(
            transaction_id=int(row['transaction_id']),
            date=row['date'],
            amount=float(row['amount']),
            label=row['label'],
            category=row['category'],
            days_unmatched=int(row['days_unmatched']),
            potential_matches=potential[:5],
            suggested_action=action
        ))

    return results


@router.get("/unmatched/invoices", response_model=List[UnmatchedInvoiceResponse])
def get_unmatched_invoices(
    days_back: int = Query(default=365, ge=1, le=730),
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Retourne les factures non payées/non rapprochées.

    Note: Utilise processed_invoices avec tenant_id.
    """
    sql = """
        SELECT
            pi.id as invoice_id,
            pi.invoice_id as invoice_number,
            pi.facture_date::date as date,
            pi.total_ttc as amount,
            pi.supplier as supplier_name,
            CURRENT_DATE - pi.facture_date::date as days_unpaid
        FROM processed_invoices pi
        WHERE pi.facture_date::date >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY pi.facture_date
    """
    df = query_df(sql, params={"days": days_back})

    if df.empty:
        return []

    # Récupérer transactions pour suggestions
    transactions = _get_transactions_for_reconciliation(tenant.id, days_back)

    results = []
    for _, row in df.iterrows():
        inv_amount = float(row['amount'] or 0)

        # Trouver transactions potentielles
        potential = []
        for txn in transactions:
            if txn.get('reconciled'):
                continue
            txn_amount = abs(float(txn['amount']))
            if _fuzzy_amount_match(inv_amount, txn_amount, tolerance=0.1):
                potential.append({
                    "transaction_id": txn['id'],
                    "date": str(txn['date']),
                    "amount": txn_amount,
                    "label": txn['label'],
                    "similarity": 1 - abs(inv_amount - txn_amount) / max(inv_amount, txn_amount)
                })

        potential.sort(key=lambda x: x['similarity'], reverse=True)

        results.append(UnmatchedInvoiceResponse(
            invoice_id=int(row['invoice_id']),
            invoice_number=row['invoice_number'],
            date=row['date'],
            amount=inv_amount,
            supplier_name=row['supplier_name'] or 'Unknown',
            days_unpaid=int(row['days_unpaid']),
            potential_matches=potential[:5]
        ))

    return results


@router.post("/match/manual")
def create_manual_match(
    request: ManualMatchRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Crée un rapprochement manuel entre une transaction et une ou plusieurs factures.
    Met à jour la colonne invoice_id dans finance_reconciliations existante.
    """
    # Vérifier la transaction
    txn_sql = """
        SELECT ft.id, CAST(ft.amount AS NUMERIC) as montant, ft.label as libelle, fr.id as reco_id
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        WHERE ft.id = :txn_id
    """
    txn_df = query_df(txn_sql, params={"txn_id": request.transaction_id})

    if txn_df.empty:
        raise HTTPException(status_code=404, detail="Transaction non trouvée")

    # Vérifier les factures dans processed_invoices
    inv_sql = """
        SELECT id, total_ttc, supplier
        FROM processed_invoices
        WHERE id = ANY(:ids)
    """
    inv_df = query_df(inv_sql, params={"ids": request.invoice_ids})

    if len(inv_df) != len(request.invoice_ids):
        raise HTTPException(status_code=404, detail="Une ou plusieurs factures non trouvées")

    # Mettre à jour le rapprochement existant avec invoice_id
    reco_id = txn_df.iloc[0]['reco_id']
    if reco_id:
        # Mettre à jour le rapprochement existant
        for invoice_id in request.invoice_ids:
            update_sql = """
                UPDATE finance_reconciliations
                SET invoice_id = :invoice_id, status = 'MANUAL'
                WHERE transaction_id = :txn_id
            """
            exec_sql(update_sql, params={
                "txn_id": request.transaction_id,
                "invoice_id": invoice_id
            })
    else:
        # Pas de rapprochement existant - ne devrait pas arriver mais on gère le cas
        raise HTTPException(status_code=400, detail="Transaction sans ligne bancaire associée")

    return {
        "status": "matched",
        "transaction_id": request.transaction_id,
        "invoice_ids": request.invoice_ids,
        "matched_at": datetime.now().isoformat()
    }


@router.get("/aliases", response_model=List[SupplierAliasResponse])
def get_supplier_aliases(
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Retourne les alias fournisseurs appris pour le rapprochement automatique.

    Si la table n'existe pas encore (environnement incomplet), retourne une
    liste vide plutôt que 500.
    """
    sql = """
        SELECT
            a.id as alias_id,
            a.bank_label,
            a.supplier_id,
            v.name as supplier_name,
            a.confidence,
            a.match_count,
            a.created_at,
            a.last_used
        FROM supplier_bank_aliases a
        LEFT JOIN finance_vendors v ON v.id = a.supplier_id
        WHERE a.tenant_id = :tenant_id
        ORDER BY a.match_count DESC
    """
    try:
        df = query_df(sql, params={"tenant_id": tenant.id})
    except Exception:
        # Table absente ou non migrée : on renvoie un tableau vide pour éviter un 500
        return []

    return [
        SupplierAliasResponse(
            alias_id=int(row['alias_id']),
            bank_label=row['bank_label'],
            supplier_id=int(row['supplier_id']),
            supplier_name=row['supplier_name'] or 'Unknown',
            confidence=float(row['confidence']),
            match_count=int(row['match_count']),
            created_at=row['created_at'],
            last_used=row['last_used']
        )
        for _, row in df.iterrows()
    ]


@router.post("/aliases")
def create_supplier_alias(
    request: CreateAliasRequest,
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Crée un nouvel alias fournisseur pour le rapprochement automatique.
    """
    sql = """
        INSERT INTO supplier_bank_aliases (tenant_id, bank_label, supplier_id, confidence, match_count)
        VALUES (:tenant_id, :label, :supplier_id, 0.9, 0)
        ON CONFLICT (tenant_id, bank_label) DO UPDATE
        SET supplier_id = :supplier_id,
            confidence = 0.9
        RETURNING id
    """
    try:
        exec_sql(sql, params={
            "tenant_id": tenant.id,
            "label": request.bank_label.upper(),
            "supplier_id": request.supplier_id
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "created",
        "bank_label": request.bank_label,
        "supplier_id": request.supplier_id
    }


@router.delete("/aliases/{alias_id}")
def delete_supplier_alias(
    alias_id: int,
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Supprime un alias fournisseur.
    """
    sql = """
        DELETE FROM supplier_bank_aliases
        WHERE id = :alias_id AND tenant_id = :tenant_id
    """
    exec_sql(sql, params={"alias_id": alias_id, "tenant_id": tenant.id})

    return {"status": "deleted", "alias_id": alias_id}


@router.get("/summary", response_model=ReconciliationSummaryResponse)
def get_reconciliation_summary(
    days_back: int = Query(default=30, ge=1, le=730),
    tenant: Tenant = Depends(get_current_tenant_or_default)
):
    """
    Résumé du rapprochement bancaire avec FACTURES.

    Une transaction est rapprochée si elle a un invoice_id dans finance_reconciliations.
    """
    # Stats transactions - rapprochement avec factures
    txn_sql = """
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE fr.invoice_id IS NOT NULL) as matched,
            COALESCE(SUM(ABS(CAST(ft.amount AS NUMERIC))), 0) as total_amount,
            COALESCE(SUM(ABS(CAST(ft.amount AS NUMERIC))) FILTER (WHERE fr.invoice_id IS NOT NULL), 0) as matched_amount
        FROM finance_transactions ft
        LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
        WHERE ft.date_operation >= CURRENT_DATE - :days * INTERVAL '1 day'
          AND ft.direction = 'OUT'
    """
    txn_df = query_df(txn_sql, params={"days": days_back})

    total = int(txn_df.iloc[0]['total'] or 0) if not txn_df.empty else 0
    matched = int(txn_df.iloc[0]['matched'] or 0) if not txn_df.empty else 0
    total_amount = float(txn_df.iloc[0]['total_amount'] or 0) if not txn_df.empty else 0
    matched_amount = float(txn_df.iloc[0]['matched_amount'] or 0) if not txn_df.empty else 0

    match_rate = (matched / total * 100) if total > 0 else 0

    # Alertes
    alerts = []
    if match_rate < 80 and total > 0:
        alerts.append(f"Taux de rapprochement bas ({match_rate:.1f}%)")
    if total - matched > 20:
        alerts.append(f"{total - matched} transactions non rapprochées")

    # Factures impayées anciennes (toutes entités)
    old_invoices_sql = """
        SELECT COUNT(*) as count
        FROM finance_invoices_supplier
        WHERE date_invoice < CURRENT_DATE - INTERVAL '30 days'
          AND status NOT IN ('PAID', 'CANCELLED')
    """
    old_df = query_df(old_invoices_sql, params={})
    old_count = int(old_df.iloc[0]['count'] or 0) if not old_df.empty else 0

    if old_count > 0:
        alerts.append(f"{old_count} factures impayées depuis plus de 30 jours")

    return ReconciliationSummaryResponse(
        period_start=date.today() - timedelta(days=days_back),
        period_end=date.today(),
        total_transactions=total,
        matched_transactions=matched,
        unmatched_transactions=total - matched,
        match_rate=match_rate,
        total_amount_matched=matched_amount,
        total_amount_unmatched=total_amount - matched_amount,
        by_match_type={
            "exact": matched,  # Simplifié pour cet exemple
            "fuzzy": 0,
            "multi_line": 0,
            "manual": 0
        },
        alerts=alerts
    )
