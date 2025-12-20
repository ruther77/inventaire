-- Met à jour les catégories/fournisseurs des ingrédients restaurant
-- à partir du catalogage épicerie et des derniers mouvements.
-- Usage :
--   psql "$DATABASE_URL" \
--     -v restaurant_tenant_id=2 \
--     -f scripts/restaurant/sync_categories_from_epicerie.sql

\set restaurant_tenant_id 2

-- 1) Catégorie depuis produits (si produit_epicerie_id est renseigné)
UPDATE restaurant_ingredients ri
SET categorie = p.categorie
FROM produits p
WHERE ri.tenant_id = :restaurant_tenant_id
  AND ri.produit_epicerie_id = p.id
  AND p.categorie IS NOT NULL
  AND (ri.categorie IS NULL OR ri.categorie <> p.categorie);

-- 2) Fournisseur depuis dernier mouvements_stock.source du produit épicerie
WITH last_src AS (
    SELECT
        m.produit_id,
        m.source,
        ROW_NUMBER() OVER (PARTITION BY m.produit_id ORDER BY m.date_mvt DESC) AS rn
    FROM mouvements_stock m
    WHERE m.source IS NOT NULL
)
UPDATE restaurant_ingredients ri
SET fournisseur = ls.source
FROM last_src ls
WHERE ri.tenant_id = :restaurant_tenant_id
  AND ri.produit_epicerie_id = ls.produit_id
  AND ls.rn = 1
  AND (ri.fournisseur IS NULL OR ri.fournisseur <> ls.source);

-- 3) Fallback fournisseur depuis produits.categorie (si toujours NULL)
UPDATE restaurant_ingredients ri
SET fournisseur = p.categorie
FROM produits p
WHERE ri.tenant_id = :restaurant_tenant_id
  AND ri.produit_epicerie_id = p.id
  AND ri.fournisseur IS NULL
  AND p.categorie IS NOT NULL;
