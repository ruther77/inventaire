-- Script de vérification post-migration: Fusion comptes LCL
-- Usage: psql -U postgres -d epicerie -f verify_lcl_merge.sql

\timing on
\x off

\echo ''
\echo '========================================'
\echo 'VÉRIFICATION POST-MIGRATION LCL'
\echo '========================================'
\echo ''

-- ==============================================================================
-- 1. État des comptes 15 et 16
-- ==============================================================================

\echo '1. ÉTAT DES COMPTES'
\echo '----------------------------------------'

SELECT
    id,
    label,
    type,
    is_active,
    iban,
    TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI:SS') as last_update
FROM finance_accounts
WHERE id IN (15, 16)
ORDER BY id;

\echo ''

-- ==============================================================================
-- 2. Nombre de transactions par compte
-- ==============================================================================

\echo '2. TRANSACTIONS PAR COMPTE'
\echo '----------------------------------------'

SELECT
    account_id,
    COUNT(*) as nb_transactions,
    TO_CHAR(MIN(date_operation), 'YYYY-MM-DD') as first_date,
    TO_CHAR(MAX(date_operation), 'YYYY-MM-DD') as last_date,
    TO_CHAR(SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END), '999,999,999.99') as total_credits,
    TO_CHAR(SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END), '999,999,999.99') as total_debits
FROM finance_transactions
WHERE account_id IN (15, 16)
GROUP BY account_id
ORDER BY account_id;

\echo ''

-- ==============================================================================
-- 3. Vérification des doublons restants
-- ==============================================================================

\echo '3. DOUBLONS RESTANTS (devrait être vide)'
\echo '----------------------------------------'

SELECT
    date_operation,
    amount,
    COUNT(*) as duplicates,
    STRING_AGG(DISTINCT label, ' | ') as labels,
    ARRAY_AGG(id ORDER BY id) as transaction_ids
FROM finance_transactions
WHERE account_id IN (15, 16)
GROUP BY date_operation, amount
HAVING COUNT(*) > 1
ORDER BY date_operation DESC
LIMIT 20;

\echo ''

-- ==============================================================================
-- 4. Distribution mensuelle pour le compte 16
-- ==============================================================================

\echo '4. DISTRIBUTION MENSUELLE - COMPTE 16'
\echo '----------------------------------------'

SELECT
    TO_CHAR(date_operation, 'YYYY-MM') as month,
    COUNT(*) as nb_tx,
    TO_CHAR(SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END), '999,999.99') as credits,
    TO_CHAR(SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END), '999,999.99') as debits,
    TO_CHAR(
        SUM(CASE WHEN direction = 'IN' THEN amount ELSE -amount END),
        '999,999.99'
    ) as balance_change
FROM finance_transactions
WHERE account_id = 16
GROUP BY TO_CHAR(date_operation, 'YYYY-MM')
ORDER BY month;

\echo ''

-- ==============================================================================
-- 5. Vérification de continuité temporelle
-- ==============================================================================

\echo '5. CONTINUITÉ TEMPORELLE'
\echo '----------------------------------------'

WITH month_series AS (
    SELECT generate_series(
        date_trunc('month', (SELECT MIN(date_operation) FROM finance_transactions WHERE account_id = 16)),
        date_trunc('month', (SELECT MAX(date_operation) FROM finance_transactions WHERE account_id = 16)),
        '1 month'::interval
    )::date as month
),
actual_months AS (
    SELECT DISTINCT date_trunc('month', date_operation)::date as month
    FROM finance_transactions
    WHERE account_id = 16
)
SELECT
    TO_CHAR(ms.month, 'YYYY-MM') as missing_month
FROM month_series ms
LEFT JOIN actual_months am ON ms.month = am.month
WHERE am.month IS NULL;

\echo ''
\echo 'Si aucun résultat ci-dessus: OK (pas de trou dans les données)'
\echo ''

-- ==============================================================================
-- 6. Vérification des index créés
-- ==============================================================================

\echo '6. INDEX CRÉÉS'
\echo '----------------------------------------'

SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'finance_transactions'
  AND (
      indexname LIKE '%dedup%'
      OR indexname LIKE '%stmtline%'
  )
ORDER BY indexname;

\echo ''

-- ==============================================================================
-- 7. Vérification du trigger
-- ==============================================================================

\echo '7. TRIGGER DE DÉTECTION'
\echo '----------------------------------------'

SELECT
    trigger_name,
    event_manipulation,
    action_timing,
    action_statement
FROM information_schema.triggers
WHERE trigger_name = 'trigger_check_duplicate_transaction';

\echo ''

-- ==============================================================================
-- 8. Vérification de la fonction trigger
-- ==============================================================================

\echo '8. FONCTION TRIGGER'
\echo '----------------------------------------'

SELECT
    proname as function_name,
    pg_get_functiondef(oid) as definition
FROM pg_proc
WHERE proname = 'check_duplicate_transaction';

\echo ''

-- ==============================================================================
-- 9. Transactions migrées (note de migration dans le champ note)
-- ==============================================================================

\echo '9. ÉCHANTILLON TRANSACTIONS MIGRÉES'
\echo '----------------------------------------'

SELECT
    id,
    TO_CHAR(date_operation, 'YYYY-MM-DD') as date,
    amount,
    LEFT(label, 50) as label_preview,
    LEFT(note, 80) as migration_note
FROM finance_transactions
WHERE account_id = 16
  AND note LIKE '%Migrated from account 15%'
ORDER BY date_operation DESC
LIMIT 10;

\echo ''

-- ==============================================================================
-- 10. Statistiques globales
-- ==============================================================================

\echo '10. STATISTIQUES GLOBALES'
\echo '----------------------------------------'

WITH stats AS (
    SELECT
        COUNT(*) as total_transactions,
        COUNT(DISTINCT date_operation) as unique_dates,
        SUM(CASE WHEN direction = 'IN' THEN 1 ELSE 0 END) as nb_credits,
        SUM(CASE WHEN direction = 'OUT' THEN 1 ELSE 0 END) as nb_debits,
        SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) as total_credits,
        SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) as total_debits,
        AVG(amount) as avg_amount,
        MIN(amount) as min_amount,
        MAX(amount) as max_amount
    FROM finance_transactions
    WHERE account_id = 16
)
SELECT
    total_transactions,
    unique_dates,
    nb_credits,
    nb_debits,
    TO_CHAR(total_credits, '999,999,999.99') as total_credits_eur,
    TO_CHAR(total_debits, '999,999,999.99') as total_debits_eur,
    TO_CHAR(total_credits - total_debits, '999,999,999.99') as net_balance_eur,
    TO_CHAR(avg_amount, '999.99') as avg_amount_eur,
    TO_CHAR(min_amount, '999.99') as min_amount_eur,
    TO_CHAR(max_amount, '999,999.99') as max_amount_eur
FROM stats;

\echo ''

-- ==============================================================================
-- 11. Top 10 des types de transactions les plus fréquents
-- ==============================================================================

\echo '11. TOP 10 TYPES DE TRANSACTIONS'
\echo '----------------------------------------'

SELECT
    CASE
        WHEN label LIKE 'REMISE CB%' THEN 'REMISE CB'
        WHEN label LIKE 'PRLV SEPA%' THEN 'PRLV SEPA'
        WHEN label LIKE 'VIR SEPA%' THEN 'VIR SEPA'
        WHEN label LIKE 'COMMISSIONS%' THEN 'COMMISSIONS'
        WHEN label LIKE 'VERSEMENT%' THEN 'VERSEMENT'
        ELSE LEFT(label, 30)
    END as transaction_type,
    COUNT(*) as occurrences,
    TO_CHAR(AVG(amount), '999,999.99') as avg_amount,
    TO_CHAR(SUM(amount), '999,999,999.99') as total_amount
FROM finance_transactions
WHERE account_id = 16
GROUP BY transaction_type
ORDER BY occurrences DESC
LIMIT 10;

\echo ''

-- ==============================================================================
-- 12. Vérification des relations (foreign keys)
-- ==============================================================================

\echo '12. RELATIONS (FOREIGN KEYS)'
\echo '----------------------------------------'

SELECT
    'finance_payments' as table_name,
    COUNT(*) as nb_relations
FROM finance_payments
WHERE transaction_id IN (
    SELECT id FROM finance_transactions WHERE account_id = 16
)
UNION ALL
SELECT
    'finance_reconciliations' as table_name,
    COUNT(*) as nb_relations
FROM finance_reconciliations
WHERE transaction_id IN (
    SELECT id FROM finance_transactions WHERE account_id = 16
)
UNION ALL
SELECT
    'finance_transaction_classification' as table_name,
    COUNT(*) as nb_relations
FROM finance_transaction_classification
WHERE transaction_id IN (
    SELECT id FROM finance_transactions WHERE account_id = 16
)
UNION ALL
SELECT
    'finance_transaction_lines' as table_name,
    COUNT(*) as nb_relations
FROM finance_transaction_lines
WHERE transaction_id IN (
    SELECT id FROM finance_transactions WHERE account_id = 16
)
ORDER BY table_name;

\echo ''

-- ==============================================================================
-- RÉSUMÉ FINAL
-- ==============================================================================

\echo '========================================'
\echo 'RÉSUMÉ DE LA VÉRIFICATION'
\echo '========================================'
\echo ''

DO $$
DECLARE
    nb_account_15 INTEGER;
    nb_account_16 INTEGER;
    nb_duplicates INTEGER;
    account_15_active BOOLEAN;
    has_trigger BOOLEAN;
    has_index_dedup BOOLEAN;
    has_index_stmtline BOOLEAN;
BEGIN
    -- Compter transactions
    SELECT COUNT(*) INTO nb_account_15 FROM finance_transactions WHERE account_id = 15;
    SELECT COUNT(*) INTO nb_account_16 FROM finance_transactions WHERE account_id = 16;

    -- Compter doublons
    SELECT COUNT(*) INTO nb_duplicates FROM (
        SELECT date_operation, amount
        FROM finance_transactions
        WHERE account_id = 16
        GROUP BY date_operation, amount
        HAVING COUNT(*) > 1
    ) sub;

    -- Vérifier compte 15
    SELECT is_active INTO account_15_active FROM finance_accounts WHERE id = 15;

    -- Vérifier trigger
    SELECT EXISTS (
        SELECT 1 FROM information_schema.triggers
        WHERE trigger_name = 'trigger_check_duplicate_transaction'
    ) INTO has_trigger;

    -- Vérifier index
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'finance_transactions'
        AND indexname = 'ix_finance_tx_dedup'
    ) INTO has_index_dedup;

    SELECT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'finance_transactions'
        AND indexname = 'ix_finance_tx_ref_externe_stmtline'
    ) INTO has_index_stmtline;

    -- Afficher résumé
    RAISE NOTICE 'Compte 15 transactions:          %', nb_account_15;
    RAISE NOTICE 'Compte 16 transactions:          %', nb_account_16;
    RAISE NOTICE 'Doublons restants:               %', nb_duplicates;
    RAISE NOTICE 'Compte 15 actif:                 %', CASE WHEN account_15_active THEN 'OUI (PROBLÈME!)' ELSE 'NON (OK)' END;
    RAISE NOTICE 'Trigger détection présent:       %', CASE WHEN has_trigger THEN 'OUI (OK)' ELSE 'NON (PROBLÈME!)' END;
    RAISE NOTICE 'Index dedup présent:             %', CASE WHEN has_index_dedup THEN 'OUI (OK)' ELSE 'NON (PROBLÈME!)' END;
    RAISE NOTICE 'Index stmtline présent:          %', CASE WHEN has_index_stmtline THEN 'OUI (OK)' ELSE 'NON (PROBLÈME!)' END;
    RAISE NOTICE '';

    IF nb_account_15 = 0 AND NOT account_15_active AND nb_duplicates = 0 AND has_trigger AND has_index_dedup THEN
        RAISE NOTICE '✓ MIGRATION RÉUSSIE - TOUT EST OK';
    ELSE
        RAISE NOTICE '✗ ATTENTION - Des problèmes ont été détectés';
        IF nb_account_15 > 0 THEN
            RAISE NOTICE '  → Le compte 15 contient encore % transactions', nb_account_15;
        END IF;
        IF account_15_active THEN
            RAISE NOTICE '  → Le compte 15 est encore actif';
        END IF;
        IF nb_duplicates > 0 THEN
            RAISE NOTICE '  → Il reste % doublons', nb_duplicates;
        END IF;
        IF NOT has_trigger THEN
            RAISE NOTICE '  → Le trigger de détection est manquant';
        END IF;
        IF NOT has_index_dedup THEN
            RAISE NOTICE '  → L''index de déduplication est manquant';
        END IF;
    END IF;
END $$;

\echo ''
\echo '========================================'
