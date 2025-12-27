-- Migration: Refactorisation des types de plats en français
-- Date: 2025-01-XX
-- Description:
--   1. Convertit les types de plats anglais en français (dish→plat, beverage→boisson, bundle→formule)
--   2. L'ancien système plat→épicerie (restaurant_epicerie_sku_map) est déprécié
--      Le lien épicerie se fait maintenant via ingredients.produit_epicerie_id

-- ============================================================================
-- 1. MISE À JOUR DES TYPES DE PLATS
-- ============================================================================

-- Convertir 'dish' → 'plat'
UPDATE plats SET type = 'plat' WHERE type = 'dish';

-- Convertir 'beverage' → 'boisson'
UPDATE plats SET type = 'boisson' WHERE type = 'beverage';

-- Convertir 'bundle' → 'formule'
UPDATE plats SET type = 'formule' WHERE type = 'bundle';

-- ============================================================================
-- 2. MISE À JOUR DE LA VALEUR PAR DÉFAUT
-- ============================================================================
-- Note: Cette valeur a déjà été mise à jour dans init.sql, mais on s'assure
-- que la colonne a bien la nouvelle valeur par défaut

ALTER TABLE plats ALTER COLUMN type SET DEFAULT 'plat';

-- ============================================================================
-- 3. DÉPRÉCIATION DE L'ANCIEN SYSTÈME PLAT→ÉPICERIE
-- ============================================================================
-- On ne supprime pas la table restaurant_epicerie_sku_map pour éviter la perte
-- de données historiques, mais on ajoute un commentaire de dépréciation

COMMENT ON TABLE restaurant_epicerie_sku_map IS 'DEPRECATED: Cette table est obsolète. Le lien épicerie se fait maintenant via ingredients.produit_epicerie_id. Ne plus utiliser pour les nouvelles fonctionnalités.';

-- ============================================================================
-- 4. VÉRIFICATION (optionnel - à exécuter manuellement)
-- ============================================================================
-- SELECT type, COUNT(*) FROM plats GROUP BY type;
-- Résultat attendu: plat, boisson, formule (plus de dish, beverage, bundle)
