-- ============================================================================
-- Migration 002: Analytics, Intelligence & Advanced Finance Tables
-- Date: 2025-12-09
-- Description: Tables pour comptabilite analytique, previsions, scoring,
--              rapprochement bancaire et marges
-- ============================================================================

-- ============================================================================
-- 1. COMPTABILITE ANALYTIQUE
-- ============================================================================

-- Axes analytiques (entites, categories, projets, centres de cout)
CREATE TABLE IF NOT EXISTS analytic_axes (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    axis_type VARCHAR(50) NOT NULL,  -- 'entity', 'category', 'project', 'cost_center'
    parent_id INTEGER REFERENCES analytic_axes(id),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, code)
);

CREATE INDEX IF NOT EXISTS idx_analytic_axes_tenant ON analytic_axes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_analytic_axes_type ON analytic_axes(tenant_id, axis_type);
CREATE INDEX IF NOT EXISTS idx_analytic_axes_parent ON analytic_axes(parent_id);

COMMENT ON TABLE analytic_axes IS 'Axes analytiques pour ventilation des couts et revenus';

-- Affectations analytiques (ventilation des transactions)
CREATE TABLE IF NOT EXISTS analytic_assignments (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    source_type VARCHAR(50) NOT NULL,  -- 'transaction', 'invoice_line', 'stock_movement'
    source_id INTEGER NOT NULL,
    axis_id INTEGER REFERENCES analytic_axes(id),
    amount DECIMAL(15,2) NOT NULL,
    percentage DECIMAL(5,2),  -- Pour ventilation multi-axes
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, source_type, source_id, axis_id)
);

CREATE INDEX IF NOT EXISTS idx_analytic_assignments_source ON analytic_assignments(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_analytic_assignments_axis ON analytic_assignments(axis_id);
CREATE INDEX IF NOT EXISTS idx_analytic_assignments_tenant ON analytic_assignments(tenant_id);

-- ============================================================================
-- 2. PREVISIONS (FORECASTING)
-- ============================================================================

-- Cache des previsions
CREATE TABLE IF NOT EXISTS forecast_cache (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    forecast_type VARCHAR(50) NOT NULL,  -- 'sales', 'cashflow', 'stock', 'price'
    target_entity VARCHAR(100),  -- 'product', 'category', 'global'
    target_id INTEGER,  -- product_id, category_id, etc.

    -- Resultats
    forecast_date DATE NOT NULL,
    predicted_value DECIMAL(15,2),
    confidence_lower DECIMAL(15,2),
    confidence_upper DECIMAL(15,2),
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    -- Methode utilisee
    model_type VARCHAR(50),  -- 'prophet', 'holt_winters', 'moving_average', 'regression'
    model_params JSONB DEFAULT '{}',

    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    UNIQUE(tenant_id, forecast_type, target_entity, COALESCE(target_id, 0), forecast_date)
);

CREATE INDEX IF NOT EXISTS idx_forecast_lookup ON forecast_cache(tenant_id, forecast_type, target_entity);
CREATE INDEX IF NOT EXISTS idx_forecast_date ON forecast_cache(forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_expiry ON forecast_cache(expires_at);

COMMENT ON TABLE forecast_cache IS 'Cache des previsions generees par les modeles ML';

-- ============================================================================
-- 3. SCORING FOURNISSEURS
-- ============================================================================

-- Scores fournisseurs actuels
CREATE TABLE IF NOT EXISTS supplier_scores (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    supplier_name VARCHAR(200) NOT NULL,  -- Nom du fournisseur (ou vendor_id si table existe)

    -- Composantes du score (0-1, haut = bon)
    price_stability_score DECIMAL(3,2),      -- Stabilite des prix
    delivery_reliability_score DECIMAL(3,2), -- Fiabilite livraison
    invoice_accuracy_score DECIMAL(3,2),     -- Precision factures
    quality_score DECIMAL(3,2),              -- Qualite produits
    payment_terms_score DECIMAL(3,2),        -- Conditions paiement

    -- Score global pondere
    overall_score DECIMAL(3,2),
    score_trend VARCHAR(20),  -- 'improving', 'stable', 'declining'

    -- Donnees de calcul
    calculation_date DATE,
    data_points INTEGER,
    calculation_params JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, supplier_name, calculation_date)
);

CREATE INDEX IF NOT EXISTS idx_supplier_scores_tenant ON supplier_scores(tenant_id);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_supplier ON supplier_scores(tenant_id, supplier_name);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_date ON supplier_scores(calculation_date DESC);

-- Historique des scores
CREATE TABLE IF NOT EXISTS supplier_score_history (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    supplier_name VARCHAR(200) NOT NULL,
    score_date DATE NOT NULL,
    overall_score DECIMAL(3,2),
    components JSONB,  -- Toutes les composantes du score

    UNIQUE(tenant_id, supplier_name, score_date)
);

CREATE INDEX IF NOT EXISTS idx_supplier_history_lookup ON supplier_score_history(tenant_id, supplier_name, score_date DESC);

-- ============================================================================
-- 4. RAPPROCHEMENT BANCAIRE
-- ============================================================================

-- Alias fournisseurs pour matching bancaire
CREATE TABLE IF NOT EXISTS vendor_aliases (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    vendor_name VARCHAR(200) NOT NULL,      -- Nom officiel du fournisseur
    alias_pattern VARCHAR(200) NOT NULL,    -- Pattern regex ou texte exact
    match_type VARCHAR(20) DEFAULT 'exact', -- 'exact', 'contains', 'regex'
    source VARCHAR(50),                     -- 'bank_lcl', 'bank_bnp', 'manual', 'learned'
    confidence DECIMAL(3,2) DEFAULT 1.0,
    times_matched INTEGER DEFAULT 0,
    last_matched_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, alias_pattern)
);

CREATE INDEX IF NOT EXISTS idx_vendor_aliases_tenant ON vendor_aliases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vendor_aliases_vendor ON vendor_aliases(tenant_id, vendor_name);

-- Rapprochements bancaires
CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    bank_transaction_id INTEGER NOT NULL,  -- ID de la transaction bancaire source

    -- Liens multiples (1 releve = N factures possible)
    matched_items JSONB NOT NULL DEFAULT '[]',
    /*
    Exemple:
    [
      {"type": "invoice", "id": 123, "amount": 450.00, "match_score": 0.95},
      {"type": "expense", "id": 456, "amount": 50.00, "match_score": 0.88}
    ]
    */

    -- Scoring du matching
    match_method VARCHAR(50),  -- 'exact_amount', 'fuzzy_amount', 'vendor_alias', 'manual'
    total_confidence DECIMAL(3,2),

    -- Montants
    bank_amount DECIMAL(15,2),
    matched_amount DECIMAL(15,2),
    discrepancy_amount DECIMAL(15,2),

    -- Etat
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'validated', 'rejected', 'partial'
    validated_by INTEGER,
    validated_at TIMESTAMPTZ,

    -- Notes
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_reconciliation_tenant ON bank_reconciliations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_reconciliation_status ON bank_reconciliations(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_reconciliation_bank_txn ON bank_reconciliations(bank_transaction_id);

-- ============================================================================
-- 5. SNAPSHOTS DE MARGES
-- ============================================================================

-- Snapshots de marges (calculs periodiques)
CREATE TABLE IF NOT EXISTS margin_snapshots (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    snapshot_date DATE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'product', 'recipe', 'category', 'global'
    entity_id INTEGER,                 -- NULL pour global
    entity_name VARCHAR(200),          -- Nom pour reference

    -- Couts
    purchase_cost DECIMAL(15,2),       -- PAMP ou cout unitaire
    direct_cost DECIMAL(15,2),         -- Cout matiere total
    indirect_cost DECIMAL(15,2),       -- Charges indirectes proratisees
    total_cost DECIMAL(15,2),

    -- Revenus
    revenue DECIMAL(15,2),
    quantity_sold DECIMAL(10,2),

    -- Marges
    gross_margin DECIMAL(15,2),
    gross_margin_pct DECIMAL(5,2),
    operating_margin DECIMAL(15,2),
    operating_margin_pct DECIMAL(5,2),

    -- Pertes
    waste_value DECIMAL(15,2),
    waste_pct DECIMAL(5,2),

    -- TVA
    tva_rate DECIMAL(4,2),
    tva_amount DECIMAL(15,2),

    -- Metadata
    calculation_method VARCHAR(50),    -- 'pamp', 'fifo', 'lifo'
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, snapshot_date, entity_type, COALESCE(entity_id, 0))
);

CREATE INDEX IF NOT EXISTS idx_margin_snapshots_tenant ON margin_snapshots(tenant_id);
CREATE INDEX IF NOT EXISTS idx_margin_snapshots_date ON margin_snapshots(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_margin_snapshots_entity ON margin_snapshots(tenant_id, entity_type, entity_id);

-- ============================================================================
-- 6. INTELLIGENCE INVENTAIRE (complement)
-- ============================================================================

-- Parametres de stock intelligent
CREATE TABLE IF NOT EXISTS inventory_intelligence (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    product_id INTEGER NOT NULL,

    -- Stock de securite
    safety_stock DECIMAL(10,2),
    safety_stock_days INTEGER,

    -- Reapprovisionnement
    reorder_point DECIMAL(10,2),
    economic_order_quantity DECIMAL(10,2),  -- EOQ
    lead_time_days INTEGER DEFAULT 3,

    -- Rotation
    rotation_rate DECIMAL(6,2),             -- Turns per month
    days_of_stock DECIMAL(6,2),

    -- Classifications
    abc_class CHAR(1),                      -- A, B, C
    xyz_class CHAR(1),                      -- X, Y, Z (variabilite)
    is_slow_moving BOOLEAN DEFAULT false,
    is_dead_stock BOOLEAN DEFAULT false,

    -- Previsions
    predicted_stockout_date DATE,
    predicted_demand_30d DECIMAL(10,2),

    -- Derniere mise a jour
    last_calculated TIMESTAMPTZ,

    UNIQUE(tenant_id, product_id)
);

CREATE INDEX IF NOT EXISTS idx_inventory_intel_tenant ON inventory_intelligence(tenant_id);
CREATE INDEX IF NOT EXISTS idx_inventory_intel_product ON inventory_intelligence(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_intel_stockout ON inventory_intelligence(predicted_stockout_date);
CREATE INDEX IF NOT EXISTS idx_inventory_intel_abc ON inventory_intelligence(tenant_id, abc_class);

-- ============================================================================
-- 7. EVENT LOG (si pas deja cree)
-- ============================================================================

CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(50) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,  -- 'invoice', 'stock', 'transaction', 'product'
    aggregate_id VARCHAR(100) NOT NULL,   -- ID de l'entite (string pour flexibilite)
    payload JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    user_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_event_log_tenant ON event_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_aggregate ON event_log(aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log(created_at DESC);

COMMENT ON TABLE event_log IS 'Event sourcing - Types: INVOICE_IMPORTED, STOCK_MOVEMENT, PRICE_UPDATED, EXPENSE_CATEGORIZED, ANOMALY_DETECTED';

-- ============================================================================
-- 8. AUDIT TRAIL (si pas deja cree)
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_trail (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,  -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_fields TEXT[],
    user_id INTEGER,
    user_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant ON audit_trail(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_trail(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_trail(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_trail(created_at DESC);

-- ============================================================================
-- 9. FONCTION TRIGGER AUDIT
-- ============================================================================

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_tenant_id INTEGER;
BEGIN
    -- Extraire tenant_id de la ligne
    IF TG_OP = 'DELETE' THEN
        v_tenant_id := OLD.tenant_id;
    ELSE
        v_tenant_id := NEW.tenant_id;
    END IF;

    -- Ignorer si pas de tenant_id
    IF v_tenant_id IS NULL THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        ELSE
            RETURN NEW;
        END IF;
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, new_data)
        VALUES (v_tenant_id, TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, old_data, new_data)
        VALUES (v_tenant_id, TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_trail (tenant_id, table_name, record_id, action, old_data)
        VALUES (v_tenant_id, TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10. APPLIQUER TRIGGERS AUDIT SUR TABLES PRINCIPALES
-- ============================================================================

-- Produits
DROP TRIGGER IF EXISTS audit_trigger_produits ON produits;
CREATE TRIGGER audit_trigger_produits
    AFTER INSERT OR UPDATE OR DELETE ON produits
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Mouvements stock
DROP TRIGGER IF EXISTS audit_trigger_mouvements_stock ON mouvements_stock;
CREATE TRIGGER audit_trigger_mouvements_stock
    AFTER INSERT OR UPDATE OR DELETE ON mouvements_stock
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Transactions finance
DROP TRIGGER IF EXISTS audit_trigger_finance_transactions ON finance_transactions;
CREATE TRIGGER audit_trigger_finance_transactions
    AFTER INSERT OR UPDATE OR DELETE ON finance_transactions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Prix historique
DROP TRIGGER IF EXISTS audit_trigger_price_history ON price_history;
CREATE TRIGGER audit_trigger_price_history
    AFTER INSERT OR UPDATE OR DELETE ON price_history
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- Financial rules
DROP TRIGGER IF EXISTS audit_trigger_financial_rules ON financial_rules;
CREATE TRIGGER audit_trigger_financial_rules
    AFTER INSERT OR UPDATE OR DELETE ON financial_rules
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================================================
-- FIN MIGRATION 002
-- ============================================================================
