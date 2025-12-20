# Scripts de Migration - Phase 3

Ce dossier contient les scripts pour la Phase 3 du plan de refactoring: **Unification des données bancaires**.

## Scripts Disponibles

### 1. `analyze_orphans.sql`
**Analyse préalable des orphelins**

Exécute une série de requêtes pour identifier:
- Nombre total d'orphelins
- Répartition par compte bancaire
- Orphelins avec liens `depense_id`
- Distribution temporelle
- Échantillons de données

**Usage**:
```bash
psql -U app_user -d app_db -f scripts/analyze_orphans.sql
```

**Sortie**: Rapport détaillé avec statistiques et résumé

---

### 2. `migrate_restaurant_orphans.py`
**Script Python de migration**

Migre les orphelins de `restaurant_bank_statements` vers `finance_bank_statement_lines`.

**Fonctionnalités**:
- Identification automatique des orphelins
- Création des comptes manquants
- Génération de statements mensuels
- Création de transactions
- Préservation des liens `depense_id`
- Logging détaillé

**Options**:
- `--dry-run`: Analyse sans écriture
- `--execute`: Exécute la migration
- `--limit N`: Limite à N lignes (pour test)

**Exemples**:
```bash
# Analyse seulement
python scripts/migrate_restaurant_orphans.py --dry-run

# Migration complète
python scripts/migrate_restaurant_orphans.py --execute

# Test sur 10 lignes
python scripts/migrate_restaurant_orphans.py --execute --limit 10
```

**Logs**: `migration_restaurant_orphans.log`

---

### 3. `backup_and_test_migration.sh`
**Script de backup et test automatisé**

Orchestre l'ensemble du processus de préparation:
1. Création de backups (.backup PostgreSQL)
2. Export CSV des orphelins
3. Exécution de l'analyse SQL
4. Test en dry-run
5. Génération du guide de validation

**Usage**:
```bash
./scripts/backup_and_test_migration.sh
```

**Sortie**: Dossier `backups/migration_phase3_YYYYMMDD_HHMMSS/` contenant:
- `restaurant_bank_statements.backup` (backup pg_dump)
- `finance_tables.backup` (backup tables finance)
- `orphans_to_migrate.csv` (export CSV)
- `analysis_report.txt` (rapport SQL)
- `dryrun_output.txt` (logs dry-run)
- `VALIDATION.md` (guide de validation)

---

## Workflow Recommandé

### Étape 1: Analyse
```bash
psql -U app_user -d app_db -f scripts/analyze_orphans.sql > report.txt
cat report.txt | grep "RÉSUMÉ"
```

### Étape 2: Backup
```bash
./scripts/backup_and_test_migration.sh
```

### Étape 3: Test Limité
```bash
python scripts/migrate_restaurant_orphans.py --execute --limit 10
```

### Étape 4: Validation Test
```sql
-- Vérifier les 10 lignes migrées
SELECT * FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;
```

### Étape 5: Migration Complète
```bash
python scripts/migrate_restaurant_orphans.py --execute
```

### Étape 6: Validation Finale
```bash
# Suivre le guide dans backups/migration_phase3_*/VALIDATION.md
```

---

## Variables d'Environnement

Les scripts utilisent les variables PostgreSQL standard:
- `DB_NAME` (défaut: `app_db`)
- `DB_USER` (défaut: `app_user`)
- `DB_HOST` (défaut: `localhost`)
- `DB_PORT` (défaut: `5432`)
- `PGPASSWORD` (mot de passe PostgreSQL)

**Exemple**:
```bash
export DB_NAME=app_db
export DB_USER=app_user
export PGPASSWORD=app_password
./scripts/backup_and_test_migration.sh
```

---

## Troubleshooting

### Erreur: "Permission denied"
```bash
chmod +x scripts/backup_and_test_migration.sh
chmod +x scripts/migrate_restaurant_orphans.py
```

### Erreur: "Module not found"
```bash
# Vérifier que le PYTHONPATH est correct
export PYTHONPATH=/home/ruuuzer/Documents/monprojet:$PYTHONPATH
```

### Erreur: "Table already exists"
Si la migration a déjà été partiellement exécutée:
```sql
-- Rollback manuel
DELETE FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;
```

### Erreur: "Duplicate key violation"
Le checksum détecte un doublon. Vérifier:
```sql
SELECT * FROM finance_bank_statement_lines
WHERE checksum = 'xxx';
```

---

## Sécurité

- **Backups automatiques**: Tous les scripts créent des backups avant modification
- **Transactions**: Le script Python utilise des transactions pour garantir l'atomicité
- **Dry-run**: Toujours tester avec `--dry-run` avant `--execute`
- **Limites**: Utiliser `--limit` pour tester sur un petit échantillon

---

## Monitoring

### Logs
- `migration_restaurant_orphans.log`: Logs détaillés de la migration
- `backups/migration_phase3_*/dryrun_output.txt`: Sortie du dry-run
- `backups/migration_phase3_*/analysis_report.txt`: Rapport SQL

### Requêtes de Suivi
```sql
-- Progression de la migration
SELECT
    COUNT(*) as total_migrated,
    MIN(created_at) as first_migration,
    MAX(created_at) as last_migration
FROM finance_bank_statement_lines
WHERE raw_data::jsonb->>'migrated_at' IS NOT NULL;

-- Orphelins restants
SELECT COUNT(*)
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL;
```

---

## Support

En cas de problème:
1. Consulter les logs (`migration_restaurant_orphans.log`)
2. Vérifier les backups (`backups/migration_phase3_*/`)
3. Consulter le guide principal (`PHASE_3_UNIFICATION_GUIDE.md`)
4. Exécuter les requêtes de diagnostic

---

**Note**: Ces scripts font partie du plan de refactoring Phase 3. Voir `PHASE_3_UNIFICATION_GUIDE.md` pour le contexte complet.
