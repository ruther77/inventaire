-- Tables SQL formelles pour la phase expérimentale : historique prix + snapshot capital.

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    code TEXT NOT NULL,
    fournisseur TEXT,
    prix_achat NUMERIC(12,4) NOT NULL,
    quantite NUMERIC(12,3),
    facture_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_context TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_price_history_tenant_code ON price_history (tenant_id, code);
CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history (tenant_id, facture_date DESC);

CREATE TABLE IF NOT EXISTS capital_snapshot (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    stock_value NUMERIC(14,2) NOT NULL DEFAULT 0,
    bank_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    cash_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_assets NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_capital_snapshot_tenant_date ON capital_snapshot (tenant_id, snapshot_date);

COMMENT ON TABLE price_history IS 'Historique prix d'achat distinct par tenant/code, utilisé pour recalculer les prix de vente.';
COMMENT ON TABLE capital_snapshot IS 'Snapshot journalier consolidant stock + trésorerie par tenant (épicerie ou restaurant).';
