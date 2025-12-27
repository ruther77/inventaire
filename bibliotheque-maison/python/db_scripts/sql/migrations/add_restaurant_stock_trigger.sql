-- Migration: Add trigger to auto-update restaurant_ingredients.stock_actuel
-- This trigger automatically updates the stock when movements are inserted
-- Based on the epicerie trigger pattern (trg_update_stock_actuel)

-- Function to update restaurant ingredient stock based on movements
CREATE OR REPLACE FUNCTION update_restaurant_stock_actuel()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the stock in restaurant_ingredients table
    -- Movement types:
    --   - 'entree': incoming stock (add)
    --   - 'sortie': outgoing stock (subtract)
    --   - 'ajustement': inventory adjustment (add, can be positive or negative via quantite sign)
    --   - 'transfert_epicerie': transfer from epicerie (add)
    UPDATE restaurant_ingredients
    SET stock_actuel = stock_actuel + CASE
        WHEN NEW.type_mouvement IN ('entree', 'transfert_epicerie') THEN NEW.quantite
        WHEN NEW.type_mouvement = 'sortie' THEN -NEW.quantite
        WHEN NEW.type_mouvement = 'ajustement' THEN NEW.quantite
        ELSE 0
    END
    WHERE id = NEW.ingredient_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger that fires after INSERT on restaurant_stock_movements
CREATE OR REPLACE TRIGGER trg_update_restaurant_stock_actuel
AFTER INSERT ON restaurant_stock_movements
FOR EACH ROW
EXECUTE FUNCTION update_restaurant_stock_actuel();

-- Success message
SELECT 'Trigger trg_update_restaurant_stock_actuel created successfully' AS status;
