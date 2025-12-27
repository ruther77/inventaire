-- Migration: Créer des vues matérialisées pour les statistiques
-- Date: 2025-12-17
-- Objectif: Améliorer les performances des requêtes de reporting

-- ============================================================================
-- VUE 1: Solde journalier par compte
-- Usage: Dashboard trésorerie, graphiques de flux
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_daily_balance CASCADE;

CREATE MATERIALIZED VIEW mv_daily_balance AS
SELECT
    account_id,
    date_operation::date as date,
    SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) as credits,
    SUM(CASE WHEN direction = 'OUT' THEN ABS(amount) ELSE 0 END) as debits,
    SUM(CASE WHEN direction = 'IN' THEN amount ELSE -ABS(amount) END) as net,
    COUNT(*) as transaction_count
FROM finance_transactions
GROUP BY account_id, date_operation::date
ORDER BY account_id, date;

CREATE UNIQUE INDEX ON mv_daily_balance(account_id, date);
CREATE INDEX ON mv_daily_balance(date);

COMMENT ON MATERIALIZED VIEW mv_daily_balance IS
'Solde journalier agrégé par compte. Rafraîchir avec: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_balance';

-- ============================================================================
-- VUE 2: Répartition par catégorie (mensuelle)
-- Usage: Graphiques de répartition des dépenses
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_category_monthly CASCADE;

CREATE MATERIALIZED VIEW mv_category_monthly AS
SELECT
    ft.entity_id,
    COALESCE(ftc.category_id, 0) as category_id,
    fc.name as category_name,
    DATE_TRUNC('month', ft.date_operation)::date as month,
    ft.direction,
    COUNT(*) as tx_count,
    SUM(ABS(ft.amount)) as total_amount,
    AVG(ABS(ft.amount)) as avg_amount
FROM finance_transactions ft
LEFT JOIN finance_transaction_classification ftc ON ftc.transaction_id = ft.id
LEFT JOIN finance_categories fc ON fc.id = ftc.category_id
GROUP BY ft.entity_id, ftc.category_id, fc.name, DATE_TRUNC('month', ft.date_operation), ft.direction
ORDER BY month DESC, total_amount DESC;

CREATE UNIQUE INDEX ON mv_category_monthly(entity_id, COALESCE(category_id, 0), month, direction);
CREATE INDEX ON mv_category_monthly(month);
CREATE INDEX ON mv_category_monthly(entity_id);

COMMENT ON MATERIALIZED VIEW mv_category_monthly IS
'Répartition mensuelle par catégorie et direction. Rafraîchir avec: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_category_monthly';

-- ============================================================================
-- VUE 3: État de rapprochement par compte
-- Usage: KPIs de rapprochement bancaire
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_reconciliation_status CASCADE;

CREATE MATERIALIZED VIEW mv_reconciliation_status AS
SELECT
    fa.id as account_id,
    fa.label as account_name,
    fa.entity_id,
    COUNT(ft.id) as total_transactions,
    COUNT(CASE WHEN fr.invoice_id IS NOT NULL THEN 1 END) as matched_with_invoice,
    COUNT(ft.id) - COUNT(CASE WHEN fr.invoice_id IS NOT NULL THEN 1 END) as unmatched,
    ROUND(
        COUNT(CASE WHEN fr.invoice_id IS NOT NULL THEN 1 END)::numeric /
        NULLIF(COUNT(ft.id), 0) * 100,
        1
    ) as match_rate_percent,
    MIN(ft.date_operation) as first_transaction,
    MAX(ft.date_operation) as last_transaction,
    SUM(CASE WHEN ft.direction = 'OUT' THEN ABS(ft.amount) ELSE 0 END) as total_debits,
    SUM(CASE WHEN ft.direction = 'IN' THEN ft.amount ELSE 0 END) as total_credits
FROM finance_accounts fa
LEFT JOIN finance_transactions ft ON ft.account_id = fa.id
LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
GROUP BY fa.id, fa.label, fa.entity_id;

CREATE UNIQUE INDEX ON mv_reconciliation_status(account_id);
CREATE INDEX ON mv_reconciliation_status(entity_id);

COMMENT ON MATERIALIZED VIEW mv_reconciliation_status IS
'État de rapprochement agrégé par compte. Rafraîchir avec: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_reconciliation_status';

-- ============================================================================
-- VUE 4: Top fournisseurs par montant
-- Usage: Analyse des dépenses fournisseurs
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_top_vendors CASCADE;

CREATE MATERIALIZED VIEW mv_top_vendors AS
SELECT
    ft.entity_id,
    COALESCE(fv.name, 'Non identifié') as vendor_name,
    fv.id as vendor_id,
    DATE_TRUNC('month', ft.date_operation)::date as month,
    COUNT(*) as invoice_count,
    SUM(ABS(ft.amount)) as total_amount,
    AVG(ABS(ft.amount)) as avg_amount,
    MIN(ft.date_operation) as first_transaction,
    MAX(ft.date_operation) as last_transaction
FROM finance_transactions ft
LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
LEFT JOIN processed_invoices pi ON pi.id = fr.invoice_id
LEFT JOIN finance_vendors fv ON fv.id = pi.vendor_id
WHERE ft.direction = 'OUT'
GROUP BY ft.entity_id, fv.name, fv.id, DATE_TRUNC('month', ft.date_operation)
ORDER BY month DESC, total_amount DESC;

CREATE INDEX ON mv_top_vendors(entity_id, month);
CREATE INDEX ON mv_top_vendors(vendor_id);

COMMENT ON MATERIALIZED VIEW mv_top_vendors IS
'Top fournisseurs par montant et mois. Rafraîchir avec: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_top_vendors';

-- ============================================================================
-- VUE 5: Résumé des importations
-- Usage: Suivi des imports de données
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS mv_import_summary CASCADE;

CREATE MATERIALIZED VIEW mv_import_summary AS
SELECT
    fbs.account_id,
    fa.label as account_name,
    DATE_TRUNC('month', fbs.period_start)::date as period_month,
    COUNT(DISTINCT fbs.id) as statement_count,
    SUM(line_counts.line_count) as total_lines,
    MIN(fbs.period_start) as earliest_period,
    MAX(fbs.period_end) as latest_period,
    MAX(fbs.imported_at) as last_import
FROM finance_bank_statements fbs
JOIN finance_accounts fa ON fa.id = fbs.account_id
LEFT JOIN LATERAL (
    SELECT COUNT(*) as line_count
    FROM finance_bank_statement_lines fbsl
    WHERE fbsl.statement_id = fbs.id
) line_counts ON true
GROUP BY fbs.account_id, fa.label, DATE_TRUNC('month', fbs.period_start)
ORDER BY period_month DESC;

CREATE INDEX ON mv_import_summary(account_id);
CREATE INDEX ON mv_import_summary(period_month);

COMMENT ON MATERIALIZED VIEW mv_import_summary IS
'Résumé des importations par compte et mois. Rafraîchir avec: REFRESH MATERIALIZED VIEW CONCURRENTLY mv_import_summary';

-- ============================================================================
-- FONCTION: Rafraîchir toutes les vues matérialisées
-- Usage: Appelée par cron ou manuellement
-- ============================================================================
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS TABLE(view_name TEXT, status TEXT, duration_ms NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
    v_start TIMESTAMP;
    v_views TEXT[] := ARRAY[
        'mv_daily_balance',
        'mv_category_monthly',
        'mv_reconciliation_status',
        'mv_top_vendors',
        'mv_import_summary'
    ];
    v_view TEXT;
BEGIN
    FOREACH v_view IN ARRAY v_views
    LOOP
        v_start := clock_timestamp();
        BEGIN
            EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', v_view);
            view_name := v_view;
            status := 'success';
            duration_ms := ROUND(EXTRACT(EPOCH FROM (clock_timestamp() - v_start)) * 1000, 2);
        EXCEPTION WHEN OTHERS THEN
            view_name := v_view;
            status := 'error: ' || SQLERRM;
            duration_ms := ROUND(EXTRACT(EPOCH FROM (clock_timestamp() - v_start)) * 1000, 2);
        END;
        RETURN NEXT;
    END LOOP;
END;
$$;

COMMENT ON FUNCTION refresh_all_materialized_views() IS
'Rafraîchit toutes les vues matérialisées. Usage: SELECT * FROM refresh_all_materialized_views()';
