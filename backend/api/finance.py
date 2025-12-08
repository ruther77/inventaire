"""Finance endpoints (reconciliation, anomalies, etc.)."""

from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi import UploadFile, File

from backend.dependencies.tenant import Tenant, get_current_tenant
from backend.services.finance import core as finance_service
from backend.services.finance import accounts as finance_accounts
from backend.services.finance import transactions as finance_transactions
from backend.services.finance import invoices as finance_invoices
from backend.services.finance import bank_statements as finance_bank_statements
from backend.services.finance import reconciliation as finance_reconciliation
from backend.services.finance import rules as finance_rules
from backend.services.finance import imports as finance_imports
from backend.services.finance import metrics as finance_metrics
from backend.services.finance import stats as finance_stats
from backend.services.finance import dashboard as finance_dashboard
from backend.services.finance import categories as finance_categories
from backend.services.finance import cost_centers as finance_cost_centers
from backend.services.importers import bank_statement_csv
from backend.schemas.finance import (
    FinanceMatch,
    FinanceMatchStatusRequest,
    FinanceRunRequest,
    FinanceRunResponse,
    BankStatementProjection,
    InvoiceDocumentProjection,
    RecurringRefreshRequest,
    RecurringRefreshResponse,
    FinanceRecurringExpense,
    AnomalyRefreshRequest,
    AnomalyRefreshResponse,
    FinanceAnomaly,
    FinanceAccountCreate,
    FinanceTransactionCreate,
    FinanceTransactionUpdate,
    FinanceVendorCreate,
    FinanceInvoiceCreate,
    FinancePaymentCreate,
    FinanceReconciliationCreate,
    FinanceBatchCategorizeRequest,
    FinanceAutreSuggestion,
    FinanceTransactionSearchResponse,
    FinanceBankStatementSearchResponse,
    FinanceInvoiceSearchResponse,
    FinanceCategoryCreate,
    FinanceCostCenterCreate,
)
from backend.schemas.finance_rules import FinanceRule, FinanceRuleCreate

router = APIRouter(prefix="/finance", tags=["finance"])
logger = logging.getLogger(__name__)


# --- Comptes ---


@router.post("/accounts")
def create_account(
    payload: FinanceAccountCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_accounts.create_account(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/accounts")
def list_accounts(
    entity_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_accounts.list_accounts(entity_id=entity_id, is_active=is_active)


@router.get("/accounts/{account_id}")
def get_account(
    account_id: int,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    account = finance_accounts.get_account(account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Compte introuvable")
    return account


@router.put("/accounts/{account_id}")
def update_account(
    account_id: int,
    payload: dict,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_accounts.update_account(account_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/accounts/{account_id}")
def delete_account(
    account_id: int,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        finance_accounts.delete_account(account_id)
        return {"success": True, "message": "Compte supprime ou desactive"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Transactions ---


@router.post("/transactions")
def create_transaction(
    payload: FinanceTransactionCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_transactions.create_transaction(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/transactions")
def list_transactions(
    entity_id: int | None = Query(default=None),
    account_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_transactions.list_transactions(
        entity_id=entity_id,
        account_id=account_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/transactions/search", response_model=FinanceTransactionSearchResponse)
def search_transactions(
    entity_id: int | None = Query(default=None),
    account_id: int | None = Query(default=None),
    category_id: int | None = Query(default=None),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    amount_min: float | None = Query(default=None),
    amount_max: float | None = Query(default=None),
    q: str | None = Query(default=None, description="Recherche texte sur libellé/note"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-date_operation", description="date_operation|amount|category|account avec - pour desc"),
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceTransactionSearchResponse:
    return finance_transactions.search_transactions(
        entity_id=entity_id,
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        q=q,
        page=page,
        size=size,
        sort=sort,
    )


@router.patch("/transactions/{transaction_id}")
def update_transaction(
    transaction_id: int,
    payload: FinanceTransactionUpdate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_transactions.update_transaction(transaction_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/transactions/{transaction_id}/lock")
def lock_transaction(
    transaction_id: int,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_transactions.lock_transaction(transaction_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Fournisseurs / factures / paiements ---


@router.post("/vendors")
def create_vendor(
    payload: FinanceVendorCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_invoices.create_vendor(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/vendors")
def list_vendors(
    entity_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_invoices.list_vendors(entity_id=entity_id, is_active=is_active)


@router.post("/invoices")
def create_invoice(
    payload: FinanceInvoiceCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_invoices.create_invoice(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/invoices/search", response_model=FinanceInvoiceSearchResponse)
def search_invoices(
    entity_id: int | None = Query(default=None),
    vendor_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-date_invoice", description="date_invoice|date_due|montant_ttc|vendor|status avec - pour desc"),
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceInvoiceSearchResponse:
    result = finance_invoices.search_invoices(
        entity_id=entity_id,
        vendor_id=vendor_id,
        status=status_filter,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
        sort=sort,
    )
    return FinanceInvoiceSearchResponse(**result)


@router.post("/payments")
def create_payment(
    payload: FinancePaymentCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_invoices.create_payment(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Suggestions / catégorisation rapide ---


@router.get("/categories/suggestions/autre-top", response_model=list[FinanceAutreSuggestion])
def suggest_autre_top(
    entity_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceAutreSuggestion]:
    return finance_transactions.suggest_autre_top(entity_id=entity_id, limit=limit)


@router.get("/categories")
def list_categories(
    entity_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_categories.list_categories(entity_id=entity_id, is_active=is_active)


@router.post("/categories")
def create_category(
    payload: FinanceCategoryCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_categories.create_category(
            entity_id=payload.entity_id,
            code=payload.code,
            name=payload.name,
            type_=payload.type,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Centres de coûts ---


@router.get("/cost-centers")
def list_cost_centers(
    entity_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_cost_centers.list_cost_centers(entity_id=entity_id, is_active=is_active)


@router.post("/cost-centers")
def create_cost_center(
    payload: FinanceCostCenterCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_cost_centers.create_cost_center(
            entity_id=payload.entity_id,
            code=payload.code,
            name=payload.name,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/categories/suggestions/complete")
def autocomplete_categories(
    q: str = Query(..., min_length=1),
    entity_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_transactions.autocomplete_categories(q=q, entity_id=entity_id, limit=limit)


@router.post("/transactions/batch-categorize")
def batch_categorize_transactions(
    payload: FinanceBatchCategorizeRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_transactions.batch_categorize(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


# --- Règles de catégorisation ---


@router.get("/rules", response_model=list[FinanceRule])
def list_rules(
    entity_id: int | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceRule]:
    return finance_rules.list_rules(entity_id=entity_id, is_active=is_active)


@router.post("/rules", response_model=FinanceRule)
def create_rule(payload: FinanceRuleCreate, tenant: Tenant = Depends(get_current_tenant)) -> FinanceRule:
    return finance_rules.create_rule(payload)


@router.patch("/rules/{rule_id}", response_model=FinanceRule)
def update_rule(
    rule_id: int,
    payload: dict,
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceRule:
    try:
        return finance_rules.update_rule(rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int, tenant: Tenant = Depends(get_current_tenant)) -> dict:
    try:
        return finance_rules.delete_rule(rule_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/imports")
def list_imports(tenant: Tenant = Depends(get_current_tenant)) -> list[dict]:
    return finance_imports.list_imports()


# --- Stats catégories / comptes ---


@router.get("/categories/stats")
def categories_stats(
    entity_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_stats.categories_stats(entity_id=entity_id)


@router.get("/accounts/overview")
def accounts_overview(
    entity_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    return finance_stats.accounts_overview(entity_id=entity_id)


@router.get("/dashboard/summary")
def finance_dashboard_summary(
    entity_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    return finance_dashboard.dashboard_summary(entity_id=entity_id)


@router.post("/stats/refresh")
def refresh_stats_cache(
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    """Rafraîchit les vues matérialisées des stats finance."""
    return finance_stats.refresh_materialized_views()


@router.get("/stats/timeline")
def get_timeline_stats(
    entity_id: int | None = Query(default=None),
    months: int | None = Query(default=12, description="Nombre de mois (null=tout)"),
    granularity: str = Query(default="monthly", description="daily|weekly|monthly"),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    """Retourne la chronologie agrégée des flux pour les graphiques."""
    return finance_stats.timeline_stats(
        entity_id=entity_id,
        months=months,
        granularity=granularity,
    )


@router.get("/stats/category-breakdown")
def get_category_breakdown(
    entity_id: int | None = Query(default=None),
    months: int | None = Query(default=12, description="Nombre de mois (null=tout)"),
    direction: str | None = Query(default=None, description="IN|OUT|null pour les deux"),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[dict]:
    """Retourne la répartition par catégorie pour les pie/bar charts."""
    return finance_stats.category_breakdown(
        entity_id=entity_id,
        months=months,
        direction=direction,
    )


@router.get("/stats/treasury")
def get_treasury_summary(
    entity_id: int | None = Query(default=None),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    """Retourne un résumé de trésorerie (totaux, solde, période)."""
    return finance_stats.treasury_summary(entity_id=entity_id)


# --- Rapprochements (nouvelles tables finance_bank_statement_lines / finance_transactions) ---


@router.post("/reconciliations")
def create_reconciliation(
    payload: FinanceReconciliationCreate,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        return finance_reconciliation.create_reconciliation(
            payload.statement_line_id,
            payload.transaction_id,
            status=payload.status,
            created_by=tenant.id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/reconciliations/{reconciliation_id}")
def delete_reconciliation(
    reconciliation_id: int,
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        finance_reconciliation.delete_reconciliation(reconciliation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return {"id": reconciliation_id, "deleted": True}


@router.get("/bank-statements/search", response_model=FinanceBankStatementSearchResponse)
def search_bank_statements(
    account_id: int | None = Query(default=None),
    period_start: str | None = Query(default=None),
    period_end: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-imported_at", description="imported_at|period_start|period_end|account avec - pour desc"),
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceBankStatementSearchResponse:
    result = finance_bank_statements.search_bank_statements(
        account_id=account_id,
        period_start=period_start,
        period_end=period_end,
        status=status_filter,
        page=page,
        size=size,
        sort=sort,
    )
    return FinanceBankStatementSearchResponse(**result)


@router.post("/bank-statements/import")
async def import_bank_statements(
    account_id: int = Query(..., description="ID du compte finance_accounts"),
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
) -> dict:
    try:
        content = await file.read()
        summary = bank_statement_csv.import_csv(content, account_id=account_id, source=file.filename or "CSV")
        finance_rules.record_import(account_id=account_id, file_name=file.filename or "CSV", summary=summary, error=None)
        finance_metrics.record_import_metrics(
            account_id=account_id,
            inserted=summary.get("inserted"),
            total=summary.get("total"),
            status="DONE",
            error=None,
        )
        return summary
    except ValueError as exc:
        finance_rules.record_import(account_id=account_id, file_name=file.filename or "CSV", summary=None, error=str(exc))
        finance_metrics.record_import_metrics(
            account_id=account_id,
            inserted=None,
            total=None,
            status="ERROR",
            error=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/reconciliation/run", response_model=FinanceRunResponse)
def run_reconciliation(
    payload: FinanceRunRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceRunResponse:
    summary = finance_service.run_reconciliation(
        tenant.id,
        amount_tolerance=payload.amount_tolerance,
        max_days_difference=payload.max_days_difference,
        auto_threshold=payload.auto_threshold,
    )
    finance_metrics.record_reco_run(summary)
    return FinanceRunResponse(**summary)


def _build_match(record: dict) -> FinanceMatch:
    bank = BankStatementProjection(
        id=record["bank_id"],
        date=record["bank_date"],
        label=record["bank_label"],
        amount=float(record.get("bank_raw_amount") or record.get("bank_amount") or 0),
        account=record.get("bank_account"),
        category=record.get("bank_category"),
    )
    invoice = InvoiceDocumentProjection(
        id=record["document_id"],
        reference=record["invoice_reference"],
        invoice_number=record.get("invoice_number"),
        supplier_name=record["supplier_name"],
        invoice_date=record["invoice_date"],
        total_incl_tax=record.get("total_incl_tax"),
        total_excl_tax=record.get("total_excl_tax"),
    )
    return FinanceMatch(
        id=record["id"],
        status=record["status"],
        match_type=record["match_type"],
        score=float(record["score"]),
        amount_diff=float(record["amount_diff"]),
        days_diff=int(record["days_diff"]),
        explanation=record.get("explanation"),
        bank=bank,
        invoice=invoice,
    )


@router.get("/reconciliation/matches", response_model=list[FinanceMatch])
def list_matches(
    status: str | None = Query(default="pending", description="Filtrer par statut."),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceMatch]:
    try:
        results = finance_service.list_matches(tenant.id, status=status)
    except Exception as exc:  # defensive fallback when optional tables are absent
        logger.warning("finance matches unavailable: %s", exc)
        return []
    return [_build_match(record) for record in results]


@router.post("/reconciliation/{match_id}/status", response_model=FinanceMatch)
def update_match_status(
    match_id: int,
    payload: FinanceMatchStatusRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> FinanceMatch:
    try:
        record = finance_service.update_match_status(
            tenant.id,
            match_id,
            status=payload.status,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _build_match(record)


@router.post("/recurring/refresh", response_model=RecurringRefreshResponse)
def refresh_recurring(
    payload: RecurringRefreshRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> RecurringRefreshResponse:
    summary = finance_service.refresh_recurring(tenant.id, min_occurrences=payload.min_occurrences)
    return RecurringRefreshResponse(**summary)


@router.get("/recurring", response_model=list[FinanceRecurringExpense])
def list_recurring(
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceRecurringExpense]:
    entries = finance_service.list_recurring(tenant.id)
    return [FinanceRecurringExpense(**entry) for entry in entries]


@router.post("/anomalies/refresh", response_model=AnomalyRefreshResponse)
def refresh_anomalies(
    payload: AnomalyRefreshRequest,
    tenant: Tenant = Depends(get_current_tenant),
) -> AnomalyRefreshResponse:
    summary = finance_service.refresh_anomalies(
        tenant.id,
        zscore_threshold=payload.zscore_threshold,
        min_occurrences=payload.min_occurrences,
    )
    return AnomalyRefreshResponse(**summary)


@router.get("/anomalies", response_model=list[FinanceAnomaly])
def list_anomalies(
    severity: str | None = Query(default=None, description="Filtrer par sévérité."),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceAnomaly]:
    try:
        entries = finance_service.list_anomalies(tenant.id, severity=severity)
    except Exception as exc:  # optional table may be absent on some tenants
        logger.warning("finance anomalies unavailable: %s", exc)
        entries = []
    return [
        FinanceAnomaly(
            id=entry["id"],
            rule=entry["rule"],
            severity=entry["severity"],
            message=entry.get("message"),
            score=entry.get("score"),
            amount=entry.get("amount"),
            expected_amount=entry.get("expected_amount"),
            statement_id=entry["statement_id"],
            statement_date=entry["statement_date"],
            statement_label=entry["statement_label"],
            statement_account=entry.get("statement_account"),
            statement_category=entry.get("statement_category"),
        )
        for entry in entries
    ]


@router.get("/reconciliation/runs/{run_id}/anomalies", response_model=list[FinanceAnomaly])
def get_reconciliation_run_anomalies(
    run_id: int,
    severity: str | None = Query(default=None, description="Filtrer par sévérité."),
    tenant: Tenant = Depends(get_current_tenant),
) -> list[FinanceAnomaly]:
    """
    Retourne les anomalies détectées pour un run de rapprochement spécifique.

    Note: Dans l'implémentation actuelle, les anomalies sont stockées par tenant.
    Ce endpoint filtre les anomalies par tenant et sévérité. Le run_id peut être
    utilisé pour des filtres futurs si la table est étendue avec un champ run_id.
    """
    try:
        entries = finance_service.list_anomalies(tenant.id, severity=severity)
    except Exception as exc:
        logger.warning("finance anomalies unavailable for run %s: %s", run_id, exc)
        entries = []

    return [
        FinanceAnomaly(
            id=entry["id"],
            rule=entry["rule"],
            severity=entry["severity"],
            message=entry.get("message"),
            score=entry.get("score"),
            amount=entry.get("amount"),
            expected_amount=entry.get("expected_amount"),
            statement_id=entry["statement_id"],
            statement_date=entry["statement_date"],
            statement_label=entry["statement_label"],
            statement_account=entry.get("statement_account"),
            statement_category=entry.get("statement_category"),
        )
        for entry in entries
    ]
