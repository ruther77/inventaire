-- Migration: Add mobile support fields to ingredients table
-- Date: 2025-12-11
-- Description: Add code_barre and seuil_alerte to ingredients for mobile scanning

-- ============================================================================
-- 1. Add code_barre column for barcode scanning
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ingredients'
        AND column_name = 'code_barre'
    ) THEN
        ALTER TABLE ingredients ADD COLUMN code_barre VARCHAR(50);
        COMMENT ON COLUMN ingredients.code_barre IS 'Barcode for mobile scanning';
    END IF;
END $$;

-- ============================================================================
-- 2. Add seuil_alerte column for stock alerts
-- ============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ingredients'
        AND column_name = 'seuil_alerte'
    ) THEN
        ALTER TABLE ingredients ADD COLUMN seuil_alerte REAL DEFAULT 5.0;
        COMMENT ON COLUMN ingredients.seuil_alerte IS 'Low stock alert threshold';
    END IF;
END $$;

-- ============================================================================
-- 3. Create index for fast barcode lookups
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_ingredients_code_barre
ON ingredients(code_barre)
WHERE code_barre IS NOT NULL;

COMMENT ON INDEX idx_ingredients_code_barre IS 'Fast barcode lookup for mobile scanning';

-- ============================================================================
-- 4. Create index for stock alert queries
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_ingredients_stock_alert
ON ingredients(tenant_id, stock_actuel, seuil_alerte);

COMMENT ON INDEX idx_ingredients_stock_alert IS 'Fast stock alert queries';

-- ============================================================================
-- 5. Create index for plat ingredients cost calculation
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_plat_ingredients_plat_id
ON plat_ingredients(plat_id, tenant_id);

COMMENT ON INDEX idx_plat_ingredients_plat_id IS 'Fast plat cost calculation';

-- ============================================================================
-- 6. Verify mouvements_stock table supports mobile adjustments
-- ============================================================================
-- The table should already exist from init.sql
-- We just verify it has the required columns

DO $$
BEGIN
    -- Check mouvements_stock exists and has required columns
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'mouvements_stock'
    ) THEN
        RAISE EXCEPTION 'Table mouvements_stock does not exist. Run init.sql first.';
    END IF;

    -- Verify source column exists for audit trail
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock'
        AND column_name = 'source'
    ) THEN
        ALTER TABLE mouvements_stock ADD COLUMN source TEXT;
        COMMENT ON COLUMN mouvements_stock.source IS 'Source of movement (e.g., mobile_adjust:breakage:notes)';
    END IF;
END $$;

-- ============================================================================
-- 7. Add mobile adjustment types to mouvements_stock
-- ============================================================================
-- These types will be used by mobile endpoints:
-- - ajustement_mobile_in: Stock increase from mobile
-- - ajustement_mobile_out: Stock decrease from mobile

COMMENT ON TABLE mouvements_stock IS 'Stock movements with support for mobile adjustments (types: ajustement_mobile_in, ajustement_mobile_out)';

-- ============================================================================
-- 8. Grant permissions (if using role-based access)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON ingredients TO restaurant_user;
-- GRANT SELECT, INSERT ON mouvements_stock TO restaurant_user;

-- ============================================================================
-- 9. Verify migration
-- ============================================================================
-- Run this to verify all columns exist:
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name IN ('ingredients', 'mouvements_stock')
  AND column_name IN ('code_barre', 'seuil_alerte', 'source')
ORDER BY table_name, ordinal_position;

-- Verify indexes:
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('ingredients', 'plat_ingredients')
  AND indexname LIKE 'idx_%'
ORDER BY tablename, indexname;

-- ============================================================================
-- 10. Sample data for testing
-- ============================================================================
-- Uncomment to insert test data:

/*
-- Update some ingredients with barcodes for testing
UPDATE ingredients
SET code_barre = '3245678901234',
    seuil_alerte = 10.0
WHERE nom = 'Tomate' AND tenant_id = 1;

UPDATE ingredients
SET code_barre = '3245678901235',
    seuil_alerte = 5.0
WHERE nom = 'Poulet' AND tenant_id = 1;

UPDATE ingredients
SET code_barre = '3245678901236',
    seuil_alerte = 15.0
WHERE nom = 'Farine' AND tenant_id = 1;

-- Verify
SELECT id, nom, code_barre, stock_actuel, seuil_alerte
FROM ingredients
WHERE tenant_id = 1 AND code_barre IS NOT NULL
LIMIT 10;
*/
