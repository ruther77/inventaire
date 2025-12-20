# Quick Start - Phase 3 Migration

**Objectif**: Migrer les orphelins de `restaurant_bank_statements` vers `finance_bank_statement_lines`

## 🚀 Démarrage Rapide (5 minutes)

### Étape 1: Analyse Rapide
```bash
cd /home/ruuuzer/Documents/monprojet

# Combien d'orphelins ?
psql -U app_user -d app_db -c "
SELECT COUNT(*)
FROM restaurant_bank_statements rbs
LEFT JOIN finance_bank_statement_lines fbsl
    ON rbs.date::date = fbsl.date_operation
    AND ABS(rbs.montant - fbsl.montant) < 0.01
WHERE fbsl.id IS NULL;
"
```

### Étape 2: Backup (1 minute)
```bash
./scripts/backup_and_test_migration.sh
```

### Étape 3: Test Migration (10 lignes)
```bash
python scripts/migrate_restaurant_orphans.py --execute --limit 10
```

### Étape 4: Vérifier le Test
```bash
./scripts/quick_status.sh
```

### Étape 5: Migration Complète
```bash
python scripts/migrate_restaurant_orphans.py --execute
```

### Étape 6: Validation
```bash
psql -U app_user -d app_db -f scripts/validate_migration.sql
```

### Étape 7: Finalisation (si validation OK)
```bash
psql -U app_user -d app_db -f db/migrations/006_deprecate_restaurant_bank_statements.sql
```

---

## 📁 Fichiers Importants

| Fichier | Description |
|---------|-------------|
| `PHASE_3_UNIFICATION_GUIDE.md` | Guide complet (lire en premier) |
| `PHASE_3_FILES_SUMMARY.md` | Récapitulatif de tous les fichiers |
| `scripts/migrate_restaurant_orphans.py` | Script de migration |
| `scripts/quick_status.sh` | Vérifier l'état rapidement |
| `scripts/validate_migration.sql` | Validation complète |

---

## 🆘 En Cas de Problème

### Rollback Rapide
```bash
# Restaurer depuis le backup le plus récent
BACKUP_DIR=$(ls -td backups/migration_phase3_* | head -1)
pg_restore -h localhost -p 5432 -U app_user -d app_db --clean \
    ${BACKUP_DIR}/restaurant_bank_statements.backup
```

### Vérifier les Logs
```bash
tail -50 migration_restaurant_orphans.log
```

---

## ✅ Checklist

- [ ] Backup créé avec succès
- [ ] Test migration (10 lignes) OK
- [ ] Migration complète terminée
- [ ] Validation SQL réussie
- [ ] 0 orphelins restants
- [ ] Table dépréciée

---

**Pour plus de détails, consulter**: `PHASE_3_UNIFICATION_GUIDE.md`
