-- ============================================================================
-- PHASE 3: ANALYSE DES ORPHELINS - restaurant_bank_statements
-- ============================================================================
-- Objectif: Identifier les données orphelines avant migration
-- Date: 2025-12-19
-- ============================================================================

\echo '============================================================================'
\echo 'ANALYSE DES ORPHELINS: restaurant_bank_statements'
\echo '============================================================================'

-- 1. STATISTIQUES GLOBALES
\echo '\n1. STATISTIQUES GLOBALES'
\echo '------------------------'

SELECT
    'Total restaurant_bank_statements' as metric,
    COUNT(*) as count
FROM restaurant_bank_statements
UNION ALL
SELECT
    'Total finance_bank_statement_lines',
    COUNT(*)
FROM finance_bank_statement_lines
UNION ALL
SELECT
    'Total finance_transactions',
    COUNT(*)
FROM finance_transactions
WHERE source = 'migration_rbs' OR ref_externe LIKE 'stmtline:%';

-- 2. IDENTIFIER LES ORPHELINS (pas de correspondance exacte)
\echo '\n2. ORPHELINS DÉTECTÉS'
\echo '----------------------'

WITH orphans AS (
    SELECT
        rbs.id,
        rbs.account,
        rbs.date,
        rbs.libelle,
        rbs.montant,
        rbs.depense_id,
        CASE
            WHEN fbsl.id IS NOT NULL THEN 'matched'
            ELSE 'orphan'
        END as status
    FROM restaurant_bank_statements rbs
    LEFT JOIN finance_bank_statement_lines fbsl
        ON rbs.date::date = fbsl.date_operation
        AND ABS(rbs.montant - fbsl.montant) < 0.01
)
SELECT
    status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
FROM orphans
GROUP BY status
ORDER BY status;

-- 3. ORPHELINS PAR COMPTE
\echo '\n3. ORPHELINS PAR COMPTE'
\echo '------------------------'

SELECT
    rbs.account,
    COUNT(*) as total_count,
    SUM(CASE WHEN fbsl.id IS NULL THEN 1 ELSE 0 END) as orphan_count,
    ROUND(SUM(CASE WHEN fbsl.id IS NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as orphan_pct
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
GROUP BY rbs.account
ORDER BY orphan_count DESC;

-- 4. ORPHELINS AVEC LIENS depense_id
\echo '\n4. ORPHELINS AVEC LIENS DÉPENSES'
\echo '----------------------------------'

SELECT
    COUNT(DISTINCT rbs.id) as orphans_with_depense,
    COUNT(DISTINCT rbs.depense_id) as unique_depenses,
    SUM(CASE WHEN rd.id IS NULL THEN 1 ELSE 0 END) as broken_links
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
LEFT JOIN restaurant_depenses rd ON rd.id = rbs.depense_id
WHERE fbsl.id IS NULL
  AND rbs.depense_id IS NOT NULL;

-- 5. ORPHELINS PAR PÉRIODE
\echo '\n5. ORPHELINS PAR MOIS'
\echo '----------------------'

SELECT
    rbs.mois,
    COUNT(*) as total_count,
    SUM(CASE WHEN fbsl.id IS NULL THEN 1 ELSE 0 END) as orphan_count,
    ROUND(AVG(CASE WHEN fbsl.id IS NULL THEN ABS(rbs.montant) ELSE 0 END), 2) as avg_orphan_amount
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
GROUP BY rbs.mois
ORDER BY rbs.mois DESC
LIMIT 12;

-- 6. ÉCHANTILLON D'ORPHELINS À MIGRER
\echo '\n6. ÉCHANTILLON ORPHELINS (10 premières lignes)'
\echo '------------------------------------------------'

SELECT
    rbs.id,
    rbs.account,
    rbs.date,
    rbs.libelle,
    rbs.montant,
    rbs.type,
    rbs.depense_id,
    rbs.categorie
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL
ORDER BY rbs.date DESC
LIMIT 10;

-- 7. VÉRIFIER LES COMPTES FINANCE EXISTANTS
\echo '\n7. COMPTES FINANCE EXISTANTS (pour mapping)'
\echo '---------------------------------------------'

SELECT
    fa.id,
    fa.entity_id,
    fa.type,
    fa.label,
    COUNT(DISTINCT fbsl.id) as statement_lines_count
FROM finance_accounts fa
LEFT JOIN finance_bank_statements fbs ON fbs.account_id = fa.id
LEFT JOIN finance_bank_statement_lines fbsl ON fbsl.statement_id = fbs.id
WHERE fa.entity_id IN (1, 2)  -- Restaurant entities
GROUP BY fa.id, fa.entity_id, fa.type, fa.label
ORDER BY fa.entity_id, fa.label;

-- 8. VÉRIFIER LES DOUBLONS POTENTIELS
\echo '\n8. DOUBLONS POTENTIELS (même date/montant/libellé)'
\echo '----------------------------------------------------'

SELECT
    date,
    montant,
    libelle,
    COUNT(*) as duplicate_count
FROM restaurant_bank_statements
GROUP BY date, montant, libelle
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC
LIMIT 10;

-- 9. RÉSUMÉ FINAL
\echo '\n9. RÉSUMÉ POUR MIGRATION'
\echo '-------------------------'

WITH stats AS (
    SELECT
        COUNT(*) as total_rbs,
        SUM(CASE WHEN fbsl.id IS NULL THEN 1 ELSE 0 END) as orphans,
        SUM(CASE WHEN fbsl.id IS NULL AND rbs.depense_id IS NOT NULL THEN 1 ELSE 0 END) as orphans_with_depense,
        SUM(CASE WHEN fbsl.id IS NULL THEN ABS(rbs.montant) ELSE 0 END) as total_orphan_amount
    FROM restaurant_bank_statements rbs
    LEFT JOIN finance_bank_statement_lines fbsl
        ON rbs.date::date = fbsl.date_operation
        AND ABS(rbs.montant - fbsl.montant) < 0.01
)
SELECT
    total_rbs as "Total RBS",
    orphans as "Orphelins à migrer",
    ROUND(orphans * 100.0 / total_rbs, 2) as "% Orphelins",
    orphans_with_depense as "Orphelins avec dépense",
    ROUND(total_orphan_amount, 2) as "Montant total orphelins (€)"
FROM stats;

\echo '\n============================================================================'
\echo 'ANALYSE TERMINÉE'
\echo '============================================================================'
\echo '\nProchaines étapes:'
\echo '1. Vérifier les statistiques ci-dessus'
\echo '2. Créer un backup: pg_dump -t restaurant_bank_statements ...'
\echo '3. Exécuter: python scripts/migrate_restaurant_orphans.py --dry-run'
\echo '4. Si OK: python scripts/migrate_restaurant_orphans.py --execute'
\echo '============================================================================'
