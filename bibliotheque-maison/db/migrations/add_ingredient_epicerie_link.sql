-- Migration: Add epicerie link columns to ingredients table
-- and create restaurant_epicerie_sku_map table

-- Add new columns to ingredients table if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'categorie') THEN
        ALTER TABLE ingredients ADD COLUMN categorie TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'fournisseur') THEN
        ALTER TABLE ingredients ADD COLUMN fournisseur TEXT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'cout_unitaire') THEN
        ALTER TABLE ingredients ADD COLUMN cout_unitaire NUMERIC(12,4) DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'stock_actuel') THEN
        ALTER TABLE ingredients ADD COLUMN stock_actuel NUMERIC(14,4) DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'stock_min') THEN
        ALTER TABLE ingredients ADD COLUMN stock_min NUMERIC(14,4) DEFAULT 0;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ingredients' AND column_name = 'produit_epicerie_id') THEN
        ALTER TABLE ingredients ADD COLUMN produit_epicerie_id INT REFERENCES produits(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Create restaurant_epicerie_sku_map table if it doesn't exist
CREATE TABLE IF NOT EXISTS restaurant_epicerie_sku_map (
    id SERIAL PRIMARY KEY,
    tenant_restaurant INT NOT NULL DEFAULT 2,
    tenant_epicerie INT NOT NULL DEFAULT 1,
    produit_restaurant_id INT NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    produit_epicerie_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    ratio NUMERIC(12,4) DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_restaurant, produit_restaurant_id)
);

CREATE INDEX IF NOT EXISTS idx_restaurant_epicerie_sku_map_epicerie ON restaurant_epicerie_sku_map (tenant_epicerie, produit_epicerie_id);

-- Sync existing ingredient data from produits if linked
-- This updates ingredients that already have a matching product in epicerie by name
UPDATE ingredients i
SET
    categorie = COALESCE(i.categorie, p.categorie),
    cout_unitaire = CASE WHEN i.cout_unitaire = 0 THEN COALESCE(p.prix_achat, 0) ELSE i.cout_unitaire END,
    produit_epicerie_id = p.id
FROM produits p
WHERE LOWER(i.nom) = LOWER(p.nom)
  AND i.produit_epicerie_id IS NULL;

SELECT 'Migration completed successfully. Updated ' || COUNT(*) || ' ingredients with epicerie links.'
FROM ingredients WHERE produit_epicerie_id IS NOT NULL;
