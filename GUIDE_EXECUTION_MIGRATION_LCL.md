# Guide d'exécution: Migration fusion comptes LCL

## Résumé rapide

Cette migration fusionne les comptes **LCL Principal (15)** et **LCL Noutam (16)** qui représentent le même compte bancaire.

- **Doublons à supprimer**: 319 transactions
- **Transactions à migrer**: ~1924 transactions du compte 15 vers 16
- **Résultat**: Un seul compte LCL Noutam (16) avec toutes les transactions

## Exécution en 3 étapes

### Étape 1: Vérifier que vous êtes prêt

```bash
# Vérifier que le container est actif
docker ps | grep inventaire-db

# Vérifier l'accès à la base
docker exec 57a2d3cfb432_inventaire-db psql -U postgres -d epicerie -c "SELECT COUNT(*) FROM finance_transactions WHERE account_id IN (15, 16);"
```

Vous devriez voir environ 3926 transactions.

### Étape 2: Exécuter la migration

**Option A - Via script bash (RECOMMANDÉ)**

```bash
cd /home/ruuuzer/Documents/monprojet

# Rendre le script exécutable
chmod +x scripts/run_lcl_merge_migration.sh

# Exécuter
./scripts/run_lcl_merge_migration.sh
```

**Option B - Manuellement via Docker**

```bash
cd /home/ruuuzer/Documents/monprojet

# 1. Copier le fichier dans le container
docker cp db/migrations/004_merge_lcl_accounts.sql 57a2d3cfb432_inventaire-db:/tmp/migration.sql

# 2. Créer une sauvegarde
docker exec 57a2d3cfb432_inventaire-db \
    pg_dump -U postgres -d epicerie -t finance_transactions -t finance_accounts \
    > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

# 3. Exécuter la migration
docker exec -i 57a2d3cfb432_inventaire-db \
    psql -U postgres -d epicerie -f /tmp/migration.sql
```

### Étape 3: Vérifier les résultats

```bash
# Copier le script de vérification dans le container
docker cp scripts/verify_lcl_merge.sql 57a2d3cfb432_inventaire-db:/tmp/verify.sql

# Exécuter les vérifications
docker exec -i 57a2d3cfb432_inventaire-db \
    psql -U postgres -d epicerie -f /tmp/verify.sql
```

## Que se passe-t-il pendant la migration?

La migration affiche des messages pour chaque étape:

```
========================================
ANALYSE AVANT MIGRATION
========================================
Compte 15 (LCL Principal): 2243 transactions
Compte 16 (LCL Noutam):    1683 transactions
Doublons détectés:         319 paires
========================================

========================================
ÉCHANTILLON DES DOUBLONS (10 premiers)
========================================
1 | Date: 2025-12-31 | Montant: 112.26 EUR
  → GARDER   ID:136489 (Compte 16) - "RESULTAT ARRETE COMPTE 31122024"
  → SUPPRIMER ID:136490 (Compte 15) - "RESULTAT ARRETE COMPTE 31122024"
...

========================================
Transactions à supprimer: 319
========================================

========================================
Doublons supprimés: 319 transactions
========================================

========================================
Transactions migrées de 15 vers 16: 1924
========================================

========================================
VÉRIFICATION POST-MIGRATION
========================================
Compte 15 (désactivé): 0 transactions
Compte 16 (LCL Noutam): 3607 transactions
Doublons restants: 0

Distribution par mois pour compte 16:
----------------------------------------
  2023-12 | 126 tx | IN: 123456.78 EUR | OUT: 98765.43 EUR
  2024-01 | 157 tx | IN: 234567.89 EUR | OUT: 123456.78 EUR
  ...

========================================
OK: Aucun trou dans les données (continuité mensuelle complète)
========================================

========================================
MIGRATION TERMINÉE AVEC SUCCÈS
========================================
```

## Résultats attendus

### Avant migration
```
Compte 15: 2243 transactions
Compte 16: 1683 transactions
Total:     3926 transactions
Doublons:  319 paires
```

### Après migration
```
Compte 15: 0 transactions (désactivé)
Compte 16: 3607 transactions (2243 + 1683 - 319)
Total:     3607 transactions uniques
Doublons:  0
```

## En cas de problème

### Restaurer depuis la sauvegarde

Si quelque chose ne va pas:

```bash
# Trouver votre sauvegarde
ls -lh backup_before_migration_*.sql

# Restaurer
docker exec -i 57a2d3cfb432_inventaire-db \
    psql -U postgres -d epicerie < backup_before_migration_YYYYMMDD_HHMMSS.sql
```

### Vérifications manuelles

```sql
-- Compter les transactions
SELECT account_id, COUNT(*) FROM finance_transactions
WHERE account_id IN (15, 16)
GROUP BY account_id;

-- Vérifier les doublons
SELECT date_operation, amount, COUNT(*)
FROM finance_transactions
WHERE account_id IN (15, 16)
GROUP BY date_operation, amount
HAVING COUNT(*) > 1;

-- Vérifier l'état du compte 15
SELECT id, label, is_active FROM finance_accounts WHERE id = 15;
```

## Logs à consulter

Si vous voyez des erreurs, consultez:

```bash
# Logs du container
docker logs 57a2d3cfb432_inventaire-db --tail 100

# Logs PostgreSQL dans le container
docker exec 57a2d3cfb432_inventaire-db \
    tail -100 /var/log/postgresql/postgresql-*.log
```

## Après la migration

### Mise à jour du code d'import

Assurez-vous que votre code d'import pointe vers le bon compte:

```python
# Dans votre code Python d'import
BANK_ACCOUNT_MAPPING = {
    "COMPTECOURANT": 16,  # LCL Noutam (CORRIGÉ - était 15 avant)
    "LIVRETA": 17,
    # ...
}
```

### Trigger de protection

Un trigger a été installé pour détecter automatiquement les futurs doublons.
Si vous importez une transaction en double, vous verrez:

```
WARNING:  Possible duplicate transaction detected: account_id=16, date=2025-01-15, amount=123.45, label=PRLV SEPA...
```

Le trigger n'empêche pas l'insertion (pour ne pas bloquer les imports), mais vous alerte.

## Support

### Fichiers créés

- `db/migrations/004_merge_lcl_accounts.sql` - Migration complète
- `scripts/run_lcl_merge_migration.sh` - Script d'exécution
- `scripts/verify_lcl_merge.sql` - Script de vérification
- `db/migrations/004_merge_lcl_accounts_README.md` - Documentation détaillée

### Commandes utiles

```bash
# Voir les transactions migrées
docker exec 57a2d3cfb432_inventaire-db psql -U postgres -d epicerie -c \
    "SELECT COUNT(*) FROM finance_transactions WHERE account_id = 16 AND note LIKE '%Migrated from account 15%';"

# Vérifier l'index de déduplication
docker exec 57a2d3cfb432_inventaire-db psql -U postgres -d epicerie -c \
    "SELECT indexname FROM pg_indexes WHERE tablename = 'finance_transactions' AND indexname LIKE '%dedup%';"

# Tester le trigger
docker exec 57a2d3cfb432_inventaire-db psql -U postgres -d epicerie -c \
    "SELECT proname FROM pg_proc WHERE proname = 'check_duplicate_transaction';"
```

## Checklist finale

Après avoir exécuté la migration, vérifiez:

- [ ] Le compte 15 a 0 transactions
- [ ] Le compte 16 a environ 3607 transactions
- [ ] Il n'y a plus de doublons (compte = 0)
- [ ] Le compte 15 est marqué comme inactif (is_active = false)
- [ ] Le trigger `trigger_check_duplicate_transaction` existe
- [ ] Les index `ix_finance_tx_dedup` et `ix_finance_tx_ref_externe_stmtline` existent
- [ ] Aucun trou dans les données (continuité mensuelle)
- [ ] La sauvegarde backup_before_migration_*.sql existe

---

**Date**: 2025-12-17
**Version**: 1.0
**Auteur**: Assistant Claude
