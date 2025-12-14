-- Data Quality Fix / Flagging
-- Usage: docker compose --env-file .env exec -T db psql -U postgres -d epicerie < scripts/data_quality_fix.sql
\pset footer off
\pset format unaligned
\pset tuples_only on

-- Table de suivi des anomalies (non intrusive)
CREATE TABLE IF NOT EXISTS data_quality_flags (
  id bigserial PRIMARY KEY,
  table_name text NOT NULL,
  row_id text NOT NULL,
  issue text NOT NULL,
  details jsonb DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- On conserve l'historique mais on peut nettoyer les flags du jour
DELETE FROM data_quality_flags WHERE created_at::date = current_date;

-- 1) Labels manquants sur transactions : remplir à minima
ALTER TABLE finance_transactions DISABLE TRIGGER ALL;
UPDATE finance_transactions
SET label = COALESCE(label, ref_externe, 'Transaction ' || id)
WHERE label IS NULL OR btrim(label) = '';
ALTER TABLE finance_transactions ENABLE TRIGGER ALL;

-- 2) Libellés banque manquants : fallback lisible
ALTER TABLE finance_bank_statement_lines DISABLE TRIGGER ALL;
UPDATE finance_bank_statement_lines
SET libelle_banque = COALESCE(NULLIF(libelle_banque, ''), ref_banque, 'LIBELLE MANQUANT #' || id)
WHERE libelle_banque IS NULL OR btrim(libelle_banque) = '';
ALTER TABLE finance_bank_statement_lines ENABLE TRIGGER ALL;

-- 3) Flags prix manquants
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'produits', p.id::text, 'NULL_PRIX_ACHAT', jsonb_build_object('nom', p.nom)
FROM produits p
WHERE p.prix_achat IS NULL;

INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'produits', p.id::text, 'NULL_PRIX_VENTE', jsonb_build_object('nom', p.nom)
FROM produits p
WHERE p.prix_vente IS NULL;

-- 4) Flags stock élevé
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'produits', p.id::text, 'HIGH_STOCK', jsonb_build_object('stock_actuel', p.stock_actuel)
FROM produits p
WHERE p.stock_actuel >= 10000;

-- 5) Flags montants négatifs inattendus sur lignes de relevés
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'finance_bank_statement_lines', b.id::text, 'NEGATIVE_AMOUNT', jsonb_build_object('montant', b.montant, 'date_operation', b.date_operation)
FROM finance_bank_statement_lines b
WHERE b.montant < 0;

-- 6) Doublons potentiels finance_transactions (date+montant)
WITH dup AS (
  SELECT date_operation, amount, array_agg(id ORDER BY id) AS ids, count(*) AS cnt
  FROM finance_transactions
  GROUP BY date_operation, amount
  HAVING count(*) > 1
)
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'finance_transactions', unnest(ids)::text, 'DUPLICATE_SIGNATURE', jsonb_build_object('date_operation', date_operation, 'amount', amount, 'group_size', cnt)
FROM dup;

-- 7) Doublons potentiels lignes de relevés (date+montant)
WITH dup AS (
  SELECT date_operation, montant, array_agg(id ORDER BY id) AS ids, count(*) AS cnt
  FROM finance_bank_statement_lines
  GROUP BY date_operation, montant
  HAVING count(*) > 1
)
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'finance_bank_statement_lines', unnest(ids)::text, 'DUPLICATE_SIGNATURE', jsonb_build_object('date_operation', date_operation, 'montant', montant, 'group_size', cnt)
FROM dup;

-- 8) Marques de TVA à zéro : flag pour correction manuelle
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'produits', p.id::text, 'TVA_ZERO', jsonb_build_object('nom', p.nom)
FROM produits p
WHERE p.tva = 0;

\echo 'Data quality flags rafraichis.'
