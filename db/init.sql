-- ### Types ENUM ###
DO $$ BEGIN
    CREATE TYPE type_mouvement AS ENUM ('ENTREE', 'SORTIE', 'TRANSFERT', 'INVENTAIRE');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- Tenants (gestion multi-tenant)
CREATE TABLE IF NOT EXISTS tenants (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO tenants (id, name, code)
VALUES
    (1, 'Épicerie HQ', 'epicerie'),
    (2, 'Restaurant HQ', 'restaurant')
ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name;

--------------------------------------------------------------------------------
-- 1. TABLES PARTAGÉES (restaurants + éléments restaurant HQ)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS restaurants (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL REFERENCES tenants(id),
    nom TEXT NOT NULL,
    code TEXT UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO restaurants (id, tenant_id, nom, code)
VALUES
    (1, 2, 'Restaurant HQ', 'restaurant')
ON CONFLICT (code) DO UPDATE
SET tenant_id = EXCLUDED.tenant_id, nom = EXCLUDED.nom;

CREATE UNIQUE INDEX IF NOT EXISTS uix_restaurant_nom ON restaurants (tenant_id, nom);

-- Nettoyage: suppression des tables restaurant V1 et des tables jamais utilisées
DROP TABLE IF EXISTS plat_ingredients CASCADE;
DROP TABLE IF EXISTS plat_equivalences CASCADE;
DROP TABLE IF EXISTS plats CASCADE;
DROP TABLE IF EXISTS ingredients CASCADE;
DROP TABLE IF EXISTS bundle_items CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS plat_categories CASCADE;
DROP TABLE IF EXISTS ingredient_conditionnements CASCADE;
DROP TABLE IF EXISTS stock_emplacements CASCADE;
DROP TABLE IF EXISTS stock_mouvements CASCADE;
DROP TABLE IF EXISTS productions CASCADE;
DROP TABLE IF EXISTS production_lots CASCADE;

--------------------------------------------------------------------------------
-- 2. TABLES (avec Contraintes d'Intégrité)
--------------------------------------------------------------------------------

-- Table produits (Mise à jour)
CREATE TABLE IF NOT EXISTS produits (
    id SERIAL PRIMARY KEY,
    nom TEXT NOT NULL,
    tenant_id INT NOT NULL DEFAULT 1,
    categorie TEXT DEFAULT 'Autre',
    -- Ajout de contraintes CHECK pour garantir des valeurs non-négatives
    prix_achat NUMERIC(10,2) CHECK (prix_achat >= 0),
    prix_vente NUMERIC(10,2) CHECK (prix_vente >= 0),
    tva NUMERIC(5,2) DEFAULT 0 CHECK (tva >= 0),
    seuil_alerte NUMERIC(12,3) DEFAULT 0 CHECK (seuil_alerte >= 0),
    actif BOOLEAN DEFAULT TRUE,
    -- NOUVEAU: Stock Actuel matérialisé
    stock_actuel NUMERIC(12,3) DEFAULT 0 CHECK (stock_actuel >= 0), 
    -- Ajout de dates de création/mise à jour
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);
-- ... (Le reste de vos tables: mouvements_stock, produits_barcodes, etc.)
-- Codes-barres (1 produit -> N codes)
CREATE TABLE IF NOT EXISTS produits_barcodes (
    id SERIAL PRIMARY KEY,
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    tenant_id INT NOT NULL DEFAULT 1,
    code TEXT NOT NULL,
    symbologie TEXT,            -- EAN-13, UPC-A, EAN-8, CODE128…
    pays_iso2 CHAR(2),
    is_principal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Mouvements
CREATE TABLE IF NOT EXISTS mouvements_stock (
    id SERIAL PRIMARY KEY,
    produit_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    tenant_id INT NOT NULL DEFAULT 1,
    type type_mouvement NOT NULL,
    -- La quantité est toujours positive (ex: une 'SORTIE' a une quantite positive)
    quantite NUMERIC(12,3) NOT NULL CHECK (quantite > 0),
    source TEXT,                -- Ex: Nom du fournisseur, Numéro de commande, Nom de l'utilisateur
    date_mvt TIMESTAMP NOT NULL DEFAULT now(),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

-- Utilisateurs applicatifs
CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'standard',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. FONCTION DE MISE À JOUR DU STOCK (Trigger)
-- =================================================================
CREATE OR REPLACE FUNCTION update_stock_actuel()
RETURNS TRIGGER AS $$
BEGIN
    -- Mettre à jour le stock dans la table produits
    UPDATE produits
    SET stock_actuel = stock_actuel + CASE
        WHEN NEW.type = 'ENTREE' THEN NEW.quantite
        WHEN NEW.type = 'SORTIE' THEN -NEW.quantite
        -- Ajoutez ici d'autres types si nécessaire (ex: INVENTAIRE, TRANSFERT)
        ELSE 0
    END
    WHERE id = NEW.produit_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- 4. TRIGGER
-- =================================================================
-- S'exécute APRÈS chaque INSERTION dans mouvements_stock
CREATE OR REPLACE TRIGGER trg_update_stock_actuel
AFTER INSERT ON mouvements_stock
FOR EACH ROW
EXECUTE FUNCTION update_stock_actuel();


-- 5. NETTOYAGE DES ANCIENNES VUES (Optionnel)
-- =================================================================
-- La vue v_stock_courant n'est plus utile, remplacez-la ou supprimez-la.
-- La vue v_stock_produits doit être réécrite pour utiliser 'stock_actuel'.
CREATE OR REPLACE VIEW v_stock_produits AS
SELECT 
    p.id, 
    p.nom, 
    p.categorie,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.stock_actuel AS quantite_stock -- Utilise la nouvelle colonne O(1)
FROM produits p
WHERE p.actif = TRUE;

-- Mise à jour de la vue v_alertes_rupture pour utiliser la colonne O(1)
CREATE OR REPLACE VIEW v_alertes_rupture AS
SELECT
    p.id, p.nom, COALESCE(p.categorie::text, 'Non renseignée') AS categorie, p.stock_actuel as stock, p.seuil_alerte
FROM produits p
WHERE p.stock_actuel <= COALESCE(p.seuil_alerte, 0)
AND p.actif = TRUE
ORDER BY p.stock_actuel ASC;
--------------------------------------------------------------------------------
-- 4. INDEXES & CONTRAINTES UNIQUES
--------------------------------------------------------------------------------

-- Configuration du search_path (maintenue pour compatibilité)
DO $$ BEGIN
    EXECUTE 'ALTER ROLE ' || current_user || ' IN DATABASE ' || current_database() || ' SET search_path TO public';
EXCEPTION WHEN others THEN
    NULL;
END $$;

-- Rendre le nom du produit unique, non sensible à la casse (Case-Insensitive Unique Index)
-- UTILE pour l'import (cf. products_loader.py)
CREATE UNIQUE INDEX IF NOT EXISTS uix_produits_nom_ci ON public.produits (LOWER(nom));

-- Rendre le code-barres unique, non sensible à la casse
CREATE UNIQUE INDEX IF NOT EXISTS uix_barcodes_code_ci ON public.produits_barcodes (LOWER(code));

-- Index pour les recherches fréquentes
CREATE INDEX IF NOT EXISTS idx_barcode_produit ON produits_barcodes(produit_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_produit ON mouvements_stock(produit_id);
CREATE INDEX IF NOT EXISTS idx_mouvements_date ON mouvements_stock(date_mvt);

--------------------------------------------------------------------------------
-- 5. VUES COHÉRENTES ET FONCTIONNELLES
--------------------------------------------------------------------------------

-- VUE DU STOCK COURANT (Méthode 1: Solde Net basé sur l'historique)
CREATE OR REPLACE VIEW v_stock_courant AS
SELECT
    p.id,
    p.nom,
    p.categorie,
    p.prix_achat,
    p.prix_vente,
    p.tva,
    p.seuil_alerte,
    p.actif,
    -- Logique de calcul du solde
    COALESCE(SUM(
        CASE
            WHEN m.type IN ('ENTREE', 'INVENTAIRE', 'TRANSFERT') THEN m.quantite -- NOTE: voir explication ci-dessous
            WHEN m.type = 'SORTIE' THEN -m.quantite
            ELSE 0
        END
    ), 0) AS stock
FROM produits p
LEFT JOIN mouvements_stock m ON m.produit_id = p.id
GROUP BY
    p.id, p.nom, p.categorie, p.prix_achat, p.prix_vente, p.tva, p.seuil_alerte, p.actif
ORDER BY p.nom;

/*
EXPLICATION DU TYPE INVENTAIRE DANS v_stock_courant:
- Si un INVENTAIRE est un 'réglage' qui s'ajoute (ou se soustrait), il doit être traité comme ENTREE ou SORTIE.
- Si un INVENTAIRE (ou un mouvement dit d' 'AJUSTEMENT') est utilisé, il est souvent préférable de le considérer comme une ENTREE.
- Dans le modèle simple (stock net), tout INVENTAIRE est une ENTREE. Un ajustement à la baisse se fait par une SORTIE (type = 'SORTIE', source='Ajustement Inventaire'). Un ajustement à la hausse par une ENTREE (type = 'ENTREE', source='Ajustement Inventaire').
- Ici, on considère 'INVENTAIRE' comme un type d'ENTRÉE.
*/

-- Produits + codes agrégés (maintenu et enrichi)
CREATE OR REPLACE VIEW v_produits_codes AS
SELECT
    p.id, p.nom, p.categorie,
    p.prix_achat, p.prix_vente, p.tva, p.actif,
    COALESCE(string_agg(pb.code, ', ' ORDER BY pb.is_principal DESC, pb.code), '') AS codes
FROM produits p
LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id
GROUP BY p.id, p.nom, p.categorie, p.prix_achat, p.prix_vente, p.tva, p.actif
ORDER BY p.nom;

-- Valorisation du stock (utilise v_stock_courant)
CREATE OR REPLACE VIEW v_valorisation_stock AS
SELECT
    s.id, s.nom, s.categorie, s.stock,
    s.prix_achat,
    -- Utilisation de s.prix_achat qui provient déjà de la vue mère
    ROUND(s.stock * COALESCE(s.prix_achat, 0), 2) AS valeur_achat
FROM v_stock_courant s
WHERE s.stock > 0
ORDER BY valeur_achat DESC;

--------------------------------------------------------------------------------
-- 6. TABLES CAPITAL & VUES PRIX POUR LE PORTEFEUILLE
--------------------------------------------------------------------------------

-- Drop explicite pour éviter les conflits d'ordre de colonnes lors du REPLACE
DROP VIEW IF EXISTS latest_price_history;

CREATE TABLE IF NOT EXISTS capital_snapshot (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    snapshot_date TIMESTAMPTZ NOT NULL,
    stock_value NUMERIC(14,2) NOT NULL DEFAULT 0,
    bank_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    cash_balance NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_assets NUMERIC(14,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_capital_snapshot_tenant_date ON capital_snapshot (tenant_id, snapshot_date);

CREATE OR REPLACE VIEW latest_price_history AS
SELECT
    code,
    tenant_id,
    fournisseur,
    prix_achat,
    quantite,
    facture_date,
    source_context,
    created_at
FROM (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY tenant_id, code
               ORDER BY facture_date DESC NULLS LAST, created_at DESC
           ) AS row_num
    FROM produits_price_history
) ranked
WHERE row_num = 1;

--------------------------------------------------------------------------------
-- 6. TABLES D'AUDIT (assignations & journal)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS processed_invoices (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    invoice_id TEXT NOT NULL,
    supplier TEXT,
    facture_date TEXT,
    line_count INT NOT NULL DEFAULT 0,
    file_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, invoice_id)
);

CREATE INDEX IF NOT EXISTS idx_processed_invoices_tenant ON processed_invoices (tenant_id);

CREATE TABLE IF NOT EXISTS audit_actions (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    tenant_id INT NOT NULL DEFAULT 1,
    responsable TEXT NOT NULL,
    note TEXT,
    status TEXT NOT NULL DEFAULT 'A investiguer',
    due_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_actions_product ON audit_actions(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_actions_status ON audit_actions(status);

CREATE TABLE IF NOT EXISTS audit_resolution_log (
    id SERIAL PRIMARY KEY,
    action_id INT REFERENCES audit_actions(id) ON DELETE CASCADE,
    product_id INT NOT NULL REFERENCES produits(id) ON DELETE CASCADE,
    tenant_id INT NOT NULL DEFAULT 1,
    statut TEXT NOT NULL,
    note TEXT,
    responsable TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_product ON audit_resolution_log(product_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_resolution_log(action_id);

--------------------------------------------------------------------------------
-- 7. RESTAURANT TABLES
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS restaurant_depense_categories (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    nom TEXT NOT NULL,
    UNIQUE (tenant_id, nom)
);

CREATE TABLE IF NOT EXISTS restaurant_cost_centers (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    nom TEXT NOT NULL,
    UNIQUE (tenant_id, nom)
);

CREATE TABLE IF NOT EXISTS restaurant_fournisseurs (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    nom TEXT NOT NULL,
    iban TEXT,
    siret TEXT,
    UNIQUE (tenant_id, nom)
);

CREATE TABLE IF NOT EXISTS restaurant_depenses (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    categorie_id INT REFERENCES restaurant_depense_categories(id) ON DELETE SET NULL,
    fournisseur_id INT REFERENCES restaurant_fournisseurs(id) ON DELETE SET NULL,
    cost_center_id INT REFERENCES restaurant_cost_centers(id) ON DELETE SET NULL,
    libelle TEXT NOT NULL,
    unite TEXT,
    quantite NUMERIC(14,4),
    prix_unitaire NUMERIC(12,4),
    montant_ht NUMERIC(12,2),
    tva_pct NUMERIC(5,2) DEFAULT 20.00,
    date_operation DATE NOT NULL DEFAULT CURRENT_DATE,
    source TEXT,
    ref_externe TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS restaurant_ingredients (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    nom TEXT NOT NULL,
    unite_base TEXT NOT NULL DEFAULT 'kg',
    cout_unitaire NUMERIC(12,4) DEFAULT 0,
    stock_actuel NUMERIC(14,4) DEFAULT 0,
    stock_min NUMERIC(14,4) DEFAULT 0,
    categorie TEXT,
    fournisseur TEXT,
    produit_epicerie_id INT REFERENCES produits(id) ON DELETE SET NULL,
    ratio_epicerie NUMERIC(12,4) DEFAULT 1.0,
    UNIQUE (tenant_id, nom)
);

CREATE TABLE IF NOT EXISTS restaurant_plats (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    restaurant_id INT NOT NULL DEFAULT 1 REFERENCES restaurants(id) ON DELETE CASCADE,
    nom TEXT NOT NULL,
    categorie TEXT,
    prix_vente_ttc NUMERIC(12,2) DEFAULT 0,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (tenant_id, nom)
);

CREATE TABLE IF NOT EXISTS restaurant_plat_ingredients (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    plat_id INT NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    ingredient_id INT NOT NULL REFERENCES restaurant_ingredients(id) ON DELETE CASCADE,
    quantite NUMERIC(14,4) NOT NULL,
    unite TEXT,
    UNIQUE (plat_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS restaurant_sales (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    plat_id INT NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    quantity NUMERIC(12,4) NOT NULL,
    sold_at TIMESTAMPTZ NOT NULL,
    source TEXT,
    source_ref TEXT,
    row_hash VARCHAR(40),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_restaurant_sales_row_hash
ON restaurant_sales (tenant_id, row_hash) WHERE row_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_restaurant_sales_tenant_sold_at
ON restaurant_sales (tenant_id, sold_at DESC);

CREATE INDEX IF NOT EXISTS idx_restaurant_sales_plat_sold_at
ON restaurant_sales (plat_id, sold_at DESC);

CREATE TABLE IF NOT EXISTS restaurant_ingredient_price_history (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    ingredient_id INT NOT NULL REFERENCES restaurant_ingredients(id) ON DELETE CASCADE,
    cout_unitaire NUMERIC(12,4) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_ingredient_price_history_ingredient ON restaurant_ingredient_price_history (tenant_id, ingredient_id, changed_at DESC);

CREATE TABLE IF NOT EXISTS restaurant_plat_price_history (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    plat_id INT NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    prix_vente_ttc NUMERIC(12,4) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_plat_price_history_plat ON restaurant_plat_price_history (tenant_id, plat_id, changed_at DESC);

-- Coûts plats matérialisés
CREATE TABLE IF NOT EXISTS restaurant_plat_costs (
    tenant_id INT NOT NULL,
    plat_id INT NOT NULL REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    cout_matiere NUMERIC(14,4) NOT NULL DEFAULT 0,
    prix_vente_ttc NUMERIC(14,4) NOT NULL DEFAULT 0,
    marge_brute NUMERIC(14,4) NOT NULL DEFAULT 0,
    marge_pct NUMERIC(8,3) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, plat_id)
);

-- Alertes restaurant (marges, etc.)
CREATE TABLE IF NOT EXISTS restaurant_alerts (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL,
    plat_id INT REFERENCES restaurant_plats(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    current_value NUMERIC(14,4),
    threshold NUMERIC(14,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_alerts_tenant_type ON restaurant_alerts (tenant_id, alert_type);

-- Table de mapping entre produits restaurant et produits épicerie
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

-- ============================================================================
-- STOCK RESTAURANT (indépendant de l'épicerie)
-- ============================================================================

-- Mouvements de stock pour les ingrédients restaurant
CREATE TABLE IF NOT EXISTS restaurant_stock_movements (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 1,
    ingredient_id INT NOT NULL REFERENCES restaurant_ingredients(id) ON DELETE CASCADE,
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
    ri.nom AS ingredient_nom,
    ri.unite_base,
    SUM(CASE WHEN m.type_mouvement IN ('entree', 'transfert_epicerie', 'ajustement') THEN m.quantite ELSE -m.quantite END) AS stock_calcule,
    MAX(m.date_mouvement) AS dernier_mouvement,
    COUNT(*) AS nb_mouvements
FROM restaurant_stock_movements m
JOIN restaurant_ingredients ri ON ri.id = m.ingredient_id
GROUP BY m.tenant_id, m.ingredient_id, ri.nom, ri.unite_base;

CREATE TABLE IF NOT EXISTS restaurant_bank_statements (
    id SERIAL PRIMARY KEY,
    tenant_id INT NOT NULL DEFAULT 2,
    account TEXT NOT NULL,
    date DATE NOT NULL,
    libelle TEXT NOT NULL,
    categorie TEXT,
    montant NUMERIC(12,2) NOT NULL,
    type TEXT NOT NULL,
    mois TEXT NOT NULL,
    source TEXT,
    depense_id INT REFERENCES restaurant_depenses(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_restaurant_bank_statements_tenant_account ON restaurant_bank_statements (tenant_id, account);
CREATE UNIQUE INDEX IF NOT EXISTS uq_restaurant_bank_statements_entry
    ON restaurant_bank_statements (tenant_id, account, date, (md5(libelle)), montant);

CREATE OR REPLACE FUNCTION trg_restaurant_bank_statements_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS restaurant_bank_statements_updated_at_trigger ON restaurant_bank_statements;
CREATE TRIGGER restaurant_bank_statements_updated_at_trigger
BEFORE UPDATE ON restaurant_bank_statements
FOR EACH ROW EXECUTE FUNCTION trg_restaurant_bank_statements_updated_at();

--------------------------------------------------------------------------------
-- Triggers d’historique des prix
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION trg_restaurant_ingredient_price_history()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.cout_unitaire IS DISTINCT FROM OLD.cout_unitaire) THEN
        INSERT INTO restaurant_ingredient_price_history (tenant_id, ingredient_id, cout_unitaire)
        VALUES (NEW.tenant_id, NEW.id, NEW.cout_unitaire);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS restaurant_ingredient_price_history_trigger ON restaurant_ingredients;
CREATE TRIGGER restaurant_ingredient_price_history_trigger
AFTER INSERT OR UPDATE ON restaurant_ingredients
FOR EACH ROW EXECUTE FUNCTION trg_restaurant_ingredient_price_history();

CREATE OR REPLACE FUNCTION trg_restaurant_plat_price_history()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR (TG_OP = 'UPDATE' AND NEW.prix_vente_ttc IS DISTINCT FROM OLD.prix_vente_ttc) THEN
        INSERT INTO restaurant_plat_price_history (tenant_id, plat_id, prix_vente_ttc)
        VALUES (NEW.tenant_id, NEW.id, NEW.prix_vente_ttc);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS restaurant_plat_price_history_trigger ON restaurant_plats;
CREATE TRIGGER restaurant_plat_price_history_trigger
AFTER INSERT OR UPDATE ON restaurant_plats
FOR EACH ROW EXECUTE FUNCTION trg_restaurant_plat_price_history();

-- Centres de coûts (Epicerie HQ)
INSERT INTO restaurant_cost_centers (tenant_id, nom)
VALUES
    (1, 'Approvisionnement/Achats'),
    (1, 'Encaissement/Commissions'),
    (1, 'Banque'),
    (1, 'Assurance'),
    (1, 'Énergie'),
    (1, 'Abonnements/IT'),
    (1, 'Paie/Charges sociales'),
    (1, 'Fiscalité/URSSAF'),
    (1, 'Loyer')
ON CONFLICT (tenant_id, nom) DO NOTHING;

-- Affectation automatique des centres de coûts (Epicerie HQ)
-- Ne met à jour que les dépenses sans cost_center_id et avec categorie_id connue
DO $$
DECLARE
    cc_id INT;
BEGIN
    -- Approvisionnement
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Approvisionnement/Achats';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Approvisionnement', 'Fournisseur', 'Boissons')
          );
    END IF;

    -- Encaissement/Commissions
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Encaissement/Commissions';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Frais d''encaissement', 'Plateformes / Commissions')
          );
    END IF;

    -- Banque
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Banque';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Frais bancaires')
          );
    END IF;

    -- Assurance
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Assurance';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Assurance')
          );
    END IF;

    -- Énergie
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Énergie';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Énergie', 'Gaz', 'Eau')
          );
    END IF;

    -- Abonnements/IT
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Abonnements/IT';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Abonnements', 'Abonnements TV', 'Télécom', 'SaaS / Informatique')
          );
    END IF;

    -- Paie/Charges sociales
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Paie/Charges sociales';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Salaires', 'Charges sociales', 'Retraite / Prévoyance')
          );
    END IF;

    -- Fiscalité/URSSAF
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Fiscalité/URSSAF';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Fiscalité', 'Impôts et taxes')
          );
    END IF;

    -- Loyer
    SELECT id INTO cc_id FROM restaurant_cost_centers WHERE tenant_id = 1 AND nom = 'Loyer';
    IF cc_id IS NOT NULL THEN
        UPDATE restaurant_depenses
        SET cost_center_id = cc_id
        WHERE tenant_id = 1 AND cost_center_id IS NULL
          AND categorie_id IN (
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = 1 AND nom IN ('Loyer/Location')
          );
    END IF;
END$$;

-- Top ventes 30 jours (maintenu)
CREATE OR REPLACE VIEW v_top_ventes_30j AS
SELECT p.id, p.nom,
    SUM(CASE WHEN m.type='SORTIE' THEN m.quantite ELSE 0 END) AS qte_sorties_30j
FROM produits p
LEFT JOIN mouvements_stock m
    ON m.produit_id = p.id
    AND m.date_mvt >= now() - INTERVAL '30 days'
GROUP BY p.id, p.nom
ORDER BY qte_sorties_30j DESC NULLS LAST;

-- Rotation 30 jours (maintenu)
CREATE OR REPLACE VIEW v_rotation_30j AS
SELECT p.id, p.nom,
    SUM(CASE WHEN m.type='ENTREE' THEN m.quantite ELSE 0 END) AS entrees_30j,
    SUM(CASE WHEN m.type='SORTIE' THEN m.quantite ELSE 0 END) AS sorties_30j
FROM produits p
LEFT JOIN mouvements_stock m
    ON m.produit_id = p.id
    AND m.date_mvt >= now() - INTERVAL '30 days'
GROUP BY p.id, p.nom
ORDER BY sorties_30j DESC NULLS LAST;

-- Anomalies : stock négatif (utilise v_stock_courant)
CREATE OR REPLACE VIEW v_inventaire_negatif AS
SELECT * FROM v_stock_courant WHERE stock < 0 ORDER BY stock ASC;

-- Produits sans code-barres (maintenu)
CREATE OR REPLACE VIEW v_produits_sans_barcode AS
SELECT p.*
FROM produits p
LEFT JOIN produits_barcodes pb ON pb.produit_id = p.id
WHERE pb.id IS NULL
ORDER BY p.nom;

-- Alertes de rupture (utilise v_stock_courant)
CREATE OR REPLACE VIEW v_alertes_rupture AS
SELECT
    s.id, s.nom, s.categorie, (s.stock)::numeric(12,3) as stock, s.seuil_alerte
FROM v_stock_courant s
WHERE (s.stock)::numeric(12,3) <= COALESCE(s.seuil_alerte, 0)
AND s.actif = TRUE
ORDER BY (s.stock)::numeric(12,3) ASC;

-- Mouvements récents (enrichi avec catégorie)
CREATE OR REPLACE VIEW v_mouvements_recents AS
SELECT
    m.id, m.date_mvt, m.type, m.quantite, m.source,
    p.id AS produit_id, p.nom, p.categorie
FROM mouvements_stock m
JOIN produits p ON p.id = m.produit_id
ORDER BY m.date_mvt DESC
LIMIT 500;

-- Alias de compatibilité (maintenu)
CREATE OR REPLACE VIEW stock_courant AS SELECT * FROM v_stock_courant;
CREATE OR REPLACE VIEW v_prod_barcodes AS SELECT * FROM v_produits_codes;
