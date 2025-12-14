-- Trigger de contrôle prix achat/vente non nuls
-- Usage : docker compose --env-file .env exec -T db psql -U postgres -d epicerie < scripts/sql/price_guard.sql
\pset footer off
\pset format unaligned
\pset tuples_only on

CREATE TABLE IF NOT EXISTS import_rejets (
  id bigserial PRIMARY KEY,
  table_name text NOT NULL,
  reason text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE OR REPLACE FUNCTION prevent_zero_price() RETURNS trigger AS $$
BEGIN
  IF NEW.prix_achat IS NULL OR NEW.prix_achat <= 0 OR NEW.prix_vente IS NULL OR NEW.prix_vente <= 0 THEN
    INSERT INTO import_rejets (table_name, reason, payload)
    VALUES (TG_TABLE_NAME, 'PRIX_ZERO', jsonb_build_object('id', NEW.id, 'nom', NEW.nom, 'prix_achat', NEW.prix_achat, 'prix_vente', NEW.prix_vente));
    RAISE EXCEPTION 'Prix achat/vente manquant ou zéro pour %', NEW.nom;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_zero_price_produits ON produits;
CREATE TRIGGER trg_prevent_zero_price_produits
BEFORE INSERT OR UPDATE ON produits
FOR EACH ROW EXECUTE FUNCTION prevent_zero_price();

DROP TRIGGER IF EXISTS trg_prevent_zero_price_stock ON stock_courant;
CREATE TRIGGER trg_prevent_zero_price_stock
BEFORE INSERT OR UPDATE ON stock_courant
FOR EACH ROW EXECUTE FUNCTION prevent_zero_price();

\echo 'Triggers prix zéro installés.'
