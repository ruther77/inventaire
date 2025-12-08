-- Rebuild finance_transactions à partir des relevés bancaires existants (/releve déjà importés).
-- Étapes :
-- 1) Dédoublonner finance_bank_statements par (account_id, period_start, period_end) en gardant celui avec le plus de lignes.
-- 2) Créer/garantir des catégories par entité : BANK_IN (RECETTE) et BANK_OUT (DEPENSE).
-- 3) Purger paiements / transactions / lines / reconciliations existants.
-- 4) Générer une transaction par ligne de relevé (ref_externe = 'stmtline:{id}'), direction selon le signe.
-- 5) Créer une ligne analytique unique par transaction.

BEGIN;

-- 1) Dédoublonnage des relevés
CREATE TEMP TABLE tmp_stmt_dups ON COMMIT DROP AS
SELECT id AS dup_id, keeper_id FROM (
  SELECT
    s.id,
    s.account_id,
    s.period_start,
    s.period_end,
    COUNT(l.id) AS lines_count,
    ROW_NUMBER() OVER (
      PARTITION BY s.account_id, s.period_start, s.period_end
      ORDER BY COUNT(l.id) DESC, s.id ASC
    ) AS rn,
    FIRST_VALUE(s.id) OVER (
      PARTITION BY s.account_id, s.period_start, s.period_end
      ORDER BY COUNT(l.id) DESC, s.id ASC
    ) AS keeper_id
  FROM finance_bank_statements s
  LEFT JOIN finance_bank_statement_lines l ON l.statement_id = s.id
  WHERE s.period_start IS NOT NULL
  GROUP BY s.id
) ranked
WHERE rn > 1;

UPDATE finance_bank_statement_lines l
SET statement_id = d.keeper_id
FROM tmp_stmt_dups d
WHERE l.statement_id = d.dup_id;

DELETE FROM finance_bank_statements
WHERE id IN (SELECT dup_id FROM tmp_stmt_dups);

-- 2) Catégories bancaires génériques par entité
WITH entities AS (
  SELECT DISTINCT entity_id FROM finance_accounts WHERE entity_id IS NOT NULL
)
INSERT INTO finance_categories (entity_id, name, type, parent_id, code)
SELECT e.entity_id, 'Bank IN', 'RECETTE', NULL, 'BANK_IN' FROM entities e
ON CONFLICT (entity_id, code) DO NOTHING;

WITH entities AS (
  SELECT DISTINCT entity_id FROM finance_accounts WHERE entity_id IS NOT NULL
)
INSERT INTO finance_categories (entity_id, name, type, parent_id, code)
SELECT e.entity_id, 'Bank OUT', 'DEPENSE', NULL, 'BANK_OUT' FROM entities e
ON CONFLICT (entity_id, code) DO NOTHING;

-- 3) Purge des flux existants
DELETE FROM finance_reconciliations;
DELETE FROM finance_transaction_lines;
DELETE FROM finance_transactions;
DELETE FROM finance_payments;

-- 4) Génération des transactions depuis les lignes de relevé
WITH src AS (
  SELECT
    l.id AS line_id,
    s.account_id,
    a.entity_id,
    l.date_operation,
    COALESCE(l.date_valeur, l.date_operation) AS date_value,
    l.libelle_banque,
    l.montant,
    CASE WHEN l.montant >= 0 THEN 'IN' ELSE 'OUT' END AS direction,
    ABS(l.montant) AS amount_abs
  FROM finance_bank_statement_lines l
  JOIN finance_bank_statements s ON s.id = l.statement_id
  JOIN finance_accounts a ON a.id = s.account_id
  WHERE l.montant IS NOT NULL AND l.montant <> 0
),
ins AS (
  INSERT INTO finance_transactions (
    entity_id,
    account_id,
    counterparty_account_id,
    direction,
    source,
    date_operation,
    date_value,
    amount,
    currency,
    ref_externe,
    note,
    status
  )
  SELECT
    s.entity_id,
    s.account_id,
    NULL,
    s.direction::finance_tx_direction,
    'BANK',
    s.date_operation,
    s.date_value,
    s.amount_abs,
    'EUR',
    CONCAT('stmtline:', s.line_id),
    s.libelle_banque,
    'CONFIRMED'
  FROM src s
  ON CONFLICT (ref_externe) DO NOTHING
  RETURNING id, entity_id, account_id, direction, amount, ref_externe
)
INSERT INTO finance_transaction_lines (
  transaction_id,
  category_id,
  cost_center_id,
  montant_ht,
  tva_pct,
  montant_ttc,
  description,
  position
)
SELECT
  t.id,
  CASE
    WHEN t.direction = 'IN' THEN (SELECT id FROM finance_categories WHERE entity_id = t.entity_id AND code = 'BANK_IN' LIMIT 1)
    ELSE (SELECT id FROM finance_categories WHERE entity_id = t.entity_id AND code = 'BANK_OUT' LIMIT 1)
  END AS category_id,
  NULL,
  NULL,
  NULL,
  t.amount,
  t.ref_externe,
  1
FROM ins t;

COMMIT;
