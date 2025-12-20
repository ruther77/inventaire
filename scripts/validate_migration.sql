-- ============================================================================
-- VALIDATION POST-MIGRATION - Phase 3
-- ============================================================================
-- Objectif: Valider que la migration des orphelins est réussie
-- Usage: psql -U app_user -d app_db -f scripts/validate_migration.sql
-- ============================================================================

\echo '============================================================================'
\echo 'VALIDATION POST-MIGRATION - PHASE 3'
\echo '============================================================================'
\echo ''

-- ============================================================================
-- 1. VÉRIFICATION DES ORPHELINS RESTANTS
-- ============================================================================
\echo '1. ORPHELINS RESTANTS'
\echo '====================='
\echo 'Attendu: 0 orphelins (tous doivent être migrés)'
\echo ''

SELECT
    COUNT(*) as orphelins_restants,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ SUCCÈS'
        ELSE '✗ ÉCHEC - Il reste des orphelins à migrer'
    END as status
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL;

\echo ''

-- ============================================================================
-- 2. LIGNES MIGRÉES
-- ============================================================================
\echo '2. LIGNES MIGRÉES VERS FINANCE'
\echo '==============================='
\echo ''

SELECT
    COUNT(*) as total_lignes_migrees,
    MIN(fbsl.date_operation) as date_min,
    MAX(fbsl.date_operation) as date_max,
    SUM(fbsl.montant) as montant_total
FROM finance_bank_statement_lines fbsl
WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL;

\echo ''

-- ============================================================================
-- 3. LIENS DEPENSE_ID PRÉSERVÉS
-- ============================================================================
\echo '3. LIENS DÉPENSES PRÉSERVÉS'
\echo '==========================='
\echo ''

SELECT
    COUNT(*) as liens_depense_crees,
    COUNT(DISTINCT tel.depense_id) as depenses_uniques,
    COUNT(DISTINCT tel.transaction_id) as transactions_liees
FROM finance_transaction_expense_links tel
WHERE tel.migrated_from = 'restaurant_bank_statements';

\echo ''

-- Vérifier l'intégrité des liens
SELECT
    COUNT(*) as liens_valides,
    CASE
        WHEN COUNT(*) = (
            SELECT COUNT(*) FROM finance_transaction_expense_links
            WHERE migrated_from = 'restaurant_bank_statements'
        ) THEN '✓ SUCCÈS - Tous les liens sont valides'
        ELSE '✗ ÉCHEC - Certains liens sont cassés'
    END as status
FROM finance_transaction_expense_links tel
JOIN restaurant_depenses rd ON rd.id = tel.depense_id
JOIN finance_transactions ft ON ft.id = tel.transaction_id
WHERE tel.migrated_from = 'restaurant_bank_statements';

\echo ''

-- ============================================================================
-- 4. TRANSACTIONS CRÉÉES
-- ============================================================================
\echo '4. TRANSACTIONS FINANCE CRÉÉES'
\echo '==============================='
\echo ''

SELECT
    COUNT(*) as transactions_creees,
    SUM(CASE WHEN direction = 'IN' THEN 1 ELSE 0 END) as entrees,
    SUM(CASE WHEN direction = 'OUT' THEN 1 ELSE 0 END) as sorties,
    SUM(amount) as montant_total
FROM finance_transactions
WHERE source = 'migration_rbs';

\echo ''

-- ============================================================================
-- 5. RÉCONCILIATIONS AUTO
-- ============================================================================
\echo '5. RÉCONCILIATIONS AUTOMATIQUES'
\echo '================================'
\echo ''

SELECT
    COUNT(*) as reconciliations_creees,
    COUNT(DISTINCT fr.statement_line_id) as lignes_reconciliees,
    COUNT(DISTINCT fr.transaction_id) as transactions_reconciliees
FROM finance_reconciliations fr
JOIN finance_bank_statement_lines fbsl ON fbsl.id = fr.statement_line_id
WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL;

\echo ''

-- ============================================================================
-- 6. INTÉGRITÉ DES MONTANTS
-- ============================================================================
\echo '6. INTÉGRITÉ DES MONTANTS'
\echo '========================='
\echo 'Vérification que les montants migrés correspondent aux sources'
\echo ''

WITH migration_check AS (
    SELECT
        COUNT(*) as nb_lignes,
        SUM(rbs.montant) as total_source,
        SUM(fbsl.montant) as total_cible,
        ABS(SUM(rbs.montant) - SUM(fbsl.montant)) as difference
    FROM restaurant_bank_statements rbs
    JOIN finance_bank_statement_lines fbsl
        ON fbsl.raw_data::jsonb->>'original_rbs_id' = rbs.id::text
)
SELECT
    nb_lignes,
    ROUND(total_source::numeric, 2) as total_source_eur,
    ROUND(total_cible::numeric, 2) as total_cible_eur,
    ROUND(difference::numeric, 2) as difference_eur,
    CASE
        WHEN difference < 0.01 THEN '✓ SUCCÈS - Montants identiques'
        WHEN difference < 1.00 THEN '⚠ ATTENTION - Petite différence'
        ELSE '✗ ÉCHEC - Différence significative'
    END as status
FROM migration_check;

\echo ''

-- ============================================================================
-- 7. COMPTES CRÉÉS/UTILISÉS
-- ============================================================================
\echo '7. COMPTES BANCAIRES UTILISÉS'
\echo '=============================='
\echo ''

SELECT
    fa.id,
    fa.label as compte,
    fa.type,
    COUNT(DISTINCT fbsl.id) as lignes_migrees,
    SUM(fbsl.montant) as montant_total
FROM finance_accounts fa
JOIN finance_bank_statements fbs ON fbs.account_id = fa.id
JOIN finance_bank_statement_lines fbsl ON fbsl.statement_id = fbs.id
WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL
GROUP BY fa.id, fa.label, fa.type
ORDER BY lignes_migrees DESC;

\echo ''

-- ============================================================================
-- 8. DISTRIBUTION TEMPORELLE
-- ============================================================================
\echo '8. DISTRIBUTION PAR MOIS'
\echo '========================'
\echo ''

SELECT
    TO_CHAR(fbsl.date_operation, 'YYYY-MM') as mois,
    COUNT(*) as nb_lignes,
    SUM(fbsl.montant) as montant_total,
    AVG(fbsl.montant) as montant_moyen
FROM finance_bank_statement_lines fbsl
WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL
GROUP BY TO_CHAR(fbsl.date_operation, 'YYYY-MM')
ORDER BY mois DESC
LIMIT 12;

\echo ''

-- ============================================================================
-- 9. DÉTECTION D'ANOMALIES
-- ============================================================================
\echo '9. DÉTECTION D''ANOMALIES'
\echo '========================='
\echo ''

-- Lignes migrées sans transaction
SELECT
    COUNT(*) as lignes_sans_transaction,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ SUCCÈS - Toutes les lignes ont une transaction'
        ELSE '⚠ ATTENTION - Certaines lignes n''ont pas de transaction'
    END as status
FROM finance_bank_statement_lines fbsl
LEFT JOIN finance_reconciliations fr ON fr.statement_line_id = fbsl.id
WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL
  AND fr.id IS NULL;

\echo ''

-- Transactions sans réconciliation
SELECT
    COUNT(*) as transactions_sans_reconciliation,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ SUCCÈS - Toutes les transactions sont réconciliées'
        ELSE '⚠ ATTENTION - Certaines transactions ne sont pas réconciliées'
    END as status
FROM finance_transactions ft
LEFT JOIN finance_reconciliations fr ON fr.transaction_id = ft.id
WHERE ft.source = 'migration_rbs'
  AND fr.id IS NULL;

\echo ''

-- Doublons potentiels (même checksum)
SELECT
    COUNT(*) as doublons_detectes,
    CASE
        WHEN COUNT(*) = 0 THEN '✓ SUCCÈS - Pas de doublons'
        ELSE '⚠ ATTENTION - Doublons détectés'
    END as status
FROM (
    SELECT checksum, COUNT(*) as cnt
    FROM finance_bank_statement_lines
    WHERE checksum IS NOT NULL
    GROUP BY checksum
    HAVING COUNT(*) > 1
) duplicates;

\echo ''

-- ============================================================================
-- 10. RÉSUMÉ GLOBAL
-- ============================================================================
\echo '10. RÉSUMÉ GLOBAL DE LA MIGRATION'
\echo '=================================='
\echo ''

WITH stats AS (
    SELECT
        (SELECT COUNT(*) FROM restaurant_bank_statements) as total_rbs,
        (SELECT COUNT(*) FROM finance_bank_statement_lines
         WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL) as migrated,
        (SELECT COUNT(*) FROM finance_transaction_expense_links
         WHERE migrated_from = 'restaurant_bank_statements') as linked_depenses,
        (SELECT COUNT(*) FROM finance_transactions
         WHERE source = 'migration_rbs') as transactions,
        (SELECT COUNT(*) FROM finance_reconciliations fr
         JOIN finance_bank_statement_lines fbsl ON fbsl.id = fr.statement_line_id
         WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL) as reconciliations,
        (SELECT COUNT(*) FROM restaurant_bank_statements rbs
         LEFT JOIN finance_bank_statement_lines fbsl
             ON rbs.date::date = fbsl.date_operation
             AND ABS(rbs.montant - fbsl.montant) < 0.01
         WHERE fbsl.id IS NULL) as orphelins_restants
)
SELECT
    total_rbs as "Total RBS",
    migrated as "Lignes migrées",
    ROUND(migrated * 100.0 / NULLIF(total_rbs, 0), 2) as "% Migration",
    transactions as "Transactions créées",
    reconciliations as "Réconciliations",
    linked_depenses as "Liens dépenses",
    orphelins_restants as "Orphelins restants",
    CASE
        WHEN orphelins_restants = 0
         AND migrated > 0
         AND transactions = migrated
         AND reconciliations = migrated
        THEN '✓ MIGRATION RÉUSSIE'
        WHEN orphelins_restants = 0 AND migrated > 0
        THEN '⚠ MIGRATION OK MAIS À VÉRIFIER'
        WHEN orphelins_restants > 0
        THEN '✗ MIGRATION INCOMPLÈTE'
        ELSE '⚠ ÉTAT INCONNU'
    END as "Status Global"
FROM stats;

\echo ''
\echo '============================================================================'
\echo 'VALIDATION TERMINÉE'
\echo '============================================================================'
\echo ''
\echo 'Interprétation des résultats:'
\echo '  ✓ SUCCÈS = Tout est OK'
\echo '  ⚠ ATTENTION = À vérifier mais pas bloquant'
\echo '  ✗ ÉCHEC = Problème détecté, action requise'
\echo ''
\echo 'Si "MIGRATION RÉUSSIE", vous pouvez procéder à la dépréciation de la table:'
\echo '  psql -U app_user -d app_db -f db/migrations/006_deprecate_restaurant_bank_statements.sql'
\echo '============================================================================'
