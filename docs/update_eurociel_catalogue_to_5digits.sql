-- Remplacement des barcodes ECZxxxx du catalogue Eurociel par des placeholders numériques 5 chiffres alignés par catégorie.
-- - Conserve les séquences existantes par catégorie (max actuel des codes 5 chiffres).
-- - Alloue de nouveaux préfixes (à partir du dernier préfixe existant) pour les catégories sans codes 5 chiffres.

WITH cat_max AS (
  SELECT
    p.categorie,
    LEFT(MAX(pb.code), 2) AS prefix,
    COALESCE(MAX(CASE WHEN pb.code ~ '^[0-9]{5}$' THEN CAST(SUBSTR(pb.code, 3, 3) AS INT) END), 0) AS max_num
  FROM produits_barcodes pb
  JOIN produits p ON p.id = pb.produit_id
  WHERE pb.code ~ '^[0-9]{5}$'
  GROUP BY p.categorie
),
max_prefix AS (
  SELECT COALESCE(MAX(prefix::INT), 0) AS max_pref FROM cat_max
),
missing_cats AS (
  SELECT DISTINCT p.categorie
  FROM produits_barcodes pb
  JOIN produits p ON p.id = pb.produit_id
  WHERE pb.code LIKE 'ECZ%'  -- catalogue Eurociel
    AND p.categorie NOT IN (SELECT categorie FROM cat_max)
),
missing_alloc AS (
  SELECT
    m.categorie,
    LPAD((mp.max_pref + ROW_NUMBER() OVER (ORDER BY m.categorie))::TEXT, 2, '0') AS prefix,
    0 AS max_num
  FROM missing_cats m CROSS JOIN max_prefix mp
),
cat_all AS (
  SELECT categorie, prefix, max_num FROM cat_max
  UNION ALL
  SELECT categorie, prefix, max_num FROM missing_alloc
),
to_update AS (
  SELECT
    pb.id AS barcode_id,
    pb.code AS old_code,
    p.id AS produit_id,
    ca.prefix,
    ca.max_num + ROW_NUMBER() OVER (PARTITION BY p.categorie ORDER BY p.id) AS seq
  FROM produits_barcodes pb
  JOIN produits p ON p.id = pb.produit_id
  JOIN cat_all ca ON ca.categorie = p.categorie
  WHERE pb.code LIKE 'ECZ%'  -- uniquement les barcodes catalogue Eurociel
),
updates AS (
  UPDATE produits_barcodes pb
  SET code = tu.prefix || LPAD(tu.seq::TEXT, 3, '0')
  FROM to_update tu
  WHERE pb.id = tu.barcode_id
  RETURNING tu.old_code, pb.code AS new_code
)
UPDATE produits_price_history ph
SET code = u.new_code
FROM updates u
WHERE ph.code = u.old_code;
