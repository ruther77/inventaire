-- Migration: Ajout de la fonctionnalité "Historique import par session"
-- Date: 2025-12-15
-- Description: Ajoute la table zero_click_jobs et le champ session_id pour grouper les imports

-- 1. Créer la table zero_click_jobs si elle n'existe pas
CREATE TABLE IF NOT EXISTS zero_click_jobs (
    id SERIAL PRIMARY KEY,
    job_id TEXT NOT NULL UNIQUE,
    tenant_id INT NOT NULL REFERENCES tenants(id),
    session_id TEXT,  -- Session browser pour grouper les imports
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    filename TEXT,
    supplier_hint TEXT,
    margin_percent NUMERIC(5,2) DEFAULT 40.0,
    auto_confirm BOOLEAN DEFAULT true,
    result JSONB,  -- Résultat de l'import (InvoiceImportSummary)
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

-- Index pour optimiser les requêtes
CREATE INDEX IF NOT EXISTS idx_zero_click_jobs_tenant ON zero_click_jobs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_zero_click_jobs_session ON zero_click_jobs (session_id);
CREATE INDEX IF NOT EXISTS idx_zero_click_jobs_status ON zero_click_jobs (status);
CREATE INDEX IF NOT EXISTS idx_zero_click_jobs_created ON zero_click_jobs (created_at DESC);

-- 2. Ajouter le champ session_id à processed_invoices
ALTER TABLE processed_invoices
ADD COLUMN IF NOT EXISTS session_id TEXT;

-- Index pour session_id sur processed_invoices
CREATE INDEX IF NOT EXISTS idx_processed_invoices_session ON processed_invoices (session_id);

-- 3. Commentaires pour documentation
COMMENT ON TABLE zero_click_jobs IS 'Jobs d''import zero-click avec traçabilité par session';
COMMENT ON COLUMN zero_click_jobs.session_id IS 'Identifiant de session browser pour grouper les imports';
COMMENT ON COLUMN zero_click_jobs.result IS 'Résultat JSON de l''import (mouvements, quantités, erreurs)';
COMMENT ON COLUMN processed_invoices.session_id IS 'Identifiant de session browser pour grouper les imports';
