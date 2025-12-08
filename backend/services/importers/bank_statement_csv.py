"""Import CSV de relevés bancaires vers les tables finance_bank_statements/lines."""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import date
from typing import Any, Iterable

from sqlalchemy import text

from core.data_repository import get_engine, query_df


def _parse_amount(value: str) -> float:
    cleaned = value.replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_date(value: str) -> date:
    """Parse une date depuis différents formats (YYYY-MM-DD, DD/MM/YYYY, DD/MM/YY, DD.MM.YY).

    Les années à 2 chiffres sont interprétées selon la convention POSIX:
    - 00-68 → 2000-2068
    - 69-99 → 1969-1999
    """
    value = value.strip()

    # Essayer YYYY-MM-DD ou YY-MM-DD
    parts = value.split("-")
    if len(parts) == 3:
        y, m, d = parts
    else:
        # Essayer DD/MM/YYYY, DD/MM/YY, DD.MM.YYYY, ou DD.MM.YY
        parts = value.replace(".", "/").split("/")
        if len(parts) == 3:
            d, m, y = parts
        else:
            raise ValueError(f"Format de date invalide: {value!r}")

    year = int(y)
    # Gérer les années à 2 chiffres (convention POSIX)
    if year < 100:
        year += 2000 if year < 69 else 1900

    return date(year, int(m), int(d))


def parse_csv(content: bytes | str) -> list[dict[str, Any]]:
    """Parse un contenu CSV en liste de mouvements normalisés."""

    if isinstance(content, bytes):
        stream = io.StringIO(content.decode("utf-8"))
    else:
        stream = io.StringIO(content)

    reader = csv.DictReader(stream)
    rows: list[dict[str, Any]] = []
    for raw in reader:
        libelle = (raw.get("libelle") or raw.get("label") or "").strip()
        montant = raw.get("montant") or raw.get("amount") or "0"
        date_raw = raw.get("date") or raw.get("date_operation") or raw.get("operation_date")
        if not date_raw:
            continue
        parsed = {
            "date_operation": _parse_date(date_raw),
            "libelle_banque": libelle,
            "montant": _parse_amount(str(montant)),
            "ref_banque": (raw.get("ref") or raw.get("reference") or "").strip() or None,
        }
        rows.append(parsed)
    return rows


def _checksum(account_id: int, entry: dict[str, Any]) -> str:
    base = f"{account_id}|{entry['date_operation']}|{entry['montant']}|{entry['libelle_banque']}"
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def import_csv(content: bytes | str, account_id: int, *, source: str = "CSV") -> dict[str, int]:
    """Insère un CSV dans finance_bank_statements/lines avec dédoublonnage."""

    entries = parse_csv(content)
    if not entries:
        return {"inserted": 0, "duplicates": 0, "total": 0}

    # Récupère entity_id pour validation éventuelle.
    df_acc = query_df(
        text("SELECT id, entity_id FROM finance_accounts WHERE id = :id"),
        params={"id": int(account_id)},
    )
    if df_acc.empty:
        raise ValueError("Compte introuvable.")

    period_start = min(e["date_operation"] for e in entries)
    period_end = max(e["date_operation"] for e in entries)

    engine = get_engine()
    content_hash = hashlib.sha1(str(len(content)).encode("utf-8") if not isinstance(content, bytes) else content).hexdigest()
    inserted = 0
    duplicates = 0

    with engine.begin() as conn:
        stmt_row = conn.execute(
            text(
                """
                INSERT INTO finance_bank_statements (account_id, period_start, period_end, source, file_name, hash)
                VALUES (:account_id, :period_start, :period_end, :source, :file_name, :hash)
                ON CONFLICT (account_id, hash) DO NOTHING
                RETURNING id
                """
            ),
            {
                "account_id": account_id,
                "period_start": period_start,
                "period_end": period_end,
                "source": source,
                "file_name": source,
                "hash": content_hash,
            },
        ).fetchone()
        if stmt_row:
            statement_id = int(stmt_row[0])
        else:
            # Rechercher un statement existant sur la même période.
            existing = conn.execute(
                text(
                    """
                    SELECT id FROM finance_bank_statements
                    WHERE account_id = :account_id
                      AND period_start = :period_start
                      AND period_end = :period_end
                    LIMIT 1
                    """
                ),
                {"account_id": account_id, "period_start": period_start, "period_end": period_end},
            ).fetchone()
            statement_id = int(existing.id) if existing else None
            if statement_id is None:
                # fallback: crée sans hash
                statement_id = conn.execute(
                    text(
                        """
                        INSERT INTO finance_bank_statements (account_id, period_start, period_end, source)
                        VALUES (:account_id, :period_start, :period_end, :source)
                        RETURNING id
                        """
                    ),
                    {"account_id": account_id, "period_start": period_start, "period_end": period_end, "source": source},
                ).scalar_one()

        for entry in entries:
            checksum = _checksum(account_id, entry)
            # Vérifier les doublons cross-statement (même compte, n'importe quel relevé)
            dup = conn.execute(
                text(
                    """
                    SELECT 1 FROM finance_bank_statement_lines l
                    JOIN finance_bank_statements s ON s.id = l.statement_id
                    WHERE s.account_id = :account_id
                      AND (l.checksum = :checksum OR (l.ref_banque IS NOT DISTINCT FROM :ref_banque AND l.ref_banque IS NOT NULL))
                    LIMIT 1
                    """
                ),
                {"account_id": account_id, "checksum": checksum, "ref_banque": entry.get("ref_banque")},
            ).fetchone()
            if dup:
                duplicates += 1
                continue
            conn.execute(
                text(
                    """
                    INSERT INTO finance_bank_statement_lines (
                        statement_id,
                        account_id,
                        date_operation,
                        date_valeur,
                        libelle_banque,
                        montant,
                        ref_banque,
                        checksum
                    ) VALUES (
                        :statement_id,
                        :account_id,
                        :date_operation,
                        :date_operation,
                        :libelle_banque,
                        :montant,
                        :ref_banque,
                        :checksum
                    )
                    """
                ),
                {
                    "statement_id": statement_id,
                    "account_id": account_id,
                    "date_operation": entry["date_operation"],
                    "libelle_banque": entry["libelle_banque"],
                    "montant": entry["montant"],
                    "ref_banque": entry.get("ref_banque"),
                    "checksum": checksum,
                },
            )
            inserted += 1

    return {"inserted": inserted, "duplicates": duplicates, "total": len(entries)}
