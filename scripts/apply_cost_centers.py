"""
Assigne les centres de coûts aux dépenses en fonction des catégories (tenant spécifique).

Usage:
  PYTHONPATH=. python3 scripts/apply_cost_centers.py --tenant 1

Le script :
  - s'assure de l'existence des centres de coûts standards pour le tenant
  - met à jour cost_center_id des restaurant_depenses sans centre, en fonction de categorie_id
"""

from __future__ import annotations

import argparse
from typing import Dict, List

from core.data_repository import exec_sql, query_df


# Mapping centre de coût -> catégories (libellé)
CC_CATEGORY_MAP: Dict[str, List[str]] = {
    "Approvisionnement/Achats": ["Approvisionnement", "Fournisseur", "Boissons"],
    "Encaissement/Commissions": ["Frais d'encaissement", "Plateformes / Commissions"],
    "Banque": ["Frais bancaires"],
    "Assurance": ["Assurance"],
    "Énergie": ["Énergie", "Gaz", "Eau"],
    "Abonnements/IT": ["Abonnements", "Abonnements TV", "Télécom", "SaaS / Informatique"],
    "Paie/Charges sociales": ["Salaires", "Charges sociales", "Retraite / Prévoyance"],
    "Fiscalité/URSSAF": ["Fiscalité", "Impôts et taxes"],
    "Loyer": ["Loyer/Location"],
}


def ensure_cost_centers(tenant_id: int) -> None:
    rows = [{"tenant": tenant_id, "nom": name} for name in CC_CATEGORY_MAP.keys()]
    exec_sql(
        """
        INSERT INTO restaurant_cost_centers (tenant_id, nom)
        VALUES (:tenant, :nom)
        ON CONFLICT (tenant_id, nom) DO NOTHING
        """,
        rows,
    )


def fetch_category_ids(tenant_id: int) -> dict[str, int]:
    df = query_df(
        """
        SELECT id, nom FROM restaurant_depense_categories
        WHERE tenant_id = :tenant
        """,
        {"tenant": tenant_id},
    )
    return {row.nom: int(row.id) for _, row in df.iterrows()} if not df.empty else {}


def fetch_cost_center_ids(tenant_id: int) -> dict[str, int]:
    df = query_df(
        """
        SELECT id, nom FROM restaurant_cost_centers
        WHERE tenant_id = :tenant
        """,
        {"tenant": tenant_id},
    )
    return {row.nom: int(row.id) for _, row in df.iterrows()} if not df.empty else {}


def apply_cost_centers(tenant_id: int) -> None:
    ensure_cost_centers(tenant_id)
    cat_ids = fetch_category_ids(tenant_id)
    cc_ids = fetch_cost_center_ids(tenant_id)

    updates = 0
    for cc_name, cat_names in CC_CATEGORY_MAP.items():
        cc_id = cc_ids.get(cc_name)
        if not cc_id:
            continue
        ids = [cat_ids[name] for name in cat_names if name in cat_ids]
        if not ids:
            continue
        exec_sql(
            """
            UPDATE restaurant_depenses
            SET cost_center_id = :cc_id
            WHERE tenant_id = :tenant
              AND cost_center_id IS NULL
              AND categorie_id = ANY(:cat_ids)
            """,
            {"cc_id": cc_id, "tenant": tenant_id, "cat_ids": ids},
        )
        updates += 1
    print(f"Cost centers applied for {updates} mappings.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Assigne les centres de coûts aux dépenses sans centre pour un tenant.")
    parser.add_argument("--tenant", type=int, required=True, help="ID du tenant (ex: 1 pour Epicerie HQ).")
    args = parser.parse_args()
    apply_cost_centers(args.tenant)


if __name__ == "__main__":
    main()
