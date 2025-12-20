#!/bin/bash
# Script pour appliquer la migration 008 - Categorization Feedback
# Ce script crée la table finance_categorization_feedback pour le feedback ML

set -e

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-inventaire}"
DB_USER="${DB_USER:-postgres}"

MIGRATION_FILE="db/migrations/008_categorization_feedback.sql"

echo "=========================================="
echo "Migration 008: Categorization Feedback"
echo "=========================================="
echo ""
echo "Database: $DB_NAME"
echo "Host: $DB_HOST"
echo "User: $DB_USER"
echo ""

# Check if table already exists
echo "Checking if table already exists..."
EXISTS=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
  "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'finance_categorization_feedback');")

if [ "$EXISTS" = "t" ]; then
    echo "✓ Table finance_categorization_feedback already exists."
    echo ""

    # Show table structure
    echo "Table structure:"
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
      "\d finance_categorization_feedback"
    echo ""

    # Show count
    COUNT=$(PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc \
      "SELECT COUNT(*) FROM finance_categorization_feedback;")
    echo "Current feedback records: $COUNT"

else
    echo "✗ Table does not exist. Applying migration..."
    echo ""

    # Apply migration
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"

    echo ""
    echo "✓ Migration applied successfully!"
    echo ""

    # Verify
    echo "Verifying table creation..."
    PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c \
      "\d finance_categorization_feedback"
fi

echo ""
echo "=========================================="
echo "Migration complete!"
echo "=========================================="
