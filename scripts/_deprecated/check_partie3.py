"""Affiche les plats insérés par PARTIE_3_MENU.txt pour validation rapide."""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data_repository import query_df

def main() -> None:
    database_url = os.getenv("DATABASE_URL")
    if database_url and "@db:" in database_url:
        # Lorsqu'on est hors container, la base locale est exposée sur localhost:5432.
        # À l'inverse, dans Docker (présence de /.dockerenv) on laisse le host `db`.
        if not Path("/.dockerenv").exists():
            os.environ["DATABASE_URL"] = database_url.replace("@db:", "@localhost:")

    sql = """
    WITH cat_names AS (
        SELECT pc.plat_id,
               STRING_AGG(c.nom, ', ' ORDER BY c.nom) AS categories
        FROM plat_categories pc
        JOIN categories c ON c.id = pc.categorie_id
        GROUP BY pc.plat_id
    )
    SELECT p.nom, p.type, COALESCE(cn.categories, '') AS categorie, p.prix_vente_ttc,
           p.tva_pct, p.actif, i.ingredient_id, i.quantite_batch, ing.nom AS ingredient
    FROM plats p
    LEFT JOIN cat_names cn ON cn.plat_id = p.id
    LEFT JOIN plat_ingredients i ON i.plat_id = p.id
    LEFT JOIN ingredients ing ON ing.id = i.ingredient_id
    WHERE p.restaurant_id = (
        SELECT id FROM restaurants WHERE code = 'restaurant' LIMIT 1
    )
    ORDER BY p.nom, i.id;
    """
    df = query_df(sql)
    if df.empty:
        print("Aucun plat trouvé pour le tenant 'restaurant'.")
        return

    print(df[["nom", "type", "categorie", "prix_vente_ttc", "ingredient", "quantite_batch"]].to_string(index=False))

if __name__ == "__main__":
    main()
