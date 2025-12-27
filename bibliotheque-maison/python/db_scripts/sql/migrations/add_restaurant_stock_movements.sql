-- Migration: Add restaurant stock movements table
-- Stock restaurant indépendant de l'épicerie avec traçabilité factures

-- Mouvements de stock pour les ingrédients restaurant
CREATE TABLE IF NOT EXISTS restaurant_stock_movements (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 2,
    ingredient_id INT NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    type_mouvement TEXT NOT NULL CHECK (type_mouvement IN ('entree', 'sortie', 'ajustement', 'transfert_epicerie')),
    quantite NUMERIC(14,4) NOT NULL,
    unite TEXT,
    cout_unitaire NUMERIC(12,4),
    cout_total NUMERIC(12,4),
    -- Traçabilité source
    source TEXT, -- 'facture', 'epicerie', 'inventaire', 'consommation', 'perte'
    facture_id INT REFERENCES processed_invoices(id) ON DELETE SET NULL,
    facture_ref TEXT, -- Référence facture pour affichage
    fournisseur TEXT,
    produit_epicerie_id INT REFERENCES produits(id) ON DELETE SET NULL,
    -- Métadonnées
    commentaire TEXT,
    date_mouvement TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_stock_movements_ingredient ON restaurant_stock_movements (tenant_id, ingredient_id, date_mouvement DESC);
CREATE INDEX IF NOT EXISTS idx_restaurant_stock_movements_date ON restaurant_stock_movements (tenant_id, date_mouvement DESC);
CREATE INDEX IF NOT EXISTS idx_restaurant_stock_movements_facture ON restaurant_stock_movements (facture_id) WHERE facture_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_restaurant_stock_movements_source ON restaurant_stock_movements (tenant_id, source, date_mouvement DESC);

-- Vue pour le stock actuel par ingrédient (calculé depuis les mouvements)
CREATE OR REPLACE VIEW v_restaurant_stock_actuel AS
SELECT
    m.tenant_id,
    m.ingredient_id,
    i.nom AS ingredient_nom,
    i.unite_base,
    SUM(CASE WHEN m.type_mouvement IN ('entree', 'transfert_epicerie', 'ajustement') THEN m.quantite ELSE -m.quantite END) AS stock_calcule,
    MAX(m.date_mouvement) AS dernier_mouvement,
    COUNT(*) AS nb_mouvements
FROM restaurant_stock_movements m
JOIN ingredients i ON i.id = m.ingredient_id
GROUP BY m.tenant_id, m.ingredient_id, i.nom, i.unite_base;

SELECT 'Migration restaurant_stock_movements completed successfully';
