-- Migration: Ajouter invoice_id pour le rapprochement factures
-- Date: 2025-12-17

-- Ajouter colonne invoice_id à finance_reconciliations
ALTER TABLE finance_reconciliations
ADD COLUMN IF NOT EXISTS invoice_id BIGINT REFERENCES processed_invoices(id) ON DELETE SET NULL;

-- Index pour les recherches de rapprochement
CREATE INDEX IF NOT EXISTS ix_finance_reconciliations_invoice
ON finance_reconciliations(invoice_id)
WHERE invoice_id IS NOT NULL;

-- Commentaire
COMMENT ON COLUMN finance_reconciliations.invoice_id IS 'Lien vers la facture fournisseur rapprochée';
