"""Services pour la gestion des transactions financières et lignes analytiques."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from core.data_repository import get_engine, query_df
from backend.schemas.finance import (
    FinanceBatchCategorizeRequest,
    FinanceTransactionCreate,
    FinanceTransactionSearchResponse,
    FinanceTransactionUpdate,
)


def _validate_lines_amount(payload: FinanceTransactionCreate) -> None:
    if not payload.lines:
        return
    total = sum((line.montant_ttc or 0) for line in payload.lines)
    if payload.direction in {"OUT", "IN"} and abs(total - payload.amount) > 0.01:
        raise ValueError("La somme des lignes ne correspond pas au montant de la transaction.")


def create_transaction(payload: FinanceTransactionCreate) -> dict[str, Any]:
    """Crée une transaction et ses lignes dans une transaction DB unique."""

    if payload.direction == "TRANSFER" and not payload.counterparty_account_id:
        raise ValueError("counterparty_account_id requis pour un transfert.")

    _validate_lines_amount(payload)

    engine = get_engine()
    direction = payload.direction.upper()
    status = payload.status.upper() if payload.status else "CONFIRMED"

    with engine.begin() as conn:
        tx_row = conn.execute(
            text(
                """
                INSERT INTO finance_transactions (
                    entity_id,
                    account_id,
                    counterparty_account_id,
                    direction,
                    source,
                    date_operation,
                    date_value,
                    amount,
                    currency,
                    ref_externe,
                    note,
                    status
                ) VALUES (
                    :entity_id,
                    :account_id,
                    :counterparty_account_id,
                    :direction,
                    :source,
                    :date_operation,
                    :date_value,
                    :amount,
                    :currency,
                    :ref_externe,
                    :note,
                    :status
                )
                RETURNING id
                """
            ),
            {
                "entity_id": payload.entity_id,
                "account_id": payload.account_id,
                "counterparty_account_id": payload.counterparty_account_id,
                "direction": direction,
                "source": payload.source,
                "date_operation": payload.date_operation,
                "date_value": payload.date_value,
                "amount": payload.amount,
                "currency": payload.currency,
                "ref_externe": payload.ref_externe,
                "note": payload.note,
                "status": status,
            },
        ).fetchone()
        tx_id = int(tx_row[0])

        for idx, line in enumerate(payload.lines or [], start=1):
            conn.execute(
                text(
                    """
                    INSERT INTO finance_transaction_lines (
                        transaction_id,
                        category_id,
                        cost_center_id,
                        montant_ht,
                        tva_pct,
                        montant_ttc,
                        description,
                        position
                    ) VALUES (
                        :transaction_id,
                        :category_id,
                        :cost_center_id,
                        :montant_ht,
                        :tva_pct,
                        :montant_ttc,
                        :description,
                        :position
                    )
                    """
                ),
                {
                    "transaction_id": tx_id,
                    "category_id": line.category_id,
                    "cost_center_id": line.cost_center_id,
                    "montant_ht": line.montant_ht,
                    "tva_pct": line.tva_pct,
                    "montant_ttc": line.montant_ttc,
                    "description": line.description,
                    "position": line.position or idx,
                },
            )

    return {
        "id": tx_id,
        "entity_id": payload.entity_id,
        "account_id": payload.account_id,
        "direction": direction,
        "amount": payload.amount,
        "status": status,
    }


def list_transactions(
    *,
    entity_id: Optional[int] = None,
    account_id: Optional[int] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Filtre basique des transactions pour l'API."""

    clauses: list[str] = []
    params: dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    if account_id is not None:
        clauses.append("account_id = :account_id")
        params["account_id"] = int(account_id)
    if status:
        clauses.append("status = :status")
        params["status"] = status.upper()
    if date_from:
        clauses.append("date_operation >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("date_operation <= :date_to")
        params["date_to"] = date_to

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    df = query_df(
        text(
            f"""
            SELECT
                id,
                entity_id,
                account_id,
                counterparty_account_id,
                direction,
                source,
                date_operation,
                amount,
                currency,
                status,
                locked_at
            FROM finance_transactions
            {where_sql}
            ORDER BY date_operation DESC, id DESC
            """
        ),
        params=params or None,
    )
    return df.to_dict("records") if not df.empty else []


def update_transaction(transaction_id: int, payload: FinanceTransactionUpdate) -> dict[str, Any]:
    """Mise à jour note/statut si la transaction n'est pas verrouillée."""

    engine = get_engine()
    with engine.begin() as conn:
        locked = conn.execute(
            text("SELECT locked_at FROM finance_transactions WHERE id = :id"),
            {"id": int(transaction_id)},
        ).fetchone()
        if not locked:
            raise ValueError("Transaction introuvable.")
        if locked.locked_at:
            raise ValueError("Transaction verrouillée, modification interdite.")

        fields = []
        params: dict[str, Any] = {"id": int(transaction_id)}
        if payload.note is not None:
            fields.append("note = :note")
            params["note"] = payload.note
        if payload.status:
            fields.append("status = :status")
            params["status"] = payload.status.upper()
        if not fields:
            return {"id": transaction_id}

        conn.execute(
            text(f"UPDATE finance_transactions SET {', '.join(fields)}, updated_at = now() WHERE id = :id"),
            params,
        )

    return {"id": transaction_id, "status": payload.status, "note": payload.note}


def lock_transaction(transaction_id: int) -> dict[str, Any]:
    """Verrouille une transaction après rapprochement."""

    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                UPDATE finance_transactions
                SET locked_at = :locked_at
                WHERE id = :id AND locked_at IS NULL
                RETURNING id
                """
            ),
            {"id": int(transaction_id), "locked_at": datetime.utcnow()},
        ).fetchone()
        if not result:
            raise ValueError("Transaction introuvable ou déjà verrouillée.")
    return {"id": transaction_id, "locked": True}


# --- Recherche paginée et batch recatégorisation ---


def search_transactions(
    *,
    entity_id: Optional[int] = None,
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    q: Optional[str] = None,
    page: int = 1,
    size: int = 50,
    sort: str = "-date_operation",
) -> FinanceTransactionSearchResponse:
    """Recherche paginée sur les lignes de transaction (avec catégorie et libellé)."""

    safe_page = max(1, int(page))
    safe_size = max(1, min(int(size), 500))
    offset = (safe_page - 1) * safe_size

    clauses: list[str] = ["t.direction IN ('IN', 'OUT')"]
    params: Dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    if account_id is not None:
        clauses.append("t.account_id = :account_id")
        params["account_id"] = int(account_id)
    if category_id is not None:
        clauses.append("tl.category_id = :category_id")
        params["category_id"] = int(category_id)
    if date_from:
        clauses.append("t.date_operation >= :date_from")
        params["date_from"] = date_from
    if date_to:
        clauses.append("t.date_operation <= :date_to")
        params["date_to"] = date_to
    amount_expr = "COALESCE(tl.montant_ttc, tl.montant_ht, 0)"
    if amount_min is not None:
        clauses.append(f"{amount_expr} >= :amount_min")
        params["amount_min"] = float(amount_min)
    if amount_max is not None:
        clauses.append(f"{amount_expr} <= :amount_max")
        params["amount_max"] = float(amount_max)
    if q:
        clauses.append(
            "(COALESCE(b.libelle_banque, t.note, '') ILIKE :q OR COALESCE(t.note, '') ILIKE :q)"
        )
        params["q"] = f"%{q}%"

    where_sql = ""
    if clauses:
        where_sql = "WHERE " + " AND ".join(clauses)

    sort_map = {
        "date_operation": "t.date_operation ASC, tl.id ASC",
        "-date_operation": "t.date_operation DESC, tl.id DESC",
        "amount": f"{amount_expr} ASC, tl.id ASC",
        "-amount": f"{amount_expr} DESC, tl.id DESC",
        "category": "c.name ASC NULLS LAST, tl.id ASC",
        "-category": "c.name DESC NULLS LAST, tl.id DESC",
        "account": "a.label ASC NULLS LAST, tl.id ASC",
        "-account": "a.label DESC NULLS LAST, tl.id DESC",
    }
    order_by = sort_map.get(sort, sort_map["-date_operation"])

    base_select = f"""
        FROM finance_transaction_lines tl
        JOIN finance_transactions t ON t.id = tl.transaction_id
        JOIN finance_accounts a ON a.id = t.account_id
        LEFT JOIN finance_categories c ON c.id = tl.category_id
        LEFT JOIN LATERAL (
          SELECT b2.libelle_banque
          FROM finance_bank_statement_lines b2
          JOIN finance_bank_statements bs ON bs.id = b2.statement_id
          WHERE (
            (t.ref_externe LIKE 'stmtline:%' AND b2.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT))
            OR (
              (t.ref_externe IS NULL OR t.ref_externe = '' OR t.ref_externe NOT LIKE 'stmtline:%')
              AND bs.account_id = t.account_id
              AND b2.date_operation = t.date_operation
              AND ABS(ABS(b2.montant) - t.amount) < 0.01
            )
          )
          LIMIT 1
        ) b ON true
        {where_sql}
    """

    count_df = query_df(
        text(f"SELECT COUNT(*) AS total {base_select}"),
        params=params or None,
    )
    total = int(count_df.iloc[0]["total"]) if not count_df.empty else 0

    data_df = query_df(
        text(
            f"""
            SELECT
              tl.id AS line_id,
              t.id AS transaction_id,
              t.entity_id,
              t.account_id,
              a.label AS account_label,
              t.direction,
              t.source,
              t.date_operation,
              t.date_value,
              t.amount AS transaction_amount,
              {amount_expr} AS amount,
              tl.category_id,
              c.code AS category_code,
              c.name AS category_name,
              COALESCE(b.libelle_banque, t.note, '') AS label,
              t.currency,
              t.status
            {base_select}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
            """
        ),
        params={**params, "limit": safe_size, "offset": offset},
    )

    items = data_df.where(data_df.notna(), None).to_dict("records") if not data_df.empty else []
    return FinanceTransactionSearchResponse(
        items=items,
        page=safe_page,
        size=safe_size,
        total=total,
        sort=sort,
        filters_applied={
            "entity_id": entity_id,
            "account_id": account_id,
            "category_id": category_id,
            "date_from": date_from,
            "date_to": date_to,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "q": q,
        },
    )


def batch_categorize(payload: FinanceBatchCategorizeRequest) -> Dict[str, Any]:
    """Applique une catégorie à une liste d'IDs ou à un motif (keywords)."""

    if not payload.transaction_ids and not payload.rule:
        raise ValueError("transaction_ids ou rule est requis.")

    params: Dict[str, Any] = {"category_id": int(payload.category_id)}
    clauses: List[str] = []
    if payload.transaction_ids:
        clauses.append("tl.transaction_id = ANY(:tx_ids)")
        params["tx_ids"] = list({int(x) for x in payload.transaction_ids})

    if payload.rule:
        keywords = [kw.strip() for kw in payload.rule.keywords if kw.strip()]
        if not keywords:
            raise ValueError("Aucun mot-clé valide fourni pour la règle.")
        like_clauses = []
        for idx, kw in enumerate(keywords):
            key = f"kw{idx}"
            like_clauses.append(f"(COALESCE(b.libelle_banque, t.note, '') ILIKE :{key})")
            params[key] = f"%{kw}%"
        clauses.append("(" + " OR ".join(like_clauses) + ")")
        if payload.rule.apply_to_autre_only:
            clauses.append("c.code = 'autre'")

    where_sql = " AND ".join(clauses)
    if not where_sql:
        raise ValueError("Aucune condition appliquée pour la recatégorisation.")

    sql = text(
        f"""
        WITH target AS (
          SELECT tl.id
          FROM finance_transaction_lines tl
          JOIN finance_transactions t ON t.id = tl.transaction_id
          LEFT JOIN finance_categories c ON c.id = tl.category_id
          LEFT JOIN finance_bank_statement_lines b
            ON t.ref_externe LIKE 'stmtline:%'
           AND b.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
          WHERE {where_sql}
        )
        UPDATE finance_transaction_lines tl
        SET category_id = :category_id
        FROM target
        WHERE tl.id = target.id
        RETURNING tl.id
        """
    )

    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(sql, params).fetchall()
    updated = len(rows)
    return {"updated": updated, "category_id": int(payload.category_id)}


def suggest_autre_top(entity_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retourne les libellés fréquents restés en fourre-tout (ici frais_generaux)."""

    safe_limit = max(1, min(int(limit), 200))
    clauses = ["c.code = 'frais_generaux'"]
    params: Dict[str, Any] = {}
    if entity_id is not None:
        clauses.append("t.entity_id = :entity_id")
        params["entity_id"] = int(entity_id)
    where_sql = "WHERE " + " AND ".join(clauses)
    sql = text(
        f"""
        SELECT
          lower(regexp_replace(COALESCE(b.libelle_banque, t.note, ''), '\\s+', ' ', 'g')) AS key,
          COUNT(*) AS cnt,
          array_agg(DISTINCT COALESCE(b.libelle_banque, t.note, '') ORDER BY COALESCE(b.libelle_banque, t.note, '')) AS examples
        FROM finance_transaction_lines tl
        JOIN finance_transactions t ON t.id = tl.transaction_id
        LEFT JOIN finance_categories c ON c.id = tl.category_id
        LEFT JOIN finance_bank_statement_lines b
          ON t.ref_externe LIKE 'stmtline:%'
         AND b.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
        {where_sql}
        GROUP BY key
        ORDER BY cnt DESC
        LIMIT :limit
        """
    )
    df = query_df(sql, {**params, "limit": safe_limit})
    if df.empty:
        return []
    df = df.where(df.notna(), None)
    results: List[Dict[str, Any]] = []
    for row in df.to_dict("records"):
        examples = row.get("examples") or []
        if len(examples) > 3:
            examples = examples[:3]
        results.append({"key": row["key"], "count": int(row["cnt"]), "examples": examples})
    return results


def autocomplete_categories(q: str, entity_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Autocomplete sur les catégories (code/nom)."""

    safe_limit = max(1, min(int(limit), 100))
    params: Dict[str, Any] = {"limit": safe_limit, "q": f"%{q}%"}
    clause = ""
    if entity_id is not None:
        clause = "AND c.entity_id = :entity_id"
        params["entity_id"] = int(entity_id)
    sql = text(
        f"""
        SELECT c.id, c.code, c.name, c.type
        FROM finance_categories c
        WHERE (c.code ILIKE :q OR c.name ILIKE :q)
          {clause}
        ORDER BY c.name ASC NULLS LAST, c.code ASC
        LIMIT :limit
        """
    )
    df = query_df(sql, params)
    return df.where(df.notna(), None).to_dict("records") if not df.empty else []
