from __future__ import annotations

from pathlib import Path

import pandas as pd


READY_PATH = Path("docs/articles_prix_ttc_ready_for_db.csv")
OUTPUT_SQL = Path("docs/articles_insert.sql")


def escape(val: str) -> str:
    return val.replace("'", "''")


def main():
    df = pd.read_csv(READY_PATH)
    values_sql = []
    for _, row in df.iterrows():
        nom = escape(row["nom_clean"])
        categorie = escape(row["categorie"])
        prix_vente = float(row["prix_vente"])
        tva = float(row["tva"])
        values_sql.append(
            f"('{nom}', 1, '{categorie}', {prix_vente:.2f}, {tva:.2f}, TRUE)"
        )

    bulk_values = ",\n".join(values_sql)
    sql = f"""-- Généré automatiquement depuis {READY_PATH.name}
BEGIN;
INSERT INTO produits (nom, tenant_id, categorie, prix_vente, tva, actif)
VALUES
{bulk_values}
ON CONFLICT (lower(nom)) DO UPDATE
  SET categorie = EXCLUDED.categorie,
      prix_vente = EXCLUDED.prix_vente,
      tva = EXCLUDED.tva,
      actif = TRUE,
      updated_at = now();
COMMIT;
"""
    OUTPUT_SQL.write_text(sql)
    print("SQL généré ->", OUTPUT_SQL, f"({len(df)} lignes)")


if __name__ == "__main__":
    main()
