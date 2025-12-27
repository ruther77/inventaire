-- ================================================================================
-- MIGRATION: Tables pour restructuration majeure - Décembre 2025
-- ================================================================================
-- Ce fichier crée les tables manquantes pour activer les fonctionnalités avancées
-- déjà codées dans core/finance/*.py mais non connectées à la BDD
-- ================================================================================

-- Vérifier que le tenant Intelligence existe
INSERT INTO tenants (id, name, code)
VALUES (4, 'Intelligence HQ', 'intelligence')
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;

-- ================================================================================
-- 1. EVENT SOURCING - event_log
-- ================================================================================
-- Stocke tous les événements métier pour traçabilité et replay

CREATE TABLE IF NOT EXISTS event_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    event_type VARCHAR(50) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,  -- 'invoice', 'stock', 'transaction', 'product'
    aggregate_id INTEGER NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by INTEGER,  -- user_id si disponible
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE event_log IS 'Event sourcing - Types: INVOICE_IMPORTED, INVOICE_VALIDATED, STOCK_RECEIVED, STOCK_CONSUMED, EXPENSE_CATEGORIZED, PRICE_UPDATED, ANOMALY_DETECTED, FORECAST_GENERATED';

CREATE INDEX IF NOT EXISTS idx_event_log_tenant ON event_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_event_log_type ON event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_event_log_aggregate ON event_log(aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_log_created ON event_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_event_log_payload ON event_log USING GIN (payload);

-- ================================================================================
-- 2. AUDIT TRAIL COMPLET - audit_trail
-- ================================================================================
-- Piste d'audit who/what/when/before/after pour toutes les tables critiques

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
    session_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE audit_trail IS 'Piste d''audit complète - Conforme RGPD';

CREATE INDEX IF NOT EXISTS idx_audit_trail_tenant ON audit_trail(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_table ON audit_trail(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_user ON audit_trail(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_trail_date ON audit_trail(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_trail_action ON audit_trail(action);

-- ================================================================================
-- 3. FINANCIAL RULES ENGINE - financial_rules
-- ================================================================================
-- Règles de catégorisation automatique des transactions

CREATE TABLE IF NOT EXISTS financial_rules (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 100,  -- Plus bas = plus prioritaire
    is_active BOOLEAN DEFAULT true,

    -- Conditions (JSONB pour flexibilité)
    conditions JSONB NOT NULL DEFAULT '{}',
    -- Exemple: {"vendor_pattern": "METRO.*", "amount_min": 100, "description_keywords": ["alimentaire"]}

    -- Actions
    target_category_id INTEGER,  -- FK vers finance_categories
    auto_validate BOOLEAN DEFAULT false,
    confidence_threshold DECIMAL(3,2) DEFAULT 0.80,

    -- Stats d'apprentissage
    times_applied INTEGER DEFAULT 0,
    times_confirmed INTEGER DEFAULT 0,
    times_rejected INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by INTEGER
);

COMMENT ON TABLE financial_rules IS 'Règles de catégorisation auto avec apprentissage progressif';

CREATE INDEX IF NOT EXISTS idx_financial_rules_tenant_active ON financial_rules(tenant_id, is_active, priority);
CREATE INDEX IF NOT EXISTS idx_financial_rules_conditions ON financial_rules USING GIN (conditions);

-- Historique des applications de règles
CREATE TABLE IF NOT EXISTS rule_applications (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES financial_rules(id) ON DELETE SET NULL,
    transaction_id INTEGER NOT NULL,
    confidence_score DECIMAL(3,2),
    was_confirmed BOOLEAN,
    user_feedback VARCHAR(20),  -- 'confirmed', 'rejected', 'modified'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rule_applications_rule ON rule_applications(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_applications_transaction ON rule_applications(transaction_id);

-- ================================================================================
-- 4. COMPTABILITÉ ANALYTIQUE - analytic_axes & analytic_assignments
-- ================================================================================
-- Axes d'analyse multi-dimensionnels

CREATE TABLE IF NOT EXISTS analytic_axes (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    axis_type VARCHAR(50) NOT NULL,  -- 'entity', 'category', 'project', 'cost_center', 'product_line'
    parent_id INTEGER REFERENCES analytic_axes(id),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, code)
);

COMMENT ON TABLE analytic_axes IS 'Axes analytiques configurables pour ventilation multi-dimensionnelle';

CREATE INDEX IF NOT EXISTS idx_analytic_axes_tenant ON analytic_axes(tenant_id, axis_type);
CREATE INDEX IF NOT EXISTS idx_analytic_axes_parent ON analytic_axes(parent_id);

-- Affectations analytiques
CREATE TABLE IF NOT EXISTS analytic_assignments (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    source_type VARCHAR(50) NOT NULL,  -- 'transaction', 'invoice_line', 'stock_movement', 'expense'
    source_id INTEGER NOT NULL,
    axis_id INTEGER NOT NULL REFERENCES analytic_axes(id),
    amount DECIMAL(15,2) NOT NULL,
    percentage DECIMAL(5,2),  -- Pour ventilation en %
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_type, source_id, axis_id)
);

CREATE INDEX IF NOT EXISTS idx_analytic_assignments_source ON analytic_assignments(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_analytic_assignments_axis ON analytic_assignments(axis_id);

-- ================================================================================
-- 5. FORECASTING CACHE - forecast_cache
-- ================================================================================
-- Cache des prévisions pour éviter recalculs coûteux

CREATE TABLE IF NOT EXISTS forecast_cache (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    forecast_type VARCHAR(50) NOT NULL,  -- 'sales', 'cashflow', 'stock', 'price'
    target_entity VARCHAR(100),  -- 'product', 'category', 'global'
    target_id INTEGER,  -- ID du produit/catégorie si applicable

    -- Résultats
    forecast_date DATE NOT NULL,
    predicted_value DECIMAL(15,2),
    confidence_lower DECIMAL(15,2),
    confidence_upper DECIMAL(15,2),
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    -- Méthode utilisée
    model_type VARCHAR(50),  -- 'prophet', 'holt_winters', 'exponential_smoothing', 'regression'
    model_params JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}',  -- MAE, RMSE, MAPE

    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    UNIQUE(tenant_id, forecast_type, target_entity, COALESCE(target_id, -1), forecast_date)
);

COMMENT ON TABLE forecast_cache IS 'Cache des prévisions avec métadonnées de qualité';

CREATE INDEX IF NOT EXISTS idx_forecast_cache_lookup ON forecast_cache(tenant_id, forecast_type, target_entity);
CREATE INDEX IF NOT EXISTS idx_forecast_cache_date ON forecast_cache(forecast_date);
CREATE INDEX IF NOT EXISTS idx_forecast_cache_expires ON forecast_cache(expires_at) WHERE expires_at IS NOT NULL;

-- ================================================================================
-- 6. SUPPLIER SCORING - supplier_scores & supplier_score_history
-- ================================================================================
-- Scores qualité fournisseurs multi-critères

CREATE TABLE IF NOT EXISTS supplier_scores (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    supplier_id INTEGER NOT NULL,  -- Référence au fournisseur (restaurant_fournisseurs ou autre)
    supplier_name VARCHAR(200),    -- Dénormalisé pour perf

    -- Composantes du score (0-1, haut = bon)
    price_volatility_score DECIMAL(3,2),  -- Stabilité des prix
    delivery_reliability_score DECIMAL(3,2),  -- Ponctualité
    invoice_accuracy_score DECIMAL(3,2),  -- Précision factures
    stock_variance_score DECIMAL(3,2),  -- Écarts livraison
    payment_terms_score DECIMAL(3,2),  -- Conditions paiement
    quality_score DECIMAL(3,2),  -- Qualité produits
    responsiveness_score DECIMAL(3,2),  -- Réactivité

    -- Score global pondéré
    overall_score DECIMAL(3,2),
    score_trend VARCHAR(20),  -- 'improving', 'stable', 'declining'

    -- Données de calcul
    calculation_date DATE NOT NULL,
    data_points INTEGER DEFAULT 0,
    calculation_params JSONB DEFAULT '{}',

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, supplier_id, calculation_date)
);

COMMENT ON TABLE supplier_scores IS 'Scoring fournisseurs multi-critères avec tendances';

CREATE INDEX IF NOT EXISTS idx_supplier_scores_tenant_supplier ON supplier_scores(tenant_id, supplier_id);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_date ON supplier_scores(calculation_date DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_scores_overall ON supplier_scores(tenant_id, overall_score DESC);

-- Historique des scores
CREATE TABLE IF NOT EXISTS supplier_score_history (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    supplier_id INTEGER NOT NULL,
    score_date DATE NOT NULL,
    overall_score DECIMAL(3,2),
    components JSONB NOT NULL,  -- Toutes les composantes

    UNIQUE(tenant_id, supplier_id, score_date)
);

CREATE INDEX IF NOT EXISTS idx_supplier_score_history_lookup ON supplier_score_history(tenant_id, supplier_id, score_date DESC);

-- ================================================================================
-- 7. BANK RECONCILIATION AVANCÉ - bank_reconciliations & vendor_aliases
-- ================================================================================
-- Rapprochement bancaire avec matching multi-lignes

CREATE TABLE IF NOT EXISTS bank_reconciliations (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    bank_statement_id INTEGER,  -- FK vers finance_bank_statement_lines ou autre

    -- Liens multiples (1 relevé = N factures possible)
    matched_items JSONB NOT NULL DEFAULT '[]',
    -- Exemple: [{"type": "invoice", "id": 123, "amount": 450.00, "match_score": 0.95}]

    -- Scoring du matching
    match_method VARCHAR(50),  -- 'exact', 'fuzzy_amount', 'fuzzy_date', 'vendor_alias', 'multi_line'
    total_confidence DECIMAL(3,2),
    amount_matched DECIMAL(15,2),
    amount_remaining DECIMAL(15,2),

    -- État
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'validated', 'rejected', 'partial'
    validated_by INTEGER,
    validated_at TIMESTAMPTZ,

    -- Alertes
    has_discrepancy BOOLEAN DEFAULT false,
    discrepancy_amount DECIMAL(15,2),
    discrepancy_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE bank_reconciliations IS 'Rapprochement bancaire avec matching intelligent';

CREATE INDEX IF NOT EXISTS idx_bank_reconciliations_tenant ON bank_reconciliations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_bank_reconciliations_status ON bank_reconciliations(status);
CREATE INDEX IF NOT EXISTS idx_bank_reconciliations_statement ON bank_reconciliations(bank_statement_id);

-- Alias fournisseurs pour matching automatique
CREATE TABLE IF NOT EXISTS vendor_aliases (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    vendor_id INTEGER,  -- FK vers restaurant_fournisseurs
    vendor_name VARCHAR(200),  -- Dénormalisé
    alias_pattern VARCHAR(200) NOT NULL,  -- Regex ou pattern exact
    alias_type VARCHAR(20) DEFAULT 'exact',  -- 'exact', 'contains', 'regex'
    source VARCHAR(50),  -- 'bank_lcl', 'bank_bnp', 'manual', 'learned'
    confidence DECIMAL(3,2) DEFAULT 1.0,
    times_used INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, alias_pattern)
);

COMMENT ON TABLE vendor_aliases IS 'Alias fournisseurs pour matching bancaire automatique';

CREATE INDEX IF NOT EXISTS idx_vendor_aliases_tenant ON vendor_aliases(tenant_id);
CREATE INDEX IF NOT EXISTS idx_vendor_aliases_vendor ON vendor_aliases(vendor_id);

-- ================================================================================
-- 8. MARGIN SNAPSHOTS - margin_snapshots
-- ================================================================================
-- Snapshots journalisés des marges par entité

CREATE TABLE IF NOT EXISTS margin_snapshots (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    snapshot_date DATE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,  -- 'product', 'recipe', 'category', 'global'
    entity_id INTEGER,  -- NULL pour global
    entity_name VARCHAR(200),  -- Dénormalisé

    -- Coûts
    purchase_cost DECIMAL(15,2),  -- PAMP
    direct_cost DECIMAL(15,2),    -- Coût matière
    indirect_cost DECIMAL(15,2),  -- Charges indirectes proratisées
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

    -- Métadonnées
    calculation_method VARCHAR(50),
    data_completeness DECIMAL(3,2),  -- % de données disponibles

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(tenant_id, snapshot_date, entity_type, COALESCE(entity_id, -1))
);

COMMENT ON TABLE margin_snapshots IS 'Snapshots journalisés des marges avec historique';

CREATE INDEX IF NOT EXISTS idx_margin_snapshots_tenant_date ON margin_snapshots(tenant_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_margin_snapshots_entity ON margin_snapshots(entity_type, entity_id);

-- ================================================================================
-- 9. INVENTORY INTELLIGENCE - inventory_intelligence & inventory_alerts
-- ================================================================================
-- Paramètres de stock intelligent par produit

CREATE TABLE IF NOT EXISTS inventory_intelligence (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200),  -- Dénormalisé

    -- Stock de sécurité
    safety_stock DECIMAL(10,2),
    safety_stock_days INTEGER,
    service_level DECIMAL(3,2) DEFAULT 0.95,  -- 95%

    -- Réapprovisionnement
    reorder_point DECIMAL(10,2),
    economic_order_quantity DECIMAL(10,2),  -- EOQ
    lead_time_days INTEGER DEFAULT 3,

    -- Rotation
    rotation_rate DECIMAL(6,2),  -- Turns per month
    days_of_stock DECIMAL(6,2),

    -- Classification
    abc_class CHAR(1),  -- A, B, C
    xyz_class CHAR(1),  -- X, Y, Z
    is_slow_moving BOOLEAN DEFAULT false,
    is_dead_stock BOOLEAN DEFAULT false,

    -- Prévisions
    avg_daily_demand DECIMAL(10,2),
    demand_std_dev DECIMAL(10,2),
    predicted_stockout_date DATE,
    predicted_demand_30d DECIMAL(10,2),

    -- Dernière mise à jour
    last_calculated TIMESTAMPTZ,
    calculation_params JSONB DEFAULT '{}',

    UNIQUE(tenant_id, product_id)
);

COMMENT ON TABLE inventory_intelligence IS 'Intelligence stock: EOQ, safety stock, classification ABC-XYZ';

CREATE INDEX IF NOT EXISTS idx_inventory_intelligence_tenant ON inventory_intelligence(tenant_id);
CREATE INDEX IF NOT EXISTS idx_inventory_intelligence_stockout ON inventory_intelligence(predicted_stockout_date) WHERE predicted_stockout_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_inventory_intelligence_dead ON inventory_intelligence(is_dead_stock) WHERE is_dead_stock = true;

-- Alertes inventaire
CREATE TABLE IF NOT EXISTS inventory_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    product_id INTEGER NOT NULL,
    product_name VARCHAR(200),
    alert_type VARCHAR(50) NOT NULL,
    -- Types: 'low_stock', 'stockout_imminent', 'dead_stock', 'variance_detected', 'price_spike', 'demand_surge'
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'critical'
    message TEXT,
    data JSONB DEFAULT '{}',

    is_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMPTZ,

    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE inventory_alerts IS 'Alertes intelligentes stock: ruptures, anomalies, prix';

CREATE INDEX IF NOT EXISTS idx_inventory_alerts_tenant ON inventory_alerts(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_inventory_alerts_unack ON inventory_alerts(tenant_id, is_acknowledged) WHERE is_acknowledged = false;
CREATE INDEX IF NOT EXISTS idx_inventory_alerts_type ON inventory_alerts(alert_type, severity);

-- ================================================================================
-- 10. DETECTED ANOMALIES - detected_anomalies
-- ================================================================================
-- Anomalies détectées par le système

CREATE TABLE IF NOT EXISTS detected_anomalies (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    anomaly_type VARCHAR(50) NOT NULL,
    -- Types: 'amount_outlier', 'duplicate_payment', 'debit_credit_mismatch', 'unusual_frequency',
    -- 'suspicious_time', 'missing_invoice', 'price_deviation', 'round_amount'
    severity VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high', 'critical'

    -- Contexte
    source_type VARCHAR(50),  -- 'transaction', 'invoice', 'stock_movement'
    source_id INTEGER,
    related_entity VARCHAR(100),

    -- Description
    description TEXT NOT NULL,
    details JSONB DEFAULT '{}',

    -- Valeurs
    expected_value DECIMAL(15,2),
    actual_value DECIMAL(15,2),
    deviation_pct DECIMAL(5,2),

    -- État
    status VARCHAR(20) DEFAULT 'new',  -- 'new', 'investigating', 'resolved', 'false_positive'
    resolution_note TEXT,
    resolved_by INTEGER,
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE detected_anomalies IS 'Anomalies détectées automatiquement';

CREATE INDEX IF NOT EXISTS idx_detected_anomalies_tenant ON detected_anomalies(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_detected_anomalies_status ON detected_anomalies(status) WHERE status NOT IN ('resolved', 'false_positive');
CREATE INDEX IF NOT EXISTS idx_detected_anomalies_type ON detected_anomalies(anomaly_type, severity);

-- ================================================================================
-- 11. TRIGGER AUDIT AUTOMATIQUE (optionnel, à activer par table)
-- ================================================================================

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    v_old_data JSONB;
    v_new_data JSONB;
    v_tenant_id INTEGER;
BEGIN
    -- Extraire tenant_id (essayer plusieurs colonnes)
    IF TG_OP = 'DELETE' THEN
        v_tenant_id := COALESCE(OLD.tenant_id, 1);
        v_old_data := to_jsonb(OLD);
    ELSE
        v_tenant_id := COALESCE(NEW.tenant_id, 1);
        v_new_data := to_jsonb(NEW);
    END IF;

    IF TG_OP = 'UPDATE' THEN
        v_old_data := to_jsonb(OLD);
    END IF;

    INSERT INTO audit_trail (tenant_id, table_name, record_id, action, old_data, new_data)
    VALUES (
        v_tenant_id,
        TG_TABLE_NAME,
        CASE WHEN TG_OP = 'DELETE' THEN OLD.id ELSE NEW.id END,
        TG_OP,
        v_old_data,
        v_new_data
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Créer triggers sur tables critiques (à activer selon besoin)
-- DROP TRIGGER IF EXISTS audit_trigger_produits ON produits;
-- CREATE TRIGGER audit_trigger_produits
-- AFTER INSERT OR UPDATE OR DELETE ON produits
-- FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ================================================================================
-- FIN MIGRATION
-- ================================================================================
SELECT 'Migration restructuration terminée avec succès' AS status;
