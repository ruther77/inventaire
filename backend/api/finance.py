"""Finance endpoints (reconciliation, anomalies, etc.)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies.tenant import Tenant, get_current_tenant
from backend.services import finance as finance_service
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
)

router = APIRouter(prefix="/finance", tags=["finance"])


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
    results = finance_service.list_matches(tenant.id, status=status)
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
    entries = finance_service.list_anomalies(tenant.id, severity=severity)
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
