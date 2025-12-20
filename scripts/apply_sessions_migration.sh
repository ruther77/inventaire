#!/bin/bash
# Script pour appliquer la migration des sessions d'import
# Usage: ./scripts/apply_sessions_migration.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MIGRATION_FILE="$PROJECT_ROOT/db/migrations/add_import_sessions.sql"

echo "=========================================="
echo "Migration: Historique Import par Session"
echo "=========================================="
echo ""

# Vérifier que le fichier de migration existe
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Erreur: Fichier de migration introuvable: $MIGRATION_FILE"
    exit 1
fi

echo "📄 Fichier de migration: $MIGRATION_FILE"
echo ""

# Demander confirmation
read -p "Appliquer la migration à la base de données ? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Migration annulée"
    exit 0
fi

# Appliquer la migration
echo "🔄 Application de la migration..."
echo ""

# Utiliser la connexion par défaut (ajuster si nécessaire)
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-inventaire}"
DB_USER="${DB_USER:-postgres}"

# Option 1: Via docker-compose (si postgres est dans docker)
if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "📦 Utilisation de docker-compose..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
        psql -U "$DB_USER" -d "$DB_NAME" < "$MIGRATION_FILE"
# Option 2: Via psql local
elif command -v psql &> /dev/null; then
    echo "🔧 Utilisation de psql local..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$MIGRATION_FILE"
else
    echo "❌ Erreur: Ni docker-compose ni psql n'est disponible"
    echo "Appliquez manuellement la migration avec:"
    echo "  psql -U $DB_USER -d $DB_NAME < $MIGRATION_FILE"
    exit 1
fi

echo ""
echo "✅ Migration appliquée avec succès !"
echo ""

# Vérifier que les colonnes existent
echo "🔍 Vérification..."
VERIFY_SQL="SELECT table_name, column_name FROM information_schema.columns WHERE column_name = 'session_id' AND table_name IN ('zero_click_jobs', 'processed_invoices');"

if command -v docker-compose &> /dev/null && [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
        psql -U "$DB_USER" -d "$DB_NAME" -c "$VERIFY_SQL"
elif command -v psql &> /dev/null; then
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "$VERIFY_SQL"
fi

echo ""
echo "=========================================="
echo "✨ Migration terminée !"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "  1. Redémarrer le backend: cd backend && uvicorn main:app --reload"
echo "  2. Redémarrer le frontend: cd frontend && npm run dev"
echo "  3. Tester l'import: Aller sur /invoices et faire un import"
echo "  4. Voir les sessions: Aller sur Historique > Historique par session"
echo ""
