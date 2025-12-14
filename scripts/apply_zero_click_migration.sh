#!/bin/bash
# Script pour appliquer la migration zero_click_jobs

set -e

echo "=========================================="
echo "Migration Zero-Click Jobs"
echo "=========================================="
echo ""

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "alembic.ini" ]; then
    echo "❌ Erreur: alembic.ini non trouvé. Exécutez ce script depuis la racine du projet."
    exit 1
fi

echo "📋 État actuel de la base de données:"
alembic current

echo ""
echo "📜 Migrations disponibles:"
alembic history | head -20

echo ""
echo "🔄 Application de la migration zero_click_jobs..."
alembic upgrade 20251211_zero_click_jobs

echo ""
echo "✅ Migration appliquée avec succès!"
echo ""

echo "📋 Nouvel état de la base de données:"
alembic current

echo ""
echo "🔍 Vérification de la table zero_click_jobs:"
psql $DATABASE_URL -c "\d zero_click_jobs" || echo "⚠️  Impossible de vérifier la table (psql non disponible ou DATABASE_URL non défini)"

echo ""
echo "=========================================="
echo "Migration terminée!"
echo "=========================================="
