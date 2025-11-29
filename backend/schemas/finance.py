"""Finance schemas for reconciliation endpoints."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class FinanceRunRequest(BaseModel):
    amount_tolerance: float = Field(2.0, ge=0, description="Tolérance absolue sur le montant (euros).")
    max_days_difference: int = Field(10, ge=0, description="Écart max en jours entre facture et paiement.")
    auto_threshold: float = Field(0.9, ge=0, le=1, description="Score minimal pour valider automatiquement.")


class FinanceRunResponse(BaseModel):
    run_id: int
    statements_scanned: int
    documents_available: int
    matches_created: int
    auto_matches: int


class BankStatementProjection(BaseModel):
    id: int
    date: date
    label: str
    amount: float
    account: Optional[str] = None
    category: Optional[str] = None


class InvoiceDocumentProjection(BaseModel):
    id: int
    reference: str
    invoice_number: Optional[str] = None
    supplier_name: str
    invoice_date: date
    total_incl_tax: Optional[float] = None
    total_excl_tax: Optional[float] = None


class FinanceMatch(BaseModel):
    id: int
    status: str
    match_type: str
    score: float
    amount_diff: float
    days_diff: int
    explanation: Optional[str] = None
    bank: BankStatementProjection
    invoice: InvoiceDocumentProjection


class FinanceMatchStatusRequest(BaseModel):
    status: str = Field(..., description="Nouveau statut (pending/auto/confirmed/rejected).")
    note: Optional[str] = Field(default=None, description="Commentaire optionnel.")


class RecurringRefreshRequest(BaseModel):
    min_occurrences: int = Field(3, ge=1, description="Nombre minimal d'occurrences pour considérer une récurrence.")


class RecurringRefreshResponse(BaseModel):
    recurring_expenses: int


class FinanceRecurringExpense(BaseModel):
    id: int
    normalized_label: str
    sample_label: str
    account: Optional[str]
    category: Optional[str]
    periodicity: str
    occurrences: int
    avg_amount: Optional[float]
    std_amount: Optional[float]
    first_date: Optional[date]
    last_date: Optional[date]


class AnomalyRefreshRequest(BaseModel):
    zscore_threshold: float = Field(2.5, ge=1.0, description="Z-score minimal pour flagger une anomalie.")
    min_occurrences: int = Field(3, ge=1, description="Occurrences min pour construire une bande.")


class AnomalyRefreshResponse(BaseModel):
    anomalies: int


class FinanceAnomaly(BaseModel):
    id: int
    rule: str
    severity: str
    message: Optional[str]
    score: Optional[float]
    amount: Optional[float]
    expected_amount: Optional[float]
    statement_id: int
    statement_date: date
    statement_label: str
    statement_account: Optional[str]
    statement_category: Optional[str]
