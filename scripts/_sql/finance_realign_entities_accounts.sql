-- Rebase des entités/comptes finance selon la nomenclature:
-- INCONTOURNABLE = RESTO, NOUTAM = EPICERIE.
-- Exécuter dans psql/pgcli; script idempotent.

BEGIN;

-- 0) Normaliser d'éventuels anciens codes entité pour éviter la duplication
UPDATE finance_entities SET code = 'RESTO', name = 'INCONTOURNABLE'
WHERE code = 'restaurant' AND NOT EXISTS (SELECT 1 FROM finance_entities WHERE code = 'RESTO');
UPDATE finance_entities SET code = 'EPICERIE', name = 'NOUTAM'
WHERE code = 'epicerie' AND NOT EXISTS (SELECT 1 FROM finance_entities WHERE code = 'EPICERIE');

-- 1) Référentiel d'entités
INSERT INTO finance_entities (code, name, currency, is_active)
VALUES
  ('RESTO', 'INCONTOURNABLE', 'EUR', TRUE),
  ('EPICERIE', 'NOUTAM', 'EUR', TRUE)
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name, currency = EXCLUDED.currency, is_active = TRUE;

-- 2) Charger les IDs dans des variables psql
SELECT id AS resto_id FROM finance_entities WHERE code = 'RESTO'\gset
SELECT id AS epi_id FROM finance_entities WHERE code = 'EPICERIE'\gset

-- 2bis) Aligner d'anciens libellés génériques sur la nomenclature relevés LCL/SumUp
UPDATE finance_accounts SET label = 'LCL - INCONTOURNABLE', entity_id = :resto_id, type = 'BANQUE', is_active = TRUE
WHERE label IN ('BNP', 'BNP - INCONTOURNABLE', 'LCL - INCONTOURNABLE', 'LCL');
UPDATE finance_accounts SET label = 'LCL - NOUTAM', entity_id = :epi_id, type = 'BANQUE', is_active = TRUE
WHERE label IN ('BNP - NOUTAM', 'LCL - NOUTAM');
UPDATE finance_accounts SET label = 'SUMUP - INCONTOURNABLE', entity_id = :resto_id, type = 'PLATFORM', is_active = TRUE
WHERE label IN ('SUMUP', 'SUMUP - INCONTOURNABLE');

-- LCL RESTO (création si absent)
INSERT INTO finance_accounts (entity_id, type, label, currency, is_active)
SELECT :resto_id, 'BANQUE', 'LCL - INCONTOURNABLE', 'EUR', TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM finance_accounts a WHERE a.label = 'LCL - INCONTOURNABLE' AND a.entity_id = :resto_id
);
UPDATE finance_accounts SET entity_id = :resto_id, type = 'BANQUE', currency = 'EUR', is_active = TRUE
WHERE label = 'LCL - INCONTOURNABLE';

-- LCL EPICERIE
INSERT INTO finance_accounts (entity_id, type, label, currency, is_active)
SELECT :epi_id, 'BANQUE', 'LCL - NOUTAM', 'EUR', TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM finance_accounts a WHERE a.label = 'LCL - NOUTAM' AND a.entity_id = :epi_id
);
UPDATE finance_accounts SET entity_id = :epi_id, type = 'BANQUE', currency = 'EUR', is_active = TRUE
WHERE label = 'LCL - NOUTAM';

-- SUMUP RESTO (compte unique)
INSERT INTO finance_accounts (entity_id, type, label, currency, is_active)
SELECT :resto_id, 'PLATFORM', 'SUMUP - INCONTOURNABLE', 'EUR', TRUE
WHERE NOT EXISTS (
  SELECT 1 FROM finance_accounts a WHERE a.label = 'SUMUP - INCONTOURNABLE' AND a.entity_id = :resto_id
);
UPDATE finance_accounts SET entity_id = :resto_id, type = 'PLATFORM', currency = 'EUR', is_active = TRUE
WHERE label = 'SUMUP - INCONTOURNABLE';

-- 3) Désactiver des doublons éventuels sur ces labels
WITH target_labels AS (
  SELECT unnest(ARRAY[
    'LCL - INCONTOURNABLE',
    'LCL - NOUTAM',
    'SUMUP - INCONTOURNABLE'
  ]) AS label
),
usage AS (
  SELECT account_id, COUNT(*) AS tx_count FROM finance_transactions GROUP BY account_id
),
ranked AS (
  SELECT a.id, a.label,
         ROW_NUMBER() OVER (
           PARTITION BY a.label
           ORDER BY COALESCE(u.tx_count, 0) DESC, a.is_active DESC, a.updated_at DESC NULLS LAST, a.id ASC
         ) AS rn
  FROM finance_accounts a
  JOIN target_labels t ON t.label = a.label
  LEFT JOIN usage u ON u.account_id = a.id
)
UPDATE finance_accounts a
SET is_active = CASE WHEN r.rn = 1 THEN TRUE ELSE FALSE END
FROM ranked r
WHERE a.id = r.id;

-- 4) Aligner les transactions avec l'entité du compte
UPDATE finance_transactions t
SET entity_id = a.entity_id
FROM finance_accounts a
WHERE t.account_id = a.id
  AND t.entity_id IS DISTINCT FROM a.entity_id;

-- 5) (Optionnel) Régularisation inter-entités pour achats épicerie payés via SumUp RESTO
-- Décommentez et adaptez le filtre "suspects" si vous avez un critère clair (catégorie EPICERIE, note, tag).
-- Par défaut on crée un transfert vers le compte LCL - NOUTAM; ajustez si vous préférez un autre compte épicerie.
-- SELECT id AS sumup_id FROM finance_accounts WHERE label = 'SUMUP - INCONTOURNABLE' AND entity_id = :resto_id LIMIT 1\gset
-- SELECT id AS epi_bank_id FROM finance_accounts WHERE label = 'LCL - NOUTAM' AND entity_id = :epi_id LIMIT 1\gset
-- WITH suspects AS (
--   SELECT t.id, t.date_operation, t.date_value, t.amount, t.currency
--   FROM finance_transactions t
--   WHERE t.account_id = :sumup_id
--     AND t.status = 'CONFIRMED'
--     AND t.direction = 'OUT'
--     AND t.entity_id = :resto_id
--     -- Exemple de critère : catégorie épicerie
--     -- AND t.id IN (SELECT transaction_id FROM finance_transaction_lines l JOIN finance_categories c ON c.id = l.category_id WHERE c.code LIKE 'EPI%')
-- )
-- INSERT INTO finance_transactions (entity_id, account_id, counterparty_account_id, direction, source, date_operation, date_value, amount, currency, ref_externe, note, status)
-- SELECT
--   :epi_id,
--   :epi_bank_id,
--   :sumup_id,
--   'TRANSFER',
--   'MANUEL',
--   s.date_operation,
--   s.date_value,
--   s.amount,
--   s.currency,
--   'SUMUP_EPICERIE_' || s.id,
--   'Régularisation achat épicerie payé avec SumUp RESTO',
--   'CONFIRMED'
-- FROM suspects s
-- ON CONFLICT (ref_externe) DO NOTHING;

COMMIT;
