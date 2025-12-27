"""
Module des schémas Pydantic pour le domaine finance.

Ce module définit tous les modèles de données (request/response) pour:
- Rapprochement bancaire automatique (matching)
- Comptes financiers et transactions
- Factures et paiements fournisseurs
- Catégories et centres de coûts
- Détection d'anomalies et dépenses récurrentes
- Relevés bancaires et imports
- Règles de catégorisation
- Statistiques et tableaux de bord

Organisation:
Les schémas sont organisés par fonctionnalité:
1. Comptes et transactions (FinanceAccount*, FinanceTransaction*)
2. Factures et paiements (FinanceInvoice*, FinancePayment*)
3. Rapprochement (FinanceMatch*, FinanceRun*)
4. Anomalies et récurrence (FinanceAnomaly*, FinanceRecurring*)
5. Catégories et analytique (FinanceCategory*, FinanceCostCenter*)
6. Recherche et pagination (*SearchResponse)

Validation:
Tous les schémas incluent:
- Validation de types avec Pydantic v2
- Contraintes métier (montants >= 0, dates cohérentes, etc.)
- Validators personnalisés pour logique complexe
- Documentation inline des champs (Field(..., description="..."))
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


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


# --- Nouvelle refonte trésorerie (comptes, transactions, factures) ---


class FinanceAccountCreate(BaseModel):
    entity_id: int
    type: str
    label: str
    iban: Optional[str] = None
    bic: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    is_active: bool = True
    metadata: Optional[dict] = None


class FinanceTransactionLineCreate(BaseModel):
    category_id: int
    cost_center_id: Optional[int] = None
    montant_ht: Optional[float] = Field(default=None, ge=0)
    tva_pct: Optional[float] = Field(default=None, ge=0)
    montant_ttc: float = Field(..., ge=0)
    description: Optional[str] = None
    position: int = Field(default=1, ge=1)


class FinanceTransactionCreate(BaseModel):
    entity_id: int
    account_id: int
    direction: str
    source: str
    date_operation: date
    amount: float = Field(..., gt=0)
    date_value: Optional[date] = None
    counterparty_account_id: Optional[int] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    ref_externe: Optional[str] = None
    note: Optional[str] = None
    status: str = "CONFIRMED"
    lines: list[FinanceTransactionLineCreate] = Field(default_factory=list)

    @field_validator("direction")
    def _validate_direction(cls, value: str) -> str:
        allowed = {"IN", "OUT", "TRANSFER"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"direction doit être dans {allowed}")
        return upper

    @field_validator("currency")
    def _validate_currency(cls, value: str) -> str:
        code = value.upper()
        if len(code) != 3:
            raise ValueError("currency doit être un code ISO à 3 lettres")
        return code


class FinanceVendorCreate(BaseModel):
    entity_id: Optional[int] = None
    name: str
    siret: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    metadata: Optional[dict] = None
    is_active: bool = True


class FinanceInvoiceLineCreate(BaseModel):
    category_id: int
    description: Optional[str] = None
    quantite: Optional[float] = Field(default=None, ge=0)
    prix_unitaire: Optional[float] = Field(default=None, ge=0)
    montant_ht: Optional[float] = Field(default=None, ge=0)
    tva_pct: Optional[float] = Field(default=None, ge=0)
    montant_ttc: Optional[float] = Field(default=None, ge=0)
    position: int = Field(default=1, ge=1)


class FinanceInvoiceCreate(BaseModel):
    entity_id: int
    vendor_id: int
    invoice_number: str
    date_invoice: Optional[date] = None
    date_due: Optional[date] = None
    montant_ht: Optional[float] = Field(default=None, ge=0)
    montant_tva: Optional[float] = Field(default=None, ge=0)
    montant_ttc: Optional[float] = Field(default=None, ge=0)
    status: str = "EN_ATTENTE"
    source: Optional[str] = None
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    ref_externe: Optional[str] = None
    metadata: Optional[dict] = None
    lines: list[FinanceInvoiceLineCreate] = Field(default_factory=list)


# --- Recherche / suggestions / batch recat ---


class FinanceTransactionSearchResponse(BaseModel):
    items: list["FinanceTransactionSearchItem"]
    page: int
    size: int
    total: int
    sort: str
    filters_applied: dict[str, object]


class FinanceAutreSuggestion(BaseModel):
    key: str
    count: int
    examples: List[str] = Field(default_factory=list)


class FinanceTransactionSearchItem(BaseModel):
    id: int
    transaction_id: int
    line_id: Optional[int] = None
    entity_id: Optional[int] = None
    account_id: Optional[int] = None
    account_label: Optional[str] = None
    direction: Optional[str] = None
    source: Optional[str] = None
    date_operation: Optional[date] = None
    date_value: Optional[date] = None
    transaction_amount: Optional[float] = None
    amount: Optional[float] = None
    category_id: Optional[int] = None
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    cost_center_id: Optional[int] = None
    cost_center_name: Optional[str] = None
    label: Optional[str] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    ai_confidence: Optional[float] = None
    classification_source: Optional[str] = None
    locked_at: Optional[datetime] = None


class FinanceBatchCategorizeRule(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    apply_to_autre_only: bool = True


class FinanceBatchCategorizeRequest(BaseModel):
    category_id: int
    transaction_ids: Optional[List[int]] = None
    rule: Optional[FinanceBatchCategorizeRule] = None


class FinancePaymentCreate(BaseModel):
    invoice_id: Optional[int] = None
    transaction_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    date_payment: date
    mode: str
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class FinanceTransactionUpdate(BaseModel):
    note: Optional[str] = None
    status: Optional[str] = None


class FinanceReconciliationCreate(BaseModel):
    statement_line_id: int
    transaction_id: int
    status: str = "AUTO"


# --- Schemas paginés pour UI ---


class FinanceBankStatementSearchResponse(BaseModel):
    items: list[dict]
    page: int
    size: int
    total: int
    sort: str
    filters_applied: dict[str, object]


class FinanceInvoiceSearchResponse(BaseModel):
    items: list[dict]
    page: int
    size: int
    total: int
    sort: str
    filters_applied: dict[str, object]


# --- Catégories et centres de coûts ---


class FinanceCategoryCreate(BaseModel):
    entity_id: int
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    type: str = Field(default="EXPENSE", description="EXPENSE ou INCOME")


class FinanceCostCenterCreate(BaseModel):
    entity_id: int
    code: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
