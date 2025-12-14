-- Migration: Ajouter le suivi des coûts dans les mouvements de stock
-- Date: 2025-12-09
-- Description: Permet de tracer le prix unitaire au moment de chaque mouvement
--              pour un calcul précis des marges rétrospectives

-- 1. Ajouter les colonnes de coût aux mouvements de stock
ALTER TABLE mouvements_stock
ADD COLUMN IF NOT EXISTS prix_unitaire_ht NUMERIC(12,4),
ADD COLUMN IF NOT EXISTS fournisseur VARCHAR(255),
ADD COLUMN IF NOT EXISTS reference VARCHAR(255),
ADD COLUMN IF NOT EXISTS utilisateur VARCHAR(100),
ADD COLUMN IF NOT EXISTS type_mouvement VARCHAR(20);

-- 2. Créer la colonne source si elle n'a pas le bon type
-- (dans certaines versions, 'source' existe déjà)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock' AND column_name = 'source'
    ) THEN
        ALTER TABLE mouvements_stock ADD COLUMN source VARCHAR(50) DEFAULT 'MANUEL';
    END IF;
END $$;

-- 3. Renommer date_mvt en date_mouvement si nécessaire
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock' AND column_name = 'date_mvt'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock' AND column_name = 'date_mouvement'
    ) THEN
        ALTER TABLE mouvements_stock RENAME COLUMN date_mvt TO date_mouvement;
    END IF;

    -- Créer date_mouvement si ni l'un ni l'autre n'existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock' AND column_name = 'date_mouvement'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'mouvements_stock' AND column_name = 'date_mvt'
    ) THEN
        ALTER TABLE mouvements_stock ADD COLUMN date_mouvement TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- 4. Créer la table inventory_alerts si elle n'existe pas
CREATE TABLE IF NOT EXISTS inventory_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    message TEXT,
    data JSONB DEFAULT '{}',
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_inventory_alerts_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(id),
    CONSTRAINT fk_inventory_alerts_product FOREIGN KEY (product_id) REFERENCES produits(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inventory_alerts_tenant ON inventory_alerts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_inventory_alerts_product ON inventory_alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_alerts_type ON inventory_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_inventory_alerts_unack ON inventory_alerts(tenant_id, is_acknowledged) WHERE NOT is_acknowledged;

-- 5. Ajouter index pour les requêtes fréquentes sur mouvements_stock
CREATE INDEX IF NOT EXISTS idx_mouvements_stock_tenant ON mouvements_stock(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_stock_produit ON mouvements_stock(produit_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_stock_date ON mouvements_stock(date_mouvement);
CREATE INDEX IF NOT EXISTS idx_mouvements_stock_fournisseur ON mouvements_stock(fournisseur) WHERE fournisseur IS NOT NULL;

-- 6. Vue pour le calcul du coût moyen pondéré (PAMP) par produit
CREATE OR REPLACE VIEW v_product_weighted_cost AS
SELECT
    tenant_id,
    produit_id,
    SUM(quantite * COALESCE(prix_unitaire_ht, 0)) / NULLIF(SUM(quantite), 0) AS pamp,
    SUM(quantite) AS total_quantity,
    COUNT(*) AS movement_count,
    MAX(date_mouvement) AS last_movement_date
FROM mouvements_stock
WHERE type_mouvement = 'ENTREE' OR type = 'ENTREE'
GROUP BY tenant_id, produit_id;

COMMENT ON VIEW v_product_weighted_cost IS 'Prix d''Achat Moyen Pondéré calculé depuis les mouvements d''entrée';

-- 7. Fonction pour calculer le PAMP d'un produit à une date donnée
CREATE OR REPLACE FUNCTION get_pamp_at_date(
    p_tenant_id INTEGER,
    p_product_id INTEGER,
    p_date TIMESTAMPTZ DEFAULT NOW()
) RETURNS NUMERIC AS $$
DECLARE
    v_pamp NUMERIC;
BEGIN
    SELECT SUM(quantite * COALESCE(prix_unitaire_ht, 0)) / NULLIF(SUM(quantite), 0)
    INTO v_pamp
    FROM mouvements_stock
    WHERE tenant_id = p_tenant_id
      AND produit_id = p_product_id
      AND (type_mouvement = 'ENTREE' OR type = 'ENTREE')
      AND date_mouvement <= p_date;

    RETURN COALESCE(v_pamp, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_pamp_at_date IS 'Calcule le PAMP d''un produit à une date donnée';

-- 8. Mettre à jour les mouvements existants avec le prix du produit si manquant
UPDATE mouvements_stock ms
SET prix_unitaire_ht = p.prix_achat
FROM produits p
WHERE ms.produit_id = p.id
  AND ms.tenant_id = p.tenant_id
  AND ms.prix_unitaire_ht IS NULL
  AND p.prix_achat IS NOT NULL
  AND p.prix_achat > 0;

-- 9. Table pour tracer les migrations appliquées
CREATE TABLE IF NOT EXISTS schema_migrations (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO schema_migrations (migration_name)
VALUES ('001_add_movement_cost_tracking')
ON CONFLICT (migration_name) DO NOTHING;
