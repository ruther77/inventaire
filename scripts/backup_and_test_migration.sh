#!/bin/bash
# ============================================================================
# PHASE 3: Backup et Test de Migration
# ============================================================================
# Script pour sécuriser la migration des orphelins restaurant_bank_statements
# Usage: ./scripts/backup_and_test_migration.sh
# ============================================================================

set -e  # Exit on error

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/migration_phase3_${TIMESTAMP}"
DB_NAME="${DB_NAME:-app_db}"
DB_USER="${DB_USER:-app_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "============================================================================"
echo "PHASE 3: BACKUP ET TEST DE MIGRATION"
echo "============================================================================"
echo "Timestamp: ${TIMESTAMP}"
echo "Database: ${DB_NAME}"
echo "Backup dir: ${BACKUP_DIR}"
echo "============================================================================"

# 1. Créer le répertoire de backup
echo -e "\n[1/8] Création du répertoire de backup..."
mkdir -p "${BACKUP_DIR}"

# 2. Backup de la table restaurant_bank_statements
echo -e "\n[2/8] Backup de restaurant_bank_statements..."
pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    -t restaurant_bank_statements \
    --format=custom \
    --file="${BACKUP_DIR}/restaurant_bank_statements.backup"
echo "✓ Backup créé: ${BACKUP_DIR}/restaurant_bank_statements.backup"

# 3. Backup des tables finance (au cas où)
echo -e "\n[3/8] Backup des tables finance_*..."
pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    -t finance_bank_statements \
    -t finance_bank_statement_lines \
    -t finance_transactions \
    -t finance_reconciliations \
    -t finance_transaction_expense_links \
    --format=custom \
    --file="${BACKUP_DIR}/finance_tables.backup"
echo "✓ Backup créé: ${BACKUP_DIR}/finance_tables.backup"

# 4. Export CSV des orphelins pour référence
echo -e "\n[4/8] Export CSV des orphelins..."
psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c "
    COPY (
        SELECT
            rbs.id,
            rbs.tenant_id,
            rbs.account,
            rbs.date,
            rbs.libelle,
            rbs.categorie,
            rbs.montant,
            rbs.type,
            rbs.depense_id
        FROM restaurant_bank_statements rbs
        LEFT JOIN finance_bank_statement_lines fbsl
            ON rbs.date::date = fbsl.date_operation
            AND ABS(rbs.montant - fbsl.montant) < 0.01
        WHERE fbsl.id IS NULL
        ORDER BY rbs.date DESC
    ) TO STDOUT WITH CSV HEADER
" > "${BACKUP_DIR}/orphans_to_migrate.csv"
echo "✓ CSV créé: ${BACKUP_DIR}/orphans_to_migrate.csv"

# 5. Analyse préalable
echo -e "\n[5/8] Exécution de l'analyse SQL..."
psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} \
    -f scripts/analyze_orphans.sql \
    > "${BACKUP_DIR}/analysis_report.txt" 2>&1
echo "✓ Rapport créé: ${BACKUP_DIR}/analysis_report.txt"

# 6. Test en mode dry-run
echo -e "\n[6/8] Test de migration (dry-run)..."
python scripts/migrate_restaurant_orphans.py --dry-run \
    > "${BACKUP_DIR}/dryrun_output.txt" 2>&1
echo "✓ Dry-run terminé: ${BACKUP_DIR}/dryrun_output.txt"

# 7. Afficher le résumé
echo -e "\n[7/8] Résumé de l'analyse..."
echo "============================================================================"
cat "${BACKUP_DIR}/analysis_report.txt" | grep -A 20 "RÉSUMÉ POUR MIGRATION" || true
echo "============================================================================"

# 8. Demander confirmation pour migration
echo -e "\n[8/8] Prêt pour la migration"
echo "============================================================================"
echo "Backups créés dans: ${BACKUP_DIR}"
echo ""
echo "Pour exécuter la migration:"
echo "  python scripts/migrate_restaurant_orphans.py --execute"
echo ""
echo "Pour restaurer en cas de problème:"
echo "  pg_restore -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} --clean ${BACKUP_DIR}/restaurant_bank_statements.backup"
echo "============================================================================"

# 9. Instructions de validation post-migration
cat > "${BACKUP_DIR}/VALIDATION.md" << 'EOF'
# Validation Post-Migration

## Étapes de validation

### 1. Vérifier le nombre de lignes migrées
```sql
SELECT COUNT(*) FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;
```

### 2. Vérifier les liens depense_id
```sql
SELECT COUNT(*) FROM finance_transaction_expense_links
WHERE migrated_from = 'restaurant_bank_statements';
```

### 3. Vérifier qu'il n'y a plus d'orphelins
```sql
SELECT COUNT(*)
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL;
```
Résultat attendu: 0

### 4. Vérifier l'intégrité des montants
```sql
SELECT
    SUM(rbs.montant) as total_rbs,
    SUM(fbsl.montant) as total_fbsl,
    SUM(rbs.montant) - SUM(fbsl.montant) as difference
FROM restaurant_bank_statements rbs
JOIN finance_bank_statement_lines fbsl
    ON fbsl.raw_data::jsonb->>'original_rbs_id' = rbs.id::text;
```
Différence attendue: proche de 0

### 5. Tester la vue de compatibilité
```sql
SELECT COUNT(*) FROM restaurant_bank_statements;  -- Vue
```
Devrait fonctionner sans erreur après migration

## En cas de problème

### Restaurer les backups
```bash
# Restaurer restaurant_bank_statements
pg_restore -h localhost -p 5432 -U app_user -d app_db --clean \
    backups/migration_phase3_*/restaurant_bank_statements.backup

# Restaurer les tables finance
pg_restore -h localhost -p 5432 -U app_user -d app_db --clean \
    backups/migration_phase3_*/finance_tables.backup
```

### Rollback manuel
```sql
-- Supprimer les données migrées
DELETE FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;

DELETE FROM finance_transaction_expense_links
WHERE migrated_from = 'restaurant_bank_statements';

DELETE FROM finance_transactions
WHERE source = 'migration_rbs';
```

## Finalisation

Une fois validé:
```sql
-- Renommer la table comme dépréciée
ALTER TABLE restaurant_bank_statements
RENAME TO _deprecated_restaurant_bank_statements;

-- Créer la vue de compatibilité (voir db/migrations/006_deprecate_restaurant_bank_statements.sql)
```
EOF

echo "✓ Guide de validation créé: ${BACKUP_DIR}/VALIDATION.md"
echo ""
echo "============================================================================"
echo "BACKUP ET TEST TERMINÉS AVEC SUCCÈS"
echo "============================================================================"
