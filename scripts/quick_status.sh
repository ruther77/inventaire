#!/bin/bash
# ============================================================================
# Quick Status Check - Phase 3 Migration
# ============================================================================
# Usage: ./scripts/quick_status.sh
# ============================================================================

set -e

DB_NAME="${DB_NAME:-app_db}"
DB_USER="${DB_USER:-app_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                    PHASE 3 - MIGRATION STATUS                          ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Fonction pour exécuter une requête et afficher le résultat
query() {
    psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -t -A -c "$1"
}

# 1. Orphelins restants
echo "📊 Orphelins restants..."
ORPHANS=$(query "
    SELECT COUNT(*)
    FROM restaurant_bank_statements rbs
    LEFT JOIN finance_bank_statement_lines fbsl
        ON rbs.date::date = fbsl.date_operation
        AND ABS(rbs.montant - fbsl.montant) < 0.01
    WHERE fbsl.id IS NULL;
")

if [ "$ORPHANS" -eq 0 ]; then
    echo "   ✓ Aucun orphelin (migration complète)"
else
    echo "   ⚠ $ORPHANS orphelins restants"
fi

# 2. Lignes migrées
echo ""
echo "📊 Lignes migrées..."
MIGRATED=$(query "
    SELECT COUNT(*)
    FROM finance_bank_statement_lines
    WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;
")
echo "   → $MIGRATED lignes migrées vers finance_bank_statement_lines"

# 3. Transactions créées
echo ""
echo "📊 Transactions créées..."
TRANSACTIONS=$(query "
    SELECT COUNT(*)
    FROM finance_transactions
    WHERE source = 'migration_rbs';
")
echo "   → $TRANSACTIONS transactions créées"

# 4. Liens dépenses
echo ""
echo "📊 Liens dépenses..."
DEPENSE_LINKS=$(query "
    SELECT COUNT(*)
    FROM finance_transaction_expense_links
    WHERE migrated_from = 'restaurant_bank_statements';
")
echo "   → $DEPENSE_LINKS liens depense_id préservés"

# 5. Réconciliations
echo ""
echo "📊 Réconciliations..."
RECONCILIATIONS=$(query "
    SELECT COUNT(*)
    FROM finance_reconciliations fr
    JOIN finance_bank_statement_lines fbsl ON fbsl.id = fr.statement_line_id
    WHERE fbsl.raw_data::jsonb->>'migrated_at' IS NOT NULL;
")
echo "   → $RECONCILIATIONS réconciliations automatiques"

# 6. Status global
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ORPHANS" -eq 0 ] && [ "$MIGRATED" -gt 0 ]; then
    echo "✓ MIGRATION COMPLÈTE"
    echo ""
    echo "Prochaine étape: Déprécier la table"
    echo "  psql -U $DB_USER -d $DB_NAME -f db/migrations/006_deprecate_restaurant_bank_statements.sql"
elif [ "$ORPHANS" -eq 0 ] && [ "$MIGRATED" -eq 0 ]; then
    echo "⚠ AUCUNE MIGRATION DÉTECTÉE"
    echo ""
    echo "La migration n'a pas encore été exécutée."
    echo "Exécuter: python scripts/migrate_restaurant_orphans.py --execute"
elif [ "$ORPHANS" -gt 0 ] && [ "$MIGRATED" -gt 0 ]; then
    echo "⚠ MIGRATION PARTIELLE"
    echo ""
    echo "Il reste $ORPHANS orphelins à migrer."
    echo "Relancer: python scripts/migrate_restaurant_orphans.py --execute"
else
    echo "⚠ ÉTAT INCONNU"
    echo ""
    echo "Exécuter une validation complète:"
    echo "  psql -U $DB_USER -d $DB_NAME -f scripts/validate_migration.sql"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Pour une validation complète, exécuter:"
echo "  psql -U $DB_USER -d $DB_NAME -f scripts/validate_migration.sql"
echo ""
