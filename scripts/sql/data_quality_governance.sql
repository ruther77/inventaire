-- Job de remise en cohérence complémentaire
-- Usage : docker compose --env-file .env exec -T db psql -U postgres -d epicerie < scripts/sql/data_quality_governance.sql
\pset footer off
\pset format unaligned
\pset tuples_only on

-- Vue produits avec prix manquants / TVA à zéro
CREATE OR REPLACE VIEW v_produits_prix_manquants AS
SELECT id, nom, prix_achat, prix_vente, tva
FROM produits
WHERE prix_achat IS NULL OR prix_vente IS NULL OR tva = 0;

-- Flags stock élevé (>= 10000) via data_quality_flags
INSERT INTO data_quality_flags (table_name, row_id, issue, details)
SELECT 'produits', p.id::text, 'HIGH_STOCK', jsonb_build_object('stock_actuel', p.stock_actuel)
FROM produits p
WHERE p.stock_actuel >= 10000
ON CONFLICT DO NOTHING;

-- Transactions sans label : si statut non compatible, on flag plutôt que d'échouer
DO $$
DECLARE
  has_status boolean;
  enum_ok boolean;
BEGIN
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='finance_transactions' AND column_name='status') INTO has_status;
  IF has_status THEN
    SELECT EXISTS (
      SELECT 1 FROM pg_type t
      JOIN pg_enum e ON e.enumtypid = t.oid
      WHERE t.typname = 'finance_tx_status' AND e.enumlabel = 'CHECK'
    ) INTO enum_ok;
    IF enum_ok THEN
      UPDATE finance_transactions SET status = 'CHECK' WHERE label IS NULL OR btrim(label) = '';
    ELSE
      INSERT INTO data_quality_flags (table_name, row_id, issue, details)
      SELECT 'finance_transactions', id::text, 'MISSING_LABEL', jsonb_build_object('label', label)
      FROM finance_transactions
      WHERE label IS NULL OR btrim(label) = '';
    END IF;
  END IF;
END$$;

-- Relevés : forcer cohérence signe / direction (si colonne direction existe)
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='finance_bank_statement_lines' AND column_name='direction') THEN
    UPDATE finance_bank_statement_lines SET direction = CASE WHEN montant < 0 THEN 'DEBIT' ELSE 'CREDIT' END;
  END IF;
END$$;

-- Appliquer needs_review sur stock >= 10000 si la colonne existe
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='produits' AND column_name='needs_review') THEN
    UPDATE produits SET needs_review = TRUE WHERE stock_actuel >= 10000;
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='stock_courant' AND column_name='needs_review') THEN
    UPDATE stock_courant SET needs_review = TRUE WHERE stock >= 10000;
  END IF;
END$$;

\echo 'Gouvernance appliquée : vue v_produits_prix_manquants et flags HIGH_STOCK créés.'
