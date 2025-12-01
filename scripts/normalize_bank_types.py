"""
Normalise le champ `type` des lignes bancaires (Entrée / Sortie) pour un tenant.

Usage :
  PYTHONPATH=. python3 scripts/normalize_bank_types.py --tenant 1 [--account <code>]

Heuristiques :
  - Marque en "Entrée" les libellés/patterns d'encaissement (remise CB, versement ALS,
    paiement entrant/payout, virement reçu, encaissement SumUp, "Entrant").
  - Marque en "Sortie" les libellés/patterns de débit (PRLV, CB/Paiement, cotisation, frais, retrait, virement sortant).

Ne touche qu'aux lignes dont le type n'est pas déjà cohérent avec le pattern détecté.
"""

from __future__ import annotations

import argparse

from core.data_repository import exec_sql


IN_PATTERNS = [
    "%REMISE CB%",
    "%VERSEMENT ALS%",
    "%VERSEMENT%",
    "%VIR RECU%",
    "%VIREMENT RECU%",
    "%PAYOUT%",
    "%ENTRANT%",
    "%PAIEMENT ENTRANT%",
    "%SUMUP PID%",
    "%SUMUP PAYOUT%",
    "%ENCAISSEMENT%",
]

OUT_PATTERNS = [
    "PRLV%",
    "PRÉLÈVEMENT%",
    "PRELEVEMENT%",
    "%CB%",
    "PAIEMENT%",
    "%COTISATION%",
    "%FRAIS%",
    "%RETRAIT%",
    "%VIREMENT SORTANT%",
    "%ENVOYE PAR%",
]


def normalize_types(tenant_id: int, account: str | None = None) -> None:
    account_clause = "AND account = :account" if account else ""
    params = {"tenant": tenant_id}
    if account:
        params["account"] = account

    # Entrées
    exec_sql(
        f"""
        UPDATE restaurant_bank_statements
        SET type = 'Entrée'
        WHERE tenant_id = :tenant
          {account_clause}
          AND (
            libelle ILIKE ANY(:in_patterns)
            OR (categorie ILIKE 'Encaissement%%')
          )
          AND (type IS NULL OR type NOT ILIKE 'Entr%')
        """,
        {**params, "in_patterns": IN_PATTERNS},
    )

    # Sorties
    exec_sql(
        f"""
        UPDATE restaurant_bank_statements
        SET type = 'Sortie'
        WHERE tenant_id = :tenant
          {account_clause}
          AND (
            libelle ILIKE ANY(:out_patterns)
            OR (categorie ILIKE 'Frais%%')
          )
          AND (type IS NULL OR type NOT ILIKE 'Sort%')
        """,
        {**params, "out_patterns": OUT_PATTERNS},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalise le type (Entrée/Sortie) des relevés bancaires.")
    parser.add_argument("--tenant", type=int, required=True, help="ID du tenant (ex: 1 pour Epicerie HQ).")
    parser.add_argument("--account", type=str, help="Filtre éventuel sur un compte bancaire.")
    args = parser.parse_args()
    normalize_types(args.tenant, account=args.account)
    print("Types normalisés (Entrée/Sortie) avec heuristiques libellé/catégorie.")


if __name__ == "__main__":
    main()
