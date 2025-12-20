-- Synchronisation restaurant -> finance (idempotente)
-- Paramétrage psql :
--   \set restaurant_entity_id 2          -- ID finance_entities pour le restaurant
--   \set restaurant_tenant_id 2          -- tenant_id côté restaurant_*
--   \set restaurant_currency '''EUR'''   -- devises à utiliser pour les écritures
--   \set restaurant_account_type '''BANQUE''' -- type de compte (ENUM finance_account_type)

-- 1) Catégories finance depuis restaurant_depense_categories
INSERT INTO finance_categories (entity_id, name, type, code)
SELECT
    :restaurant_entity_id,
    rdc.nom,
    'EXPENSE',
    'RESTO_' || lower(replace(regexp_replace(rdc.nom, '\s+', '_', 'g'), '''', ''))
FROM restaurant_depense_categories rdc
WHERE NOT EXISTS (
    SELECT 1 FROM finance_categories fc
    WHERE fc.entity_id = :restaurant_entity_id
      AND fc.code = 'RESTO_' || lower(replace(regexp_replace(rdc.nom, '\s+', '_', 'g'), '''', ''))
);

-- 2) Comptes finance depuis restaurant_bank_statements.account (si non présents)
INSERT INTO finance_accounts (
    entity_id, type, label, currency, is_active, created_at, updated_at
)
SELECT DISTINCT
    :restaurant_entity_id,
    cast(:restaurant_account_type AS finance_account_type),
    rbs.account,
    :restaurant_currency,
    TRUE,
    now(),
    now()
FROM restaurant_bank_statements rbs
WHERE rbs.tenant_id = :restaurant_tenant_id
  AND NOT EXISTS (
      SELECT 1 FROM finance_accounts fa
      WHERE fa.entity_id = :restaurant_entity_id
        AND fa.label = rbs.account
  );

-- 3) Transactions finance à partir de restaurant_bank_statements
INSERT INTO finance_transactions (
    entity_id,
    account_id,
    direction,
    source,
    date_operation,
    date_value,
    amount,
    currency,
    ref_externe,
    note,
    status,
    created_at,
    updated_at
)
SELECT
    :restaurant_entity_id,
    fa.id,
    CASE WHEN rbs.montant < 0 THEN 'OUT' ELSE 'IN' END,
    'restaurant',
    rbs.date,
    rbs.date,
    rbs.montant,
    :restaurant_currency,
    CONCAT('RESTO:', rbs.account, ':', rbs.date, ':', md5(coalesce(rbs.libelle, '') || ':' || rbs.montant::text)),
    rbs.libelle,
    'CONFIRMED',
    now(),
    now()
FROM restaurant_bank_statements rbs
JOIN finance_accounts fa
  ON fa.entity_id = :restaurant_entity_id
 AND fa.label = rbs.account
WHERE rbs.tenant_id = :restaurant_tenant_id
  AND NOT EXISTS (
      SELECT 1
      FROM finance_transactions ft
      WHERE ft.ref_externe = CONCAT('RESTO:', rbs.account, ':', rbs.date, ':', md5(coalesce(rbs.libelle, '') || ':' || rbs.montant::text))
  );

-- 4) (Optionnel) Dépenses restaurant -> finance_transactions (si pas de relevés)
--    Montant HT, sens OUT, source 'restaurant_depense'
INSERT INTO finance_transactions (
    entity_id,
    account_id,
    direction,
    source,
    date_operation,
    amount,
    currency,
    ref_externe,
    note,
    status,
    created_at,
    updated_at
)
SELECT
    :restaurant_entity_id,
    -- Assigne au premier compte restaurant existant pour l'entité; ajuster si besoin
    (SELECT id FROM finance_accounts fa WHERE fa.entity_id = :restaurant_entity_id ORDER BY id LIMIT 1),
    'OUT',
    'restaurant_depense',
    rd.date_operation,
    COALESCE(rd.montant_ht, 0),
    :restaurant_currency,
    CONCAT('RESTO_DEP:', rd.id),
    rd.libelle,
    'CONFIRMED',
    now(),
    now()
FROM restaurant_depenses rd
WHERE rd.tenant_id = :restaurant_tenant_id
  AND COALESCE(rd.montant_ht, 0) <> 0
  AND NOT EXISTS (
      SELECT 1 FROM finance_transactions ft WHERE ft.ref_externe = CONCAT('RESTO_DEP:', rd.id)
  );
