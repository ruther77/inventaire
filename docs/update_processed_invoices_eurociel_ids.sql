-- Renumérotation des invoice_id Eurociel au format EUR-XXX (3 lettres fournisseur + numéro séquentiel)
-- Base = max numéro existant parmi les invoice_id déjà au format PREFIX-### (hors Eurociel)

WITH base AS (
  SELECT COALESCE(MAX((regexp_match(invoice_id, '-([0-9]+)$'))[1]::int), 0) AS last_num
  FROM processed_invoices
  WHERE invoice_id ~ '^[A-Z]+-[0-9]+$'
    AND supplier <> 'EUROCIEL'
),
targets AS (
  SELECT id, ROW_NUMBER() OVER (ORDER BY coalesce(facture_date, '9999-12-31'), id) AS rn
  FROM processed_invoices
  WHERE supplier = 'EUROCIEL'
),
updated AS (
  UPDATE processed_invoices pi
  SET invoice_id = 'EUR-' || (b.last_num + t.rn)
  FROM targets t, base b
  WHERE pi.id = t.id
  RETURNING pi.id, pi.invoice_id
)
SELECT COUNT(*) AS updated_rows FROM updated;
