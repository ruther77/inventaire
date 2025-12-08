"""Dédoublonne finance_bank_statements/lines par compte+période.

Logique : pour chaque (account_id, period_start, period_end), on conserve
le relevé qui a le plus de lignes (ou l'id le plus bas en cas d'égalité),
on réassigne les lines vers ce relevé, puis on supprime les doublons restants.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from sqlalchemy import text

from core.data_repository import get_engine


@dataclass
class StatementGroup:
    account_id: int
    period_start: str
    period_end: str
    ids: List[int]


def fetch_duplicates(conn) -> List[StatementGroup]:
    rows = conn.execute(
        text(
            """
            SELECT account_id, period_start, period_end, array_agg(id ORDER BY id) AS ids
            FROM finance_bank_statements
            GROUP BY account_id, period_start, period_end
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()
    groups: List[StatementGroup] = []
    for r in rows:
        groups.append(
            StatementGroup(
                account_id=int(r.account_id),
                period_start=str(r.period_start),
                period_end=str(r.period_end),
                ids=list(r.ids),
            )
        )
    return groups


def pick_keeper(conn, ids: List[int]) -> int:
    # Choisir l'id avec le plus de lignes, sinon le plus petit id.
    rows = conn.execute(
        text(
            """
            SELECT s.id, COUNT(l.id) AS lines_count
            FROM finance_bank_statements s
            LEFT JOIN finance_bank_statement_lines l ON l.statement_id = s.id
            WHERE s.id = ANY(:ids)
            GROUP BY s.id
            ORDER BY lines_count DESC, s.id ASC
            LIMIT 1
            """
        ),
        {"ids": ids},
    ).fetchall()
    return int(rows[0].id)


def main() -> None:
    eng = get_engine()
    with eng.begin() as conn:
        groups = fetch_duplicates(conn)
        if not groups:
            print("Aucun doublon trouvé.")
            return
        total_deleted = 0
        for grp in groups:
            keeper = pick_keeper(conn, grp.ids)
            to_delete = [i for i in grp.ids if i != keeper]
            if not to_delete:
                continue
            # Réassigner les lignes vers le relevé conservé
            conn.execute(
                text(
                    """
                    UPDATE finance_bank_statement_lines
                    SET statement_id = :keeper
                    WHERE statement_id = ANY(:to_delete)
                    """
                ),
                {"keeper": keeper, "to_delete": to_delete},
            )
            # Supprimer les relevés doublons
            conn.execute(
                text("DELETE FROM finance_bank_statements WHERE id = ANY(:to_delete)"),
                {"to_delete": to_delete},
            )
            total_deleted += len(to_delete)
            print(
                f"[{grp.account_id} {grp.period_start}→{grp.period_end}] "
                f"garde {keeper}, supprime {to_delete}"
            )
        print(f"Terminé. {total_deleted} relevé(s) supprimé(s).")


if __name__ == "__main__":
    main()
