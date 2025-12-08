-- Ajoute la catégorie "Carburant" pour chaque entité finance (si absente).
WITH entities AS (
  SELECT DISTINCT entity_id FROM finance_accounts WHERE entity_id IS NOT NULL
)
INSERT INTO finance_categories (entity_id, name, type, parent_id, code)
SELECT e.entity_id, 'Carburant', 'DEPENSE', NULL, 'carburant'
FROM entities e
ON CONFLICT (entity_id, code) DO NOTHING;

-- Vérification rapide :
-- SELECT entity_id, code, name FROM finance_categories WHERE code = 'carburant';
