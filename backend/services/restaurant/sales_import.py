"""Import restaurant sales from SumUp order CSVs.

This module ingests "rapport-de-commandes-produits" CSV files and stores
rows in restaurant_sales without touching stock movements.
"""

from __future__ import annotations

import csv
import hashlib
import io
import unicodedata
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import text

from core.data_repository import get_engine, query_df


_RAW_SYNONYMS: dict[str, str] = {
    "1/2 BLACK LABEL": "1/2 BLACK LABEL",
    "1/2 BLACL LABEL": "1/2 BLACK LABEL",
    "LEGUMES SAUTES POISSON FUME": "LEGUMES SAUTES POISSON FUME",
    "HEINEKEIN": "HEINEKEN (PETITE)",
    "GUINNESS": "GUINESS",
    "SUPPLEMENTS 3": "SUPPLEMENTS 3",
    "SUPPLEMENTS 5": "SUPPLEMENTS 5",
    "SUPPLEMENTS 10": "SUPPLEMENTS 10",
    "PRUNES 5": "PRUNES 5",
    "PRUNES 10": "PRUNES 10",
    "OEUF": "OEUF",
    "ROGNON SAUTEE 15": "ROGNON SAUTEE 15",
    "ROGNON SAUTEE 20": "ROGNON SAUTEE 20",
    "ROTI PORC": "ROTI PORC",
    "GINGER": "GINGER",
    "BOOSTER": "BOOSTER",
    "COCA": "COCA",
    "GLENFIDDICH": "GLENFIDDICH",
    "1/2 GLENFIDDICH": "1/2 GLENFIDDICH",
    "VIN 20": "VIN 20",
    "VIN 25": "VIN 25",
    "VIN 30": "VIN 30",
    "VIN 50": "VIN 50",
    "BEIGNET HARICOT": "BEIGNET HARICOT",
    "BEIGNET HARICOT VIANDE": "BEIGNET HARICOT VIANDE",
    "CONSO WHISKY": "CONSO WHISKY",
    "GESIER 15": "GESIER 15",
    "RAGOUT VIANDE": "RAGOUT VIANDE",
    "REDBULL": "REDBULL",
    "SALADE": "SALADE",
    "VODKA CONSO": "VODKA CONSO",
    "DESPERADOS": "GRANDE DESPERADOS",
    "GRANDE GUINESS": "GUINNESS (GRANDE)",
}


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _normalize_header(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.replace("\xa0", " ").strip()
    cleaned = " ".join(cleaned.split()).lower()
    return _strip_accents(cleaned)

def _normalize_name(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.replace("\xa0", " ").strip()
    cleaned = " ".join(cleaned.split())
    cleaned = _strip_accents(cleaned)
    return cleaned.upper()


_SYNONYMS = {
    _normalize_name(key): _normalize_name(value) for key, value in _RAW_SYNONYMS.items()
}


def _normalize_product_name(name: str) -> str:
    normalized = _normalize_name(name)
    return _SYNONYMS.get(normalized, normalized)


def _parse_french_decimal(value: str | None) -> Decimal:
    if not value:
        return Decimal("0")
    cleaned = value.strip().replace(",", ".").replace(" ", "").replace("\xa0", "")
    cleaned = _strip_accents(cleaned)
    try:
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")


def _parse_french_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = value.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _detect_delimiter(sample: str) -> str:
    return ";" if ";" in sample else ","


def _iter_sales_rows(content: bytes) -> Iterable[dict[str, Any]]:
    text_content = content.decode("utf-8-sig", errors="ignore")
    if not text_content.strip():
        return []

    sample = text_content.splitlines()[0] if text_content else ""
    delimiter = _detect_delimiter(sample)
    reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter, quotechar='"')

    for row in reader:
        normalized = {_normalize_header(k): v for k, v in row.items() if k}

        product = (normalized.get("produit") or normalized.get("product") or "").strip()
        if not product:
            continue

        quantity = _parse_french_decimal(
            normalized.get("quantite") or normalized.get("quantity")
        )
        if quantity <= 0:
            continue

        date_str = normalized.get("date fermeture") or normalized.get("date ouverture") or normalized.get("date")
        sold_at = _parse_french_datetime(date_str)
        if not sold_at:
            continue

        order_id = (normalized.get("id commande") or normalized.get("order id") or "").strip() or None

        yield {
            "product": product,
            "quantity": float(quantity),
            "sold_at": sold_at,
            "order_id": order_id,
        }


def _load_plat_mapping(tenant_id: int) -> dict[str, int]:
    df = query_df(
        text("SELECT id, nom FROM restaurant_plats WHERE tenant_id = :tenant"),
        {"tenant": int(tenant_id)},
    )
    if df.empty:
        return {}
    mapping: dict[str, int] = {}
    for _, row in df.iterrows():
        mapping[_normalize_name(row["nom"])] = int(row["id"])
    return mapping


def _hash_row(order_id: str | None, product: str, quantity: float, sold_at: datetime) -> str:
    base = f"{order_id or ''}|{product}|{quantity}|{sold_at.isoformat()}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def import_sales_csv_bytes(
    content: bytes,
    *,
    tenant_id: int,
    filename: str | None = None,
    source: str = "sumup_csv",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Import sales rows from a SumUp orders CSV into restaurant_sales.

    Returns a summary with counts and unmatched product examples.
    """
    plat_mapping = _load_plat_mapping(tenant_id)

    total_rows = 0
    valid_rows = 0
    unmapped_rows = 0

    prepared: list[dict[str, Any]] = []
    unmatched: dict[str, int] = {}

    period_start: datetime | None = None
    period_end: datetime | None = None

    for row in _iter_sales_rows(content):
        total_rows += 1
        sold_at = row["sold_at"]
        if period_start is None or sold_at < period_start:
            period_start = sold_at
        if period_end is None or sold_at > period_end:
            period_end = sold_at

        valid_rows += 1
        product = row["product"]
        normalized_name = _normalize_product_name(product)
        plat_id = plat_mapping.get(normalized_name)
        if not plat_id:
            unmapped_rows += 1
            unmatched[product] = unmatched.get(product, 0) + 1
            continue

        prepared.append(
            {
                "tenant_id": int(tenant_id),
                "plat_id": int(plat_id),
                "quantity": float(row["quantity"]),
                "sold_at": sold_at,
                "source": source,
                "source_ref": row.get("order_id"),
                "row_hash": _hash_row(row.get("order_id"), normalized_name, row["quantity"], sold_at),
            }
        )

    if total_rows == 0:
        return {
            "filename": filename,
            "rows_total": 0,
            "rows_valid": 0,
            "rows_invalid": 0,
            "rows_mapped": 0,
            "rows_unmapped": 0,
            "rows_inserted": 0,
            "rows_duplicates": 0,
            "period_start": None,
            "period_end": None,
            "unmapped_examples": [],
        }

    invalid_rows = 0

    if dry_run:
        return {
            "filename": filename,
            "rows_total": total_rows,
            "rows_valid": valid_rows,
            "rows_invalid": invalid_rows,
            "rows_mapped": len(prepared),
            "rows_unmapped": unmapped_rows,
            "rows_inserted": 0,
            "rows_duplicates": 0,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "unmapped_examples": _top_unmatched(unmatched),
        }

    inserted = 0
    rowcount_supported = True

    insert_sql = text(
        """
        INSERT INTO restaurant_sales (
            tenant_id,
            plat_id,
            quantity,
            sold_at,
            source,
            source_ref,
            row_hash
        ) VALUES (
            :tenant_id,
            :plat_id,
            :quantity,
            :sold_at,
            :source,
            :source_ref,
            :row_hash
        )
        ON CONFLICT (tenant_id, row_hash) DO NOTHING
        """
    )

    engine = get_engine()
    with engine.begin() as conn:
        if prepared:
            result = conn.execute(insert_sql, prepared)
            if result.rowcount is None or result.rowcount < 0:
                rowcount_supported = False
            else:
                inserted += result.rowcount

    if not rowcount_supported:
        inserted = len(prepared)

    duplicates = max(0, len(prepared) - inserted) if rowcount_supported else 0

    return {
        "filename": filename,
        "rows_total": total_rows,
        "rows_valid": valid_rows,
        "rows_invalid": invalid_rows,
        "rows_mapped": len(prepared),
        "rows_unmapped": unmapped_rows,
        "rows_inserted": inserted,
        "rows_duplicates": duplicates,
        "period_start": period_start.isoformat() if period_start else None,
        "period_end": period_end.isoformat() if period_end else None,
        "unmapped_examples": _top_unmatched(unmatched),
    }


def _top_unmatched(unmatched: dict[str, int], limit: int = 20) -> list[dict[str, Any]]:
    if not unmatched:
        return []
    items = sorted(unmatched.items(), key=lambda item: (-item[1], item[0]))
    return [{"product": name, "count": count} for name, count in items[:limit]]


__all__ = ["import_sales_csv_bytes"]
