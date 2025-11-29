from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Connection

from core.data_repository import get_engine
from core.product_service import parse_barcode_input
from core.products_loader import insert_or_update_barcode


class CatalogServiceError(Exception):
    """Base exception for catalogue operations."""


class ProductNotFound(CatalogServiceError):
    """Raised when a product cannot be located."""


PRODUCT_COLUMNS = (
    "id, nom, tenant_id, prix_achat, prix_vente, tva, categorie, seuil_alerte, stock_actuel, actif"
)


def _row_to_dict(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, dict):
        return dict(row)
    return dict(row)


def _fetch_barcodes(conn: Connection, product_id: int, tenant_id: int) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT code
            FROM produits_barcodes
            WHERE produit_id = :pid AND tenant_id = :tenant_id
            ORDER BY code ASC
            """
        ),
        {"pid": product_id, "tenant_id": tenant_id},
    ).fetchall()
    return [str(row[0]) for row in rows]


def _derive_status(stock: float, seuil: float) -> str:
    if stock <= 0:
        return "critical"
    if seuil is None:
        return "ok"
    return "warning" if stock < seuil else "ok"


def list_products_page(
    tenant_id: int,
    *,
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> Tuple[list[dict[str, Any]], int]:
    page = max(1, page)
    per_page = max(1, min(per_page, 200))
    offset = (page - 1) * per_page

    where_clauses = ["tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}

    if search:
        where_clauses.append("LOWER(nom) LIKE :search")
        params["search"] = f"%{search.lower()}%"
    if category:
        where_clauses.append("categorie = :category")
        params["category"] = category
    if status:
        if status == "critical":
            where_clauses.append("stock_actuel <= 0")
        elif status == "warning":
            where_clauses.append("(stock_actuel > 0 AND seuil_alerte > 0 AND stock_actuel < seuil_alerte)")
        elif status == "ok":
            where_clauses.append("(stock_actuel > 0 AND (seuil_alerte = 0 OR stock_actuel >= seuil_alerte))")

    where_sql = "WHERE " + " AND ".join(where_clauses)
    base_sql = f"SELECT {PRODUCT_COLUMNS} FROM produits {where_sql}"

    with get_engine().begin() as conn:
        count_row = conn.execute(text(f"SELECT COUNT(*) FROM produits {where_sql}"), params).fetchone()
        total = int(count_row[0] if count_row else 0)

        rows = conn.execute(
            text(f"{base_sql} ORDER BY nom LIMIT :limit OFFSET :offset"),
            {**params, "limit": per_page, "offset": offset},
        ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            record = _row_to_dict(row)
            record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
            stock = float(record.get("stock_actuel") or 0)
            seuil = record.get("seuil_alerte")
            seuil_value = float(seuil) if seuil is not None else None
            record["status"] = _derive_status(stock, seuil_value if seuil_value is not None else 0)
            results.append(record)

        return results, total


def get_product(product_id: int, tenant_id: int) -> dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(f"SELECT {PRODUCT_COLUMNS} FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row:
            raise ProductNotFound(f"Produit {product_id} introuvable.")
        record = _row_to_dict(row)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record


def create_product(
    payload: dict[str, Any],
    *,
    tenant_id: int,
    codes: Iterable[str] | None = None,
) -> dict[str, Any]:
    codes = parse_barcode_input(codes or [])
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO produits
                (nom, tenant_id, prix_achat, prix_vente, tva, categorie, seuil_alerte, stock_actuel, actif)
                VALUES (:nom, :tenant_id, :prix_achat, :prix_vente, :tva, :categorie, :seuil_alerte, :stock_actuel, :actif)
                RETURNING {cols}
                """.format(cols=PRODUCT_COLUMNS)
            ),
            {**payload, "tenant_id": tenant_id},
        ).fetchone()
        if row is None:
            raise CatalogServiceError("Échec de la création produit (aucun ID retourné).")
        record = _row_to_dict(row)
        for code in codes:
            insert_or_update_barcode(conn, int(record["id"]), code, tenant_id=tenant_id)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record


def update_product(
    product_id: int,
    changes: dict[str, Any],
    codes: Iterable[str] | None = None,
    *,
    tenant_id: int,
) -> dict[str, Any]:
    if not changes and codes is None:
        return get_product(product_id, tenant_id=tenant_id)

    set_clauses = ", ".join(f"{col} = :{col}" for col in changes.keys())
    with get_engine().begin() as conn:
        if set_clauses:
            params = dict(changes)
            params["pid"] = product_id
            params["tenant_id"] = tenant_id
            result = conn.execute(
                text(
                    f"UPDATE produits SET {set_clauses}, updated_at = now() WHERE id = :pid AND tenant_id = :tenant_id"
                ),
                params,
            )
            if result.rowcount == 0:
                raise ProductNotFound(f"Produit {product_id} introuvable.")

        if codes is not None:
            desired = set(parse_barcode_input(codes))
            existing = set(_fetch_barcodes(conn, product_id, tenant_id))

            for code in existing - desired:
                conn.execute(
                    text(
                        """
                        DELETE FROM produits_barcodes
                        WHERE produit_id = :pid AND tenant_id = :tenant_id AND lower(code) = lower(:code)
                        """
                    ),
                    {"pid": product_id, "tenant_id": tenant_id, "code": code},
                )
            for code in desired - existing:
                insert_or_update_barcode(conn, product_id, code, tenant_id=tenant_id)

        return get_product(product_id, tenant_id=tenant_id)


def delete_product(product_id: int, *, tenant_id: int) -> None:
    with get_engine().begin() as conn:
        result = conn.execute(
            text("DELETE FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": tenant_id},
        )
        if result.rowcount == 0:
            raise ProductNotFound(f"Produit {product_id} introuvable.")


def get_product_by_barcode(barcode: str, *, tenant_id: int) -> dict[str, Any]:
    normalized_codes = parse_barcode_input([barcode])
    if not normalized_codes:
        raise ProductNotFound("Code-barres invalide.")
    canonical = normalized_codes[0]

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT {PRODUCT_COLUMNS}
                FROM produits p
                JOIN produits_barcodes pb ON p.id = pb.produit_id
                WHERE pb.code = :code AND p.tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"code": canonical, "tenant_id": tenant_id},
        ).fetchone()

        if not row:
            raise ProductNotFound("Aucun produit pour ce code-barres.")

        record = _row_to_dict(row)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record
