# Phase 3 du Plan de Refactoring - UNIFICATION

**Date**: 2025-12-19
**Objectif**: Migrer les données orphelines de `restaurant_bank_statements` vers `finance_bank_statement_lines` et unifier le système bancaire.

## Contexte

Actuellement, les données bancaires sont fragmentées entre:
- **`restaurant_bank_statements`** (ancien système, table legacy)
- **`finance_bank_statement_lines`** (nouveau système unifié)

Cette phase vise à:
1. Identifier et migrer les orphelins (données dans RBS sans correspondance dans finance)
2. Préserver les liens `depense_id` via `finance_transaction_expense_links`
3. Déprécier `restaurant_bank_statements` (renommer en `_deprecated_*`)
4. Assurer la synchronisation `invoices → finance_invoices_supplier` (déjà implémentée)

---

## Architecture de Migration

### Tables Impliquées

```
restaurant_bank_statements (SOURCE - à déprécier)
    ↓
finance_bank_statement_lines (CIBLE)
    ↓
finance_transactions (via finance_reconciliations)
    ↓
finance_transaction_expense_links (préserve depense_id)
```

### Flux de Données

```
1. restaurant_bank_statements.id → raw_data.original_rbs_id
2. depense_id → finance_transaction_expense_links
3. account → finance_accounts (via label)
4. date/montant → finance_bank_statement_lines
5. finance_bank_statement_lines → finance_transactions (auto-réconciliation)
```

---

## Fichiers Créés

### 1. Script Python de Migration
**Fichier**: `/home/ruuuzer/Documents/monprojet/scripts/migrate_restaurant_orphans.py`

**Fonctionnalités**:
- Identification automatique des orphelins
- Migration sécurisée avec transactions
- Préservation des liens `depense_id`
- Logging détaillé de chaque opération
- Mode `--dry-run` pour tester sans écriture

**Usage**:
```bash
# Analyse seulement
python scripts/migrate_restaurant_orphans.py --dry-run

# Migration complète
python scripts/migrate_restaurant_orphans.py --execute

# Migration limitée (test sur 100 lignes)
python scripts/migrate_restaurant_orphans.py --execute --limit 100
```

### 2. Script SQL d'Analyse
**Fichier**: `/home/ruuuzer/Documents/monprojet/scripts/analyze_orphans.sql`

**Contenu**:
- Statistiques globales (total RBS, orphelins, matchés)
- Orphelins par compte bancaire
- Orphelins avec liens `depense_id`
- Orphelins par période
- Échantillon de données à migrer
- Vérification des comptes finance existants
- Détection de doublons potentiels

**Usage**:
```bash
psql -U app_user -d app_db -f scripts/analyze_orphans.sql
```

### 3. Script de Backup et Test
**Fichier**: `/home/ruuuzer/Documents/monprojet/scripts/backup_and_test_migration.sh`

**Fonctionnalités**:
- Backup automatique de `restaurant_bank_statements`
- Backup des tables `finance_*`
- Export CSV des orphelins pour référence
- Exécution automatique de l'analyse SQL
- Test en mode dry-run
- Génération d'un guide de validation

**Usage**:
```bash
./scripts/backup_and_test_migration.sh
```

---

## Procédure d'Exécution

### Étape 1: Préparation et Analyse

```bash
# 1. Naviguer dans le répertoire du projet
cd /home/ruuuzer/Documents/monprojet

# 2. Exécuter l'analyse SQL
psql -U app_user -d app_db -f scripts/analyze_orphans.sql > analysis_report.txt

# 3. Vérifier le rapport
cat analysis_report.txt | grep -A 10 "RÉSUMÉ POUR MIGRATION"
```

**Vérifications**:
- Nombre d'orphelins identifiés
- Nombre d'orphelins avec `depense_id`
- Comptes bancaires concernés
- Montant total des orphelins

### Étape 2: Backup et Test

```bash
# 1. Exécuter le script de backup
./scripts/backup_and_test_migration.sh

# 2. Vérifier les backups créés
ls -lh backups/migration_phase3_*/

# 3. Vérifier le dry-run
cat backups/migration_phase3_*/dryrun_output.txt
```

**Vérifications**:
- Backups créés avec succès
- Dry-run sans erreurs
- Statistiques cohérentes

### Étape 3: Migration (Test Limité)

```bash
# Migrer uniquement 10 lignes pour tester
python scripts/migrate_restaurant_orphans.py --execute --limit 10

# Vérifier les résultats
psql -U app_user -d app_db -c "
SELECT COUNT(*) FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;
"
```

**Vérifications**:
- 10 lignes migrées avec succès
- Pas d'erreurs dans les logs
- Données correctes dans `finance_bank_statement_lines`

### Étape 4: Migration Complète

```bash
# Exécuter la migration complète
python scripts/migrate_restaurant_orphans.py --execute

# Vérifier le log de migration
cat migration_restaurant_orphans.log
```

### Étape 5: Validation Post-Migration

```bash
# Exécuter les requêtes de validation
psql -U app_user -d app_db
```

**Requêtes de validation**:

```sql
-- 1. Vérifier qu'il n'y a plus d'orphelins
SELECT COUNT(*)
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL;
-- Attendu: 0

-- 2. Vérifier les liens depense_id
SELECT COUNT(*) FROM finance_transaction_expense_links
WHERE migrated_from = 'restaurant_bank_statements';
-- Attendu: nombre d'orphelins avec depense_id

-- 3. Vérifier l'intégrité des montants
SELECT
    SUM(rbs.montant) as total_rbs,
    SUM(fbsl.montant) as total_fbsl,
    ABS(SUM(rbs.montant) - SUM(fbsl.montant)) as difference
FROM restaurant_bank_statements rbs
JOIN finance_bank_statement_lines fbsl
    ON fbsl.raw_data::jsonb->>'original_rbs_id' = rbs.id::text;
-- Différence attendue: < 0.01

-- 4. Vérifier les transactions créées
SELECT COUNT(*) FROM finance_transactions
WHERE source = 'migration_rbs';
-- Attendu: nombre d'orphelins migrés
```

### Étape 6: Dépréciation de la Table

**Une fois la migration validée**, exécuter la migration SQL:

```bash
psql -U app_user -d app_db -f db/migrations/006_deprecate_restaurant_bank_statements.sql
```

**Ceci va**:
1. Renommer `restaurant_bank_statements` → `_deprecated_restaurant_bank_statements`
2. Créer une vue `restaurant_bank_statements` pour la compatibilité arrière
3. Ajouter un commentaire explicatif sur la table dépréciée

---

## Rollback en Cas de Problème

### Option 1: Restauration depuis Backup

```bash
# Restaurer restaurant_bank_statements
pg_restore -h localhost -p 5432 -U app_user -d app_db --clean \
    backups/migration_phase3_*/restaurant_bank_statements.backup

# Restaurer les tables finance
pg_restore -h localhost -p 5432 -U app_user -d app_db --clean \
    backups/migration_phase3_*/finance_tables.backup
```

### Option 2: Rollback Manuel (SQL)

```sql
BEGIN;

-- Supprimer les données migrées
DELETE FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;

DELETE FROM finance_transaction_expense_links
WHERE migrated_from = 'restaurant_bank_statements';

DELETE FROM finance_reconciliations
WHERE statement_line_id IN (
    SELECT id FROM finance_bank_statement_lines
    WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL
);

DELETE FROM finance_transactions
WHERE source = 'migration_rbs';

COMMIT;
```

---

## Synchronisation Invoices (Déjà Implémentée)

### État Actuel

La synchronisation `processed_invoices → finance_invoices_supplier` est **déjà implémentée** dans:
- **Fichier**: `/home/ruuuzer/Documents/monprojet/backend/services/invoices.py`
- **Fonction**: `_sync_to_finance_invoices_supplier()` (lignes 657-722)

### Fonctionnement

Chaque fois qu'une facture est enregistrée via `record_processed_invoices()`:
1. La facture est insérée dans `processed_invoices` (ancien système)
2. La fonction `_sync_to_finance_invoices_supplier()` est appelée automatiquement
3. Un vendor est créé/récupéré dans `finance_vendors`
4. La facture est insérée dans `finance_invoices_supplier` avec:
   - `ref_externe` = `processed_invoices:{tenant_id}:{invoice_id}`
   - Totaux HT/TTC calculés depuis les lignes
   - Status = 'pending'

### Vérification

```sql
-- Vérifier la synchronisation
SELECT
    pi.invoice_id,
    pi.supplier,
    pi.facture_date,
    fis.id as finance_invoice_id,
    fis.montant_ttc,
    fis.status
FROM processed_invoices pi
LEFT JOIN finance_invoices_supplier fis
    ON fis.ref_externe = 'processed_invoices:' || pi.tenant_id || ':' || pi.invoice_id
ORDER BY pi.created_at DESC
LIMIT 10;
```

---

## Logs et Monitoring

### Logs de Migration

**Fichier**: `migration_restaurant_orphans.log`

Contient:
- Timestamp de chaque opération
- RBS migrés avec succès
- Erreurs rencontrées
- Statistiques finales

### Monitoring Post-Migration

```sql
-- Vue pour surveiller les migrations
CREATE OR REPLACE VIEW v_migration_status AS
SELECT
    (SELECT COUNT(*) FROM _deprecated_restaurant_bank_statements) as total_rbs,
    (SELECT COUNT(*) FROM finance_bank_statement_lines WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL) as migrated,
    (SELECT COUNT(*) FROM finance_transaction_expense_links WHERE migrated_from = 'restaurant_bank_statements') as linked_depenses,
    (SELECT COUNT(*) FROM finance_transactions WHERE source = 'migration_rbs') as transactions_created;
```

---

## Checklist de Validation

- [ ] Analyse SQL exécutée sans erreurs
- [ ] Backups créés et vérifiés
- [ ] Dry-run exécuté avec succès
- [ ] Migration test (10 lignes) réussie
- [ ] Migration complète terminée
- [ ] 0 orphelins restants (requête validation #1)
- [ ] Liens depense_id préservés (requête validation #2)
- [ ] Intégrité des montants vérifiée (requête validation #3)
- [ ] Transactions créées (requête validation #4)
- [ ] Table dépréciée et vue créée
- [ ] Documentation mise à jour
- [ ] Équipe informée

---

## Points d'Attention

### 1. Gestion des Doublons

Le script utilise un **checksum MD5** pour éviter les doublons:
```python
checksum = md5(f"{account}_{date}_{montant}_{libelle}".encode()).hexdigest()
```

Si un doublon existe déjà, PostgreSQL retournera une erreur de contrainte unique.

### 2. Mapping Tenant → Entity

Convention du projet:
- `tenant_id=1` (Épicerie) → `entity_id=1`
- `tenant_id=2` (Restaurant) → `entity_id=2`
- `tenant_id=4` (Restaurant alt) → `entity_id=2`

### 3. Direction des Transactions

Le script détermine automatiquement:
- Montant > 0 → `direction='IN'` (crédit)
- Montant < 0 → `direction='OUT'` (débit)

### 4. Préservation des Métadonnées

Toutes les données originales sont préservées dans `raw_data` (JSONB):
```json
{
  "original_rbs_id": 123,
  "tenant_id": 2,
  "categorie": "Fournisseur",
  "type": "Sortie",
  "mois": "2024-12",
  "source": "import_pdf",
  "migrated_at": "2025-12-19T10:30:00"
}
```

---

## Support et Questions

En cas de problème:
1. Consulter les logs: `migration_restaurant_orphans.log`
2. Vérifier les backups: `backups/migration_phase3_*/`
3. Consulter le guide de validation: `backups/migration_phase3_*/VALIDATION.md`
4. Exécuter les requêtes de diagnostic

---

## Prochaines Étapes (Post-Phase 3)

1. **Nettoyage du code legacy**:
   - Supprimer les références à `restaurant_bank_statements` dans le code
   - Mettre à jour la documentation

2. **Migration Phase 4** (si applicable):
   - Unification des catégories
   - Harmonisation des règles de classification

3. **Optimisation**:
   - Créer des index sur `finance_transaction_expense_links`
   - Matérialiser les vues fréquemment utilisées

---

**Dernière mise à jour**: 2025-12-19
**Auteur**: Claude Opus 4.5
**Version**: 1.0
