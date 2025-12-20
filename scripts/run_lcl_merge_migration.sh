#!/bin/bash

# Script pour exécuter la migration de fusion des comptes LCL
# Usage: ./run_lcl_merge_migration.sh

set -e  # Arrêter en cas d'erreur

# Configuration
CONTAINER_ID="57a2d3cfb432_inventaire-db"
DB_NAME="epicerie"
DB_USER="postgres"
MIGRATION_FILE="/home/ruuuzer/Documents/monprojet/db/migrations/004_merge_lcl_accounts.sql"

echo "========================================"
echo "MIGRATION: FUSION COMPTES LCL"
echo "========================================"
echo ""
echo "Container: $CONTAINER_ID"
echo "Database:  $DB_NAME"
echo "User:      $DB_USER"
echo "Migration: $MIGRATION_FILE"
echo ""

# Vérifier que le container existe et est actif
if ! docker ps --format '{{.ID}}' | grep -q "$CONTAINER_ID"; then
    echo "ERREUR: Container $CONTAINER_ID n'est pas actif"
    exit 1
fi

# Vérifier que le fichier de migration existe
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "ERREUR: Fichier de migration introuvable: $MIGRATION_FILE"
    exit 1
fi

echo "Étape 1: Copie du fichier de migration dans le container..."
docker cp "$MIGRATION_FILE" "$CONTAINER_ID:/tmp/004_merge_lcl_accounts.sql"
echo "OK"
echo ""

echo "Étape 2: Création d'une sauvegarde avant migration..."
BACKUP_FILE="/tmp/backup_before_lcl_merge_$(date +%Y%m%d_%H%M%S).sql"
docker exec "$CONTAINER_ID" pg_dump -U "$DB_USER" -d "$DB_NAME" -t finance_transactions -t finance_accounts > "$BACKUP_FILE"
echo "Sauvegarde créée: $BACKUP_FILE"
echo ""

echo "Étape 3: Exécution de la migration..."
echo "========================================"
echo ""

docker exec -i "$CONTAINER_ID" psql -U "$DB_USER" -d "$DB_NAME" -f /tmp/004_merge_lcl_accounts.sql

echo ""
echo "========================================"
echo "Migration terminée!"
echo "========================================"
echo ""
echo "Sauvegarde disponible: $BACKUP_FILE"
echo ""
echo "Pour restaurer en cas de problème:"
echo "  psql -U $DB_USER -d $DB_NAME < $BACKUP_FILE"
echo ""
