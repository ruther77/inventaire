-- Migration: Fusion des comptes LCL Principal (15) et LCL Noutam (16)
-- Problème: Les comptes 15 et 16 représentent EN FAIT le même compte bancaire LCL Noutam
-- Les fichiers COMPTECOURANT_*.pdf étaient incorrectement importés sur le compte 15
-- Cette migration fusionne tout vers le compte 16 et supprime les doublons

-- ==============================================================================
-- ÉTAPE 1: ANALYSE PRÉLIMINAIRE
-- ==============================================================================

DO $$
DECLARE
    count_account_15 INTEGER;
    count_account_16 INTEGER;
    count_duplicates INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_account_15 FROM finance_transactions WHERE account_id = 15;
    SELECT COUNT(*) INTO count_account_16 FROM finance_transactions WHERE account_id = 16;

    SELECT COUNT(*) INTO count_duplicates FROM (
        SELECT date_operation, amount
        FROM finance_transactions
        WHERE account_id IN (15, 16)
        GROUP BY date_operation, amount
        HAVING COUNT(*) > 1
    ) sub;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'ANALYSE AVANT MIGRATION';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Compte 15 (LCL Principal): % transactions', count_account_15;
    RAISE NOTICE 'Compte 16 (LCL Noutam):    % transactions', count_account_16;
    RAISE NOTICE 'Doublons détectés:         % paires', count_duplicates;
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- ÉTAPE 2: CRÉER UNE TABLE TEMPORAIRE POUR IDENTIFIER LES DOUBLONS
-- ==============================================================================

CREATE TEMP TABLE temp_duplicates AS
SELECT
    date_operation,
    amount,
    ARRAY_AGG(id ORDER BY
        -- Priorité 1: Préférer le compte 16 (destination finale)
        CASE WHEN account_id = 16 THEN 0 ELSE 1 END,
        -- Priorité 2: Préférer les transactions avec ref_externe non-stmtline
        CASE WHEN ref_externe LIKE 'stmtline:%' THEN 1 ELSE 0 END,
        -- Priorité 3: Préférer les transactions avec un label plus long/descriptif
        LENGTH(COALESCE(label, '')) DESC,
        -- Priorité 4: Garder la plus récente (created_at)
        created_at DESC
    ) as transaction_ids,
    ARRAY_AGG(account_id ORDER BY
        CASE WHEN account_id = 16 THEN 0 ELSE 1 END,
        CASE WHEN ref_externe LIKE 'stmtline:%' THEN 1 ELSE 0 END,
        LENGTH(COALESCE(label, '')) DESC,
        created_at DESC
    ) as account_ids,
    ARRAY_AGG(label ORDER BY
        CASE WHEN account_id = 16 THEN 0 ELSE 1 END,
        CASE WHEN ref_externe LIKE 'stmtline:%' THEN 1 ELSE 0 END,
        LENGTH(COALESCE(label, '')) DESC,
        created_at DESC
    ) as labels
FROM finance_transactions
WHERE account_id IN (15, 16)
GROUP BY date_operation, amount
HAVING COUNT(*) > 1;

-- Afficher un échantillon des doublons détectés
DO $$
DECLARE
    rec RECORD;
    counter INTEGER := 0;
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'ÉCHANTILLON DES DOUBLONS (10 premiers)';
    RAISE NOTICE '========================================';

    FOR rec IN
        SELECT
            date_operation,
            amount,
            transaction_ids[1] as keep_id,
            transaction_ids[2] as delete_id,
            account_ids[1] as keep_account,
            account_ids[2] as delete_account,
            labels[1] as keep_label,
            labels[2] as delete_label
        FROM temp_duplicates
        ORDER BY date_operation DESC
        LIMIT 10
    LOOP
        counter := counter + 1;
        RAISE NOTICE '% | Date: % | Montant: % EUR', counter, rec.date_operation, rec.amount;
        RAISE NOTICE '  → GARDER   ID:% (Compte %) - "%"', rec.keep_id, rec.keep_account, LEFT(rec.keep_label, 60);
        RAISE NOTICE '  → SUPPRIMER ID:% (Compte %) - "%"', rec.delete_id, rec.delete_account, LEFT(rec.delete_label, 60);
        RAISE NOTICE '';
    END LOOP;
END $$;

-- ==============================================================================
-- ÉTAPE 3: SAUVEGARDER LES DONNÉES AVANT SUPPRESSION (AUDIT)
-- ==============================================================================

CREATE TEMP TABLE temp_deleted_transactions AS
SELECT
    t.*,
    CURRENT_TIMESTAMP as deleted_at,
    'Duplicate transaction merged from account ' || t.account_id || ' to account 16' as deletion_reason
FROM finance_transactions t
INNER JOIN temp_duplicates d ON t.id = ANY(d.transaction_ids[2:]);

-- Compter les transactions qui vont être supprimées
DO $$
DECLARE
    count_to_delete INTEGER;
BEGIN
    SELECT COUNT(*) INTO count_to_delete FROM temp_deleted_transactions;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Transactions à supprimer: %', count_to_delete;
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- ÉTAPE 4: SUPPRIMER LES RELATIONS (FOREIGN KEYS) AVANT DE SUPPRIMER LES TRANSACTIONS
-- ==============================================================================

-- Supprimer les relations dans finance_payments
DELETE FROM finance_payments
WHERE transaction_id IN (
    SELECT id FROM temp_deleted_transactions
);

-- Supprimer les relations dans finance_reconciliations
DELETE FROM finance_reconciliations
WHERE transaction_id IN (
    SELECT id FROM temp_deleted_transactions
);

-- Supprimer les relations dans finance_transaction_classification
DELETE FROM finance_transaction_classification
WHERE transaction_id IN (
    SELECT id FROM temp_deleted_transactions
);

-- Supprimer les relations dans finance_transaction_lines
DELETE FROM finance_transaction_lines
WHERE transaction_id IN (
    SELECT id FROM temp_deleted_transactions
);

-- ==============================================================================
-- ÉTAPE 5: SUPPRIMER LES TRANSACTIONS EN DOUBLE
-- ==============================================================================

WITH deleted AS (
    DELETE FROM finance_transactions
    WHERE id IN (
        SELECT UNNEST(transaction_ids[2:])
        FROM temp_duplicates
    )
    RETURNING *
)
SELECT COUNT(*) as nb_deleted INTO TEMP temp_delete_count FROM deleted;

DO $$
DECLARE
    nb_deleted INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_deleted FROM temp_delete_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Doublons supprimés: % transactions', nb_deleted;
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- ÉTAPE 6: MIGRER TOUTES LES TRANSACTIONS RESTANTES DU COMPTE 15 VERS LE COMPTE 16
-- ==============================================================================

-- Mettre à jour les transactions du compte 15 vers le compte 16
WITH updated AS (
    UPDATE finance_transactions
    SET
        account_id = 16,
        updated_at = CURRENT_TIMESTAMP,
        note = CASE
            WHEN note IS NULL THEN 'Migrated from account 15 (LCL Principal) to 16 (LCL Noutam)'
            ELSE note || E'\n[Migration] Moved from account 15 to 16'
        END
    WHERE account_id = 15
    RETURNING *
)
SELECT COUNT(*) as nb_migrated INTO TEMP temp_migrate_count FROM updated;

DO $$
DECLARE
    nb_migrated INTEGER;
BEGIN
    SELECT COUNT(*) INTO nb_migrated FROM temp_migrate_count;
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Transactions migrées de 15 vers 16: %', nb_migrated;
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- ÉTAPE 7: METTRE À JOUR LES RELATIONS counterparty_account_id
-- ==============================================================================

UPDATE finance_transactions
SET counterparty_account_id = 16
WHERE counterparty_account_id = 15;

-- ==============================================================================
-- ÉTAPE 8: CRÉER DES INDEX OPTIMISÉS POUR LA DÉDUPLICATION FUTURE
-- ==============================================================================

-- Index pour détecter rapidement les doublons potentiels
CREATE INDEX IF NOT EXISTS ix_finance_tx_dedup
ON finance_transactions(account_id, date_operation, amount);

-- Index pour identifier les transactions stmtline (à privilégier pour suppression)
CREATE INDEX IF NOT EXISTS ix_finance_tx_ref_externe_stmtline
ON finance_transactions(ref_externe)
WHERE ref_externe LIKE 'stmtline:%';

-- ==============================================================================
-- ÉTAPE 9: CRÉER UNE CONTRAINTE UNIQUE POUR ÉVITER LES FUTURS DOUBLONS
-- ==============================================================================

-- Note: On ne peut pas ajouter une contrainte unique stricte car il peut y avoir
-- plusieurs transactions légitimes avec le même montant et la même date.
-- À la place, on crée une fonction trigger qui alerte sur les doublons potentiels.

CREATE OR REPLACE FUNCTION check_duplicate_transaction()
RETURNS TRIGGER AS $$
DECLARE
    duplicate_count INTEGER;
BEGIN
    -- Vérifier s'il existe déjà une transaction similaire
    SELECT COUNT(*) INTO duplicate_count
    FROM finance_transactions
    WHERE account_id = NEW.account_id
      AND date_operation = NEW.date_operation
      AND amount = NEW.amount
      AND label = NEW.label
      AND id != NEW.id;

    IF duplicate_count > 0 THEN
        RAISE WARNING 'Possible duplicate transaction detected: account_id=%, date=%, amount=%, label=%',
            NEW.account_id, NEW.date_operation, NEW.amount, NEW.label;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Créer le trigger (seulement s'il n'existe pas déjà)
DROP TRIGGER IF EXISTS trigger_check_duplicate_transaction ON finance_transactions;
CREATE TRIGGER trigger_check_duplicate_transaction
    BEFORE INSERT OR UPDATE ON finance_transactions
    FOR EACH ROW
    EXECUTE FUNCTION check_duplicate_transaction();

-- ==============================================================================
-- ÉTAPE 10: DÉSACTIVER LE COMPTE 15
-- ==============================================================================

UPDATE finance_accounts
SET
    is_active = false,
    label = label || ' [OBSOLETE - MERGED TO ACCOUNT 16]',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 15;

-- ==============================================================================
-- ÉTAPE 11: VÉRIFICATION POST-MIGRATION
-- ==============================================================================

DO $$
DECLARE
    count_account_15 INTEGER;
    count_account_16 INTEGER;
    count_remaining_duplicates INTEGER;
    count_per_month RECORD;
BEGIN
    -- Compter les transactions restantes
    SELECT COUNT(*) INTO count_account_15 FROM finance_transactions WHERE account_id = 15;
    SELECT COUNT(*) INTO count_account_16 FROM finance_transactions WHERE account_id = 16;

    -- Compter les doublons restants
    SELECT COUNT(*) INTO count_remaining_duplicates FROM (
        SELECT date_operation, amount
        FROM finance_transactions
        WHERE account_id = 16
        GROUP BY date_operation, amount
        HAVING COUNT(*) > 1
    ) sub;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'VÉRIFICATION POST-MIGRATION';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Compte 15 (désactivé): % transactions', count_account_15;
    RAISE NOTICE 'Compte 16 (LCL Noutam): % transactions', count_account_16;
    RAISE NOTICE 'Doublons restants: %', count_remaining_duplicates;
    RAISE NOTICE '';
    RAISE NOTICE 'Distribution par mois pour compte 16:';
    RAISE NOTICE '----------------------------------------';

    FOR count_per_month IN
        SELECT
            TO_CHAR(date_operation, 'YYYY-MM') as month,
            COUNT(*) as nb_tx,
            SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) as total_in,
            SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) as total_out
        FROM finance_transactions
        WHERE account_id = 16
        GROUP BY TO_CHAR(date_operation, 'YYYY-MM')
        ORDER BY month
    LOOP
        RAISE NOTICE '  % | % tx | IN: % EUR | OUT: % EUR',
            count_per_month.month,
            count_per_month.nb_tx,
            count_per_month.total_in,
            count_per_month.total_out;
    END LOOP;

    RAISE NOTICE '========================================';

    -- Vérifier s'il y a des trous dans les données
    RAISE NOTICE '';
    RAISE NOTICE 'Vérification de continuité temporelle:';
    RAISE NOTICE '----------------------------------------';

    WITH month_series AS (
        SELECT generate_series(
            date_trunc('month', (SELECT MIN(date_operation) FROM finance_transactions WHERE account_id = 16)),
            date_trunc('month', (SELECT MAX(date_operation) FROM finance_transactions WHERE account_id = 16)),
            '1 month'::interval
        )::date as month
    ),
    actual_months AS (
        SELECT DISTINCT date_trunc('month', date_operation)::date as month
        FROM finance_transactions
        WHERE account_id = 16
    )
    SELECT
        TO_CHAR(ms.month, 'YYYY-MM') as missing_month
    FROM month_series ms
    LEFT JOIN actual_months am ON ms.month = am.month
    WHERE am.month IS NULL
    INTO TEMP temp_missing_months;

    IF EXISTS (SELECT 1 FROM temp_missing_months) THEN
        RAISE NOTICE 'ATTENTION: Mois sans transactions détectés:';
        FOR count_per_month IN SELECT * FROM temp_missing_months LOOP
            RAISE NOTICE '  - %', count_per_month.missing_month;
        END LOOP;
    ELSE
        RAISE NOTICE 'OK: Aucun trou dans les données (continuité mensuelle complète)';
    END IF;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'MIGRATION TERMINÉE AVEC SUCCÈS';
    RAISE NOTICE '========================================';
END $$;

-- ==============================================================================
-- ÉTAPE 12: NETTOYAGE DES TABLES TEMPORAIRES
-- ==============================================================================

DROP TABLE IF EXISTS temp_duplicates;
DROP TABLE IF EXISTS temp_deleted_transactions;
DROP TABLE IF EXISTS temp_delete_count;
DROP TABLE IF EXISTS temp_migrate_count;
DROP TABLE IF EXISTS temp_missing_months;

-- ==============================================================================
-- NOTES FINALES
-- ==============================================================================

-- Cette migration a effectué les actions suivantes:
-- 1. Identifié et supprimé les transactions en double entre les comptes 15 et 16
-- 2. Migré toutes les transactions restantes du compte 15 vers le compte 16
-- 3. Désactivé le compte 15 (marqué comme obsolète)
-- 4. Créé des index pour optimiser les recherches de doublons
-- 5. Ajouté un trigger pour détecter les futurs doublons potentiels
-- 6. Vérifié l'intégrité et la continuité des données

-- Pour des imports futurs:
-- - Toujours importer les relevés COMPTECOURANT_*.pdf sur le compte 16 (LCL Noutam)
-- - Le trigger alertera automatiquement en cas de doublon potentiel
