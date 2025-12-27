-- Migration: Déprécier restaurant_bank_statements
-- Date: 2025-12-17
-- Objectif: Unifier sur finance_bank_statement_lines comme source unique

-- 1. Créer une table de mapping pour préserver les liens depense_id
-- Ces liens connectent les transactions bancaires aux dépenses restaurant
CREATE TABLE IF NOT EXISTS finance_transaction_expense_links (
    id SERIAL PRIMARY KEY,
    transaction_id BIGINT REFERENCES finance_transactions(id) ON DELETE CASCADE,
    depense_id INTEGER REFERENCES restaurant_depenses(id) ON DELETE SET NULL,
    migrated_from TEXT DEFAULT 'restaurant_bank_statements',
    original_rbs_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_finance_tx_expense_transaction
ON finance_transaction_expense_links(transaction_id);

CREATE INDEX IF NOT EXISTS ix_finance_tx_expense_depense
ON finance_transaction_expense_links(depense_id);

-- 2. Migrer les liens depense_id vers la nouvelle table
-- Matching basé sur statement_line → transaction via finance_reconciliations
INSERT INTO finance_transaction_expense_links (transaction_id, depense_id, original_rbs_id)
SELECT DISTINCT ON (fr.transaction_id)
    fr.transaction_id,
    rbs.depense_id,
    rbs.id as original_rbs_id
FROM restaurant_bank_statements rbs
JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
JOIN finance_reconciliations fr ON fr.statement_line_id = fbsl.id
WHERE rbs.depense_id IS NOT NULL
AND NOT EXISTS (
    SELECT 1 FROM finance_transaction_expense_links
    WHERE transaction_id = fr.transaction_id
)
ORDER BY fr.transaction_id, rbs.id;

-- 3. Renommer la table comme dépréciée
ALTER TABLE restaurant_bank_statements
RENAME TO _deprecated_restaurant_bank_statements;

-- 4. Ajouter un commentaire explicatif
COMMENT ON TABLE _deprecated_restaurant_bank_statements IS
'Table dépréciée le 2025-12-17. Les données sont maintenant dans finance_bank_statement_lines et finance_transactions. Les liens depense_id ont été migrés vers finance_transaction_expense_links.';

-- 5. Créer une vue pour la compatibilité arrière (lecture seule)
CREATE OR REPLACE VIEW restaurant_bank_statements AS
SELECT
    fbsl.id,
    NULL::integer as tenant_id,
    fa.label as account,
    fbsl.date_operation as date,
    fbsl.libelle_banque as libelle,
    fbsl.category as categorie,
    fbsl.montant,
    CASE
        WHEN fbsl.montant > 0 THEN 'credit'
        ELSE 'debit'
    END as type,
    TO_CHAR(fbsl.date_operation, 'YYYY-MM') as mois,
    'finance_bank_statement_lines' as source,
    tel.depense_id,
    fr.created_at,
    fr.created_at as updated_at
FROM finance_bank_statement_lines fbsl
JOIN finance_accounts fa ON fa.id = fbsl.account_id
LEFT JOIN finance_reconciliations fr ON fr.statement_line_id = fbsl.id
LEFT JOIN finance_transaction_expense_links tel ON tel.transaction_id = fr.transaction_id;
