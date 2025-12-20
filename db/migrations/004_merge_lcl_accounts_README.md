# Migration 004: Fusion des comptes LCL Principal et Noutam

## Contexte du problème

### Problème identifié
Les comptes **LCL Principal** (account_id=15) et **LCL Noutam** (account_id=16) représentent EN FAIT le même compte bancaire physique. Cette erreur a été causée par:

1. Les fichiers `COMPTECOURANT_*.pdf` (relevés bancaires Noutam) ont été incorrectement importés sur le compte 15
2. Il existe des chevauchements de dates entre les deux comptes
3. 319 transactions sont présentes en double entre les deux comptes

### Données avant migration
```
Compte 15 (LCL Principal): 2243 transactions (2023-12-31 à 2025-12-31)
Compte 16 (LCL Noutam):    1683 transactions (2023-11-30 à 2025-12-31)
Doublons détectés:         319 paires de transactions
```

### Distribution temporelle
- **2023-12** : Uniquement compte 16
- **2024-01 à 2024-12** : Principalement compte 15
- **2024-02** : Chevauchement (147 tx sur 15, 147 tx sur 16)
- **2025-01** : Chevauchement (170 tx sur 15, 169 tx sur 16)
- **2025-03 à 2025-10** : Uniquement compte 16

## Solution mise en place

### Architecture de la migration

La migration `004_merge_lcl_accounts.sql` effectue les opérations suivantes:

1. **Analyse préliminaire** : Comptage des transactions et identification des doublons
2. **Identification intelligente des doublons** : Création d'une table temporaire avec priorités
3. **Sauvegarde audit** : Conservation des transactions supprimées pour traçabilité
4. **Suppression des relations** : Nettoyage des foreign keys (payments, reconciliations, etc.)
5. **Suppression des doublons** : Suppression des transactions en double
6. **Migration des transactions** : Déplacement de toutes les transactions du compte 15 vers 16
7. **Mise à jour des relations** : Correction des counterparty_account_id
8. **Création d'index** : Index optimisés pour détecter les futurs doublons
9. **Trigger de protection** : Détection automatique des doublons futurs
10. **Désactivation du compte 15** : Marquage du compte comme obsolète
11. **Vérifications** : Contrôles d'intégrité et de continuité des données

### Stratégie de déduplication

Pour chaque doublon détecé (même date_operation + même amount), la migration conserve la transaction selon cet ordre de priorité:

1. **Priorité au compte de destination** : Préférer account_id=16 (LCL Noutam)
2. **Qualité de la référence** : Préférer les transactions sans ref_externe "stmtline:"
3. **Richesse du label** : Préférer les transactions avec un label plus descriptif (plus long)
4. **Récence** : En cas d'égalité, préférer la transaction la plus récente (created_at DESC)

## Exécution de la migration

### Prérequis
- PostgreSQL database: `epicerie`
- Container Docker: `57a2d3cfb432_inventaire-db`
- User: `postgres`
- Permissions: Read/Write sur les tables finance_*

### Méthode 1: Via script bash (recommandé)

```bash
cd /home/ruuuzer/Documents/monprojet
chmod +x scripts/run_lcl_merge_migration.sh
./scripts/run_lcl_merge_migration.sh
```

Le script effectue automatiquement:
- Vérification du container Docker
- Création d'une sauvegarde avant migration
- Copie du fichier SQL dans le container
- Exécution de la migration
- Affichage des résultats

### Méthode 2: Via Docker directement

```bash
# 1. Copier le fichier de migration dans le container
docker cp /home/ruuuzer/Documents/monprojet/db/migrations/004_merge_lcl_accounts.sql \
    57a2d3cfb432_inventaire-db:/tmp/migration.sql

# 2. Créer une sauvegarde
docker exec 57a2d3cfb432_inventaire-db \
    pg_dump -U postgres -d epicerie -t finance_transactions -t finance_accounts \
    > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

# 3. Exécuter la migration
docker exec -i 57a2d3cfb432_inventaire-db \
    psql -U postgres -d epicerie -f /tmp/migration.sql
```

### Méthode 3: Via psql local (si installé)

```bash
psql -h localhost -U postgres -d epicerie \
    -f /home/ruuuzer/Documents/monprojet/db/migrations/004_merge_lcl_accounts.sql
```

## Résultats attendus

### Après migration

```
Compte 15 (LCL Principal): 0 transactions (désactivé, label modifié)
Compte 16 (LCL Noutam):    ~3607 transactions (2243 + 1683 - 319 doublons)
Doublons restants:         0
```

### Distribution mensuelle unifiée

Le compte 16 devrait maintenant avoir une couverture complète de:
- 2023-12 à 2025-12
- Sans trou de données
- Avec tous les flux de trésorerie consolidés

### Vérifications automatiques

La migration affiche automatiquement:

1. **Statistiques avant/après**
   - Nombre de transactions par compte
   - Nombre de doublons détectés
   - Nombre de transactions supprimées/migrées

2. **Échantillon des doublons**
   - 10 premiers doublons avec détails
   - Indication de la transaction conservée vs supprimée

3. **Distribution mensuelle**
   - Nombre de transactions par mois
   - Total IN (crédits) et OUT (débits) par mois

4. **Continuité temporelle**
   - Détection des mois sans transactions (trous dans les données)
   - Validation de la continuité

## Mesures de protection

### Trigger de détection des doublons

Un trigger `trigger_check_duplicate_transaction` a été créé pour détecter automatiquement les futurs doublons:

```sql
CREATE TRIGGER trigger_check_duplicate_transaction
    BEFORE INSERT OR UPDATE ON finance_transactions
    FOR EACH ROW
    EXECUTE FUNCTION check_duplicate_transaction();
```

Le trigger émet un **WARNING** (pas d'erreur bloquante) quand:
- Même account_id
- Même date_operation
- Même amount
- Même label

### Index optimisés

Deux index ont été créés pour optimiser les recherches:

1. **ix_finance_tx_dedup**
   ```sql
   CREATE INDEX ix_finance_tx_dedup
   ON finance_transactions(account_id, date_operation, amount);
   ```
   Permet de détecter rapidement les doublons potentiels

2. **ix_finance_tx_ref_externe_stmtline**
   ```sql
   CREATE INDEX ix_finance_tx_ref_externe_stmtline
   ON finance_transactions(ref_externe)
   WHERE ref_externe LIKE 'stmtline:%';
   ```
   Permet d'identifier rapidement les transactions avec ref_externe de type stmtline

## Rollback (en cas de problème)

### Restauration depuis la sauvegarde

Si la migration échoue ou produit des résultats incorrects:

```bash
# Restaurer depuis la sauvegarde créée par le script
psql -U postgres -d epicerie < /tmp/backup_before_lcl_merge_YYYYMMDD_HHMMSS.sql

# Ou via Docker
docker exec -i 57a2d3cfb432_inventaire-db \
    psql -U postgres -d epicerie < backup_before_lcl_merge_YYYYMMDD_HHMMSS.sql
```

### Nettoyage manuel (si nécessaire)

Si vous devez nettoyer partiellement:

```sql
-- Réactiver le compte 15
UPDATE finance_accounts
SET
    is_active = true,
    label = 'LCL - Principal',
    updated_at = CURRENT_TIMESTAMP
WHERE id = 15;

-- Supprimer le trigger de détection
DROP TRIGGER IF EXISTS trigger_check_duplicate_transaction ON finance_transactions;
DROP FUNCTION IF EXISTS check_duplicate_transaction();

-- Supprimer les index créés
DROP INDEX IF EXISTS ix_finance_tx_dedup;
DROP INDEX IF EXISTS ix_finance_tx_ref_externe_stmtline;
```

## Bonnes pratiques pour les imports futurs

### Import des relevés COMPTECOURANT_*.pdf

**TOUJOURS** importer les fichiers `COMPTECOURANT_*.pdf` sur le **compte 16 (LCL Noutam)**.

```python
# Exemple dans le code d'import
BANK_ACCOUNT_MAPPING = {
    "COMPTECOURANT": 16,  # LCL Noutam
    "LIVRETA": 17,        # Autre compte
    # ...
}
```

### Détection des doublons lors de l'import

Le trigger créé alertera automatiquement si un doublon est détecté. Pour une détection proactive avant import:

```sql
-- Vérifier si une transaction existe déjà
SELECT COUNT(*) FROM finance_transactions
WHERE account_id = 16
  AND date_operation = '2025-01-15'
  AND amount = 123.45
  AND label LIKE '%PRLV SEPA%';
```

### Validation post-import

Après chaque import, vérifier:

```sql
-- 1. Vérifier qu'il n'y a pas de nouveaux doublons
SELECT date_operation, amount, COUNT(*) as duplicates
FROM finance_transactions
WHERE account_id = 16
GROUP BY date_operation, amount
HAVING COUNT(*) > 1;

-- 2. Vérifier la continuité temporelle
SELECT
    TO_CHAR(date_operation, 'YYYY-MM') as month,
    COUNT(*) as nb_tx
FROM finance_transactions
WHERE account_id = 16
GROUP BY TO_CHAR(date_operation, 'YYYY-MM')
ORDER BY month;
```

## Fichiers créés

- `/home/ruuuzer/Documents/monprojet/db/migrations/004_merge_lcl_accounts.sql` - Migration SQL complète
- `/home/ruuuzer/Documents/monprojet/scripts/run_lcl_merge_migration.sh` - Script d'exécution
- `/home/ruuuzer/Documents/monprojet/db/migrations/004_merge_lcl_accounts_README.md` - Cette documentation

## Logs et audit

La migration crée des tables temporaires pour audit:
- `temp_duplicates` : Liste des doublons identifiés
- `temp_deleted_transactions` : Sauvegarde des transactions supprimées
- `temp_delete_count` : Nombre de suppressions
- `temp_migrate_count` : Nombre de migrations

Ces tables sont automatiquement supprimées à la fin de la migration, mais les informations sont affichées via `RAISE NOTICE`.

## Support

En cas de problème ou de question:

1. Vérifier les logs PostgreSQL du container
2. Consulter les messages NOTICE de la migration
3. Vérifier les sauvegardes dans `/tmp/backup_before_lcl_merge_*`
4. Examiner les transactions dans `temp_deleted_transactions` (si vous stoppez la migration avant la fin)

## Historique

- **2025-12-17** : Création de la migration initiale
- **Auteur** : Assistant Claude
- **Version** : 1.0
