"""Création d'une table de mapping Epicerie -> Restaurant + fonction de transfert de stock.

Usage :
  DATABASE_URL=postgresql://... python scripts/setup_restaurant_transfer.py

- Table restaurant_epicerie_sku_map : relie un SKU épicerie (tenant 1) à un SKU restaurant (tenant 2) avec ratio.
- Fonction transfer_from_epicerie(restaurant_produit_id, quantite) :
    * lit le mapping
    * crée un mouvement SORTIE (tenant épicerie)
    * crée un mouvement ENTREE (tenant restaurant)
    * retourne les ids de mouvements.
"""
from __future__ import annotations
import os
from decimal import Decimal
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/epicerie")
TENANT_EPICERIE = int(os.environ.get("TENANT_EPICERIE", 1))
TENANT_RESTAURANT = int(os.environ.get("TENANT_RESTAURANT", 2))

en = create_engine(DB_URL)

def main():
    with en.begin() as conn:
        conn.execute(text(
            """
            CREATE TABLE IF NOT EXISTS restaurant_epicerie_sku_map (
                id SERIAL PRIMARY KEY,
                tenant_restaurant INT NOT NULL DEFAULT 2,
                tenant_epicerie INT NOT NULL DEFAULT 1,
                produit_restaurant_id INT NOT NULL,
                produit_epicerie_id INT NOT NULL,
                ratio NUMERIC(12,4) NOT NULL DEFAULT 1.0,
                UNIQUE (tenant_restaurant, produit_restaurant_id)
            );
            """
        ))
        # Fonction plpgsql pour transférer
        conn.execute(text(
            f"""
            CREATE OR REPLACE FUNCTION transfer_from_epicerie(p_restaurant_id INT, p_quantite NUMERIC)
            RETURNS TABLE(epicerie_mvt_id INT, restaurant_mvt_id INT) AS $$
            DECLARE
                m RECORD;
            BEGIN
                SELECT * INTO m FROM restaurant_epicerie_sku_map
                 WHERE tenant_restaurant = {TENANT_RESTAURANT}
                   AND produit_restaurant_id = p_restaurant_id
                 LIMIT 1;
                IF NOT FOUND THEN
                    RAISE EXCEPTION 'Mapping non trouvé pour produit %', p_restaurant_id;
                END IF;
                -- Sortie épicerie
                INSERT INTO mouvements_stock (produit_id, tenant_id, type, quantite, source)
                VALUES (m.produit_epicerie_id, m.tenant_epicerie, 'SORTIE', p_quantite * m.ratio, 'transfer_to_restaurant')
                RETURNING id INTO epicerie_mvt_id;
                -- Entrée restaurant
                INSERT INTO mouvements_stock (produit_id, tenant_id, type, quantite, source)
                VALUES (p_restaurant_id, m.tenant_restaurant, 'ENTREE', p_quantite, 'from_epicerie')
                RETURNING id INTO restaurant_mvt_id;
                RETURN NEXT;
            END;
            $$ LANGUAGE plpgsql;
            """
        ))
    print("Table mapping + fonction transfer_from_epicerie créées sur", DB_URL)

if __name__ == "__main__":
    main()
