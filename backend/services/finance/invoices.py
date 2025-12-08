"""Services factures fournisseurs (fournisseurs, factures, paiements)."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import text

from core.data_repository import exec_sql_return_id, get_engine, query_df
from backend.schemas.finance import FinanceInvoiceCreate, FinanceInvoiceLineCreate, FinancePaymentCreate, FinanceVendorCreate


def create_vendor(payload: FinanceVendorCreate) -> dict[str, Any]:
    vendor_id = exec_sql_return_id(
        text(
            """
            INSERT INTO finance_vendors (
                entity_id,
                name,
                siret,
                iban,
                bic,
                contact_email,
                contact_phone,
                address,
                metadata,
                is_active
            ) VALUES (
                :entity_id,
                :name,
                :siret,
                :iban,
                :bic,
                :contact_email,
                :contact_phone,
                :address,
                :metadata,
                :is_active
            )
            RETURNING id
            """
        ),
        params=payload.dict(),
    )
    return {"id": vendor_id, "name": payload.name, "entity_id": payload.entity_id}


def list_vendors(entity_id: Optional[int] = None, is_active: Optional[bool] = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    if is_active is not None:
        clauses.append("is_active = :is_active")
        params["is_active"] = bool(is_active)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    df = query_df(
        text(
            f"""
            SELECT id, entity_id, name, siret, iban, bic, contact_email, contact_phone, is_active
            FROM finance_vendors
            {where_sql}
            ORDER BY name
            """
        ),
        params=params or None,
    )
    return df.to_dict("records") if not df.empty else []


def _compute_amounts_from_lines(lines: list[FinanceInvoiceLineCreate]) -> tuple[Optional[float], Optional[float], Optional[float]]:
    if not lines:
        return None, None, None
    total_ht = 0.0
    total_ttc = 0.0
    total_tva = 0.0
    for line in lines:
        ht = line.montant_ht or 0
        ttc = line.montant_ttc or ht
        tva_pct = line.tva_pct or 0
        total_ht += ht
        total_ttc += ttc
        total_tva += ttc - ht if tva_pct else 0
    return total_ht, total_tva, total_ttc


def create_invoice(payload: FinanceInvoiceCreate) -> dict[str, Any]:
    status = payload.status.upper() if payload.status else "EN_ATTENTE"
    lines = payload.lines or []
    computed_ht, computed_tva, computed_ttc = _compute_amounts_from_lines(lines)
    montant_ttc = payload.montant_ttc if payload.montant_ttc is not None else computed_ttc
    montant_ht = payload.montant_ht if payload.montant_ht is not None else computed_ht
    montant_tva = payload.montant_tva if payload.montant_tva is not None else computed_tva

    engine = get_engine()
    with engine.begin() as conn:
        invoice_row = conn.execute(
            text(
                """
                INSERT INTO finance_invoices_supplier (
                    entity_id,
                    vendor_id,
                    invoice_number,
                    date_invoice,
                    date_due,
                    montant_ht,
                    montant_tva,
                    montant_ttc,
                    status,
                    source,
                    currency,
                    ref_externe,
                    metadata
                ) VALUES (
                    :entity_id,
                    :vendor_id,
                    :invoice_number,
                    :date_invoice,
                    :date_due,
                    :montant_ht,
                    :montant_tva,
                    :montant_ttc,
                    :status,
                    :source,
                    :currency,
                    :ref_externe,
                    :metadata
                )
                RETURNING id
                """
            ),
            {
                "entity_id": payload.entity_id,
                "vendor_id": payload.vendor_id,
                "invoice_number": payload.invoice_number,
                "date_invoice": payload.date_invoice,
                "date_due": payload.date_due,
                "montant_ht": montant_ht,
                "montant_tva": montant_tva,
                "montant_ttc": montant_ttc,
                "status": status,
                "source": payload.source,
                "currency": payload.currency,
                "ref_externe": payload.ref_externe,
                "metadata": payload.metadata,
            },
        ).fetchone()
        invoice_id = int(invoice_row[0])

        for idx, line in enumerate(lines, start=1):
            conn.execute(
                text(
                    """
                    INSERT INTO finance_invoice_lines_supplier (
                        invoice_id,
                        category_id,
                        description,
                        quantite,
                        prix_unitaire,
                        montant_ht,
                        tva_pct,
                        montant_ttc,
                        position
                    ) VALUES (
                        :invoice_id,
                        :category_id,
                        :description,
                        :quantite,
                        :prix_unitaire,
                        :montant_ht,
                        :tva_pct,
                        :montant_ttc,
                        :position
                    )
                    """
                ),
                {
                    "invoice_id": invoice_id,
                    "category_id": line.category_id,
                    "description": line.description,
                    "quantite": line.quantite,
                    "prix_unitaire": line.prix_unitaire,
                    "montant_ht": line.montant_ht,
                    "tva_pct": line.tva_pct,
                    "montant_ttc": line.montant_ttc or line.montant_ht,
                    "position": line.position or idx,
                },
            )

    return {
        "id": invoice_id,
        "entity_id": payload.entity_id,
        "vendor_id": payload.vendor_id,
        "status": status,
        "montant_ttc": montant_ttc,
    }


def create_payment(payload: FinancePaymentCreate) -> dict[str, Any]:
    payment_id = exec_sql_return_id(
        text(
            """
            INSERT INTO finance_payments (
                invoice_id,
                transaction_id,
                amount,
                date_payment,
                mode,
                currency
            ) VALUES (
                :invoice_id,
                :transaction_id,
                :amount,
                :date_payment,
                :mode,
                :currency
            )
            RETURNING id
            """
        ),
        params=payload.dict(),
    )
    return {"id": payment_id, "invoice_id": payload.invoice_id, "transaction_id": payload.transaction_id}


def search_invoices(
    *,
    entity_id: Optional[int] = None,
    vendor_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    sort: str = "-date_invoice",
) -> dict[str, Any]:
    """Recherche paginée sur les factures fournisseurs."""

    safe_page = max(1, int(page))
    safe_size = max(1, min(int(size), 500))
    offset = (safe_page - 1) * safe_size

    clauses: list[str] = []
    params: dict[str, Any] = {}

    if entity_id is not None:
        clauses.append("inv.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    if vendor_id is not None:
        clauses.append("inv.vendor_id = :vendor_id")
        params["vendor_id"] = int(vendor_id)
    if status:
        clauses.append("inv.status = :status")
        params["status"] = status.upper()
    if date_from:
        clauses.append("inv.date_invoice >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("inv.date_invoice <= :date_to")
        params["date_to"] = date_to

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    # Define sort mapping
    sort_map = {
        "date_invoice": "inv.date_invoice ASC NULLS LAST, inv.id ASC",
        "-date_invoice": "inv.date_invoice DESC NULLS LAST, inv.id DESC",
        "date_due": "inv.date_due ASC NULLS LAST, inv.id ASC",
        "-date_due": "inv.date_due DESC NULLS LAST, inv.id DESC",
        "montant_ttc": "inv.montant_ttc ASC NULLS LAST, inv.id ASC",
        "-montant_ttc": "inv.montant_ttc DESC NULLS LAST, inv.id DESC",
        "vendor": "v.name ASC, inv.id ASC",
        "-vendor": "v.name DESC, inv.id DESC",
        "status": "inv.status ASC, inv.id ASC",
        "-status": "inv.status DESC, inv.id DESC",
    }
    order_by = sort_map.get(sort, sort_map["-date_invoice"])

    base_select = f"""
        FROM finance_invoices_supplier inv
        JOIN finance_vendors v ON v.id = inv.vendor_id
        LEFT JOIN finance_entities e ON e.id = inv.entity_id
        {where_sql}
    """

    # Count total
    count_df = query_df(
        text(f"SELECT COUNT(*) AS total {base_select}"),
        params=params or None,
    )
    total = int(count_df.iloc[0]["total"]) if not count_df.empty else 0

    # Get data
    data_df = query_df(
        text(
            f"""
            SELECT
                inv.id,
                inv.entity_id,
                e.name AS entity_name,
                inv.vendor_id,
                v.name AS vendor_name,
                inv.invoice_number,
                inv.date_invoice,
                inv.date_due,
                inv.montant_ht,
                inv.montant_tva,
                inv.montant_ttc,
                inv.status,
                inv.source,
                inv.currency,
                inv.ref_externe,
                inv.created_at,
                inv.updated_at,
                (
                    SELECT COALESCE(SUM(p.amount), 0)
                    FROM finance_payments p
                    WHERE p.invoice_id = inv.id
                ) AS total_paid,
                (
                    SELECT COUNT(*)
                    FROM finance_invoice_lines_supplier il
                    WHERE il.invoice_id = inv.id
                ) AS line_count
            {base_select}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
            """
        ),
        params={**params, "limit": safe_size, "offset": offset},
    )

    items = data_df.where(data_df.notna(), None).to_dict("records") if not data_df.empty else []

    return {
        "items": items,
        "page": safe_page,
        "size": safe_size,
        "total": total,
        "sort": sort,
        "filters_applied": {
            "entity_id": entity_id,
            "vendor_id": vendor_id,
            "status": status,
            "date_from": date_from,
            "date_to": date_to,
        },
    }
