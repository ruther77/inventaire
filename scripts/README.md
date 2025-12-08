# Scripts

Organisation des scripts du projet.

## Structure

```
scripts/
├── imports/      # Import de données (PDF, CSV, fournisseurs)
├── etl/          # Transformation et analyse de données
├── catalog/      # Gestion catalogue et EUROCIEL
├── finance/      # Scripts finance et trésorerie
├── restaurant/   # Scripts restaurant (seed, export)
├── _sql/         # Fichiers SQL (migrations manuelles)
├── _deprecated/  # Scripts obsolètes ou one-shot terminés
└── *.sh          # Scripts shell utilitaires
```

## Scripts principaux

### Imports (`imports/`)
| Script | Description | Usage |
|--------|-------------|-------|
| `import_lcl_pdf.py` | Import relevés LCL | Manuel |
| `import_bnp_pdf.py` | Import relevés BNP | Manuel |
| `import_sumup_pdf.py` | Import relevés SumUp | Manuel |
| `import_releves_to_db.py` | Import CSV relevés vers DB | Manuel |
| `import_vendor_*.py` | Import fournisseurs | One-shot |

### ETL (`etl/`)
| Script | Description | Usage |
|--------|-------------|-------|
| `analyze_releves.py` | Analyse des relevés bancaires | Manuel |
| `classify_finance_transactions.py` | Classification automatique transactions | Manuel |
| `generate_category_markers.py` | Génération règles catégorisation | Manuel |

### Finance (`finance/`)
| Script | Description | Usage |
|--------|-------------|-------|
| `run_finance_reconciliation.py` | Lancer rapprochement | Manuel |
| `backfill_finance.py` | Migration données vers finance_* | One-shot |
| `dedupe_finance_statements.py` | Dédoublonnage relevés | Manuel |

### Restaurant (`restaurant/`)
| Script | Description | Usage |
|--------|-------------|-------|
| `seed_restaurant_*.py` | Seed données restaurant | One-shot |
| `export_restaurant_consumptions.py` | Export consommations | Manuel |

## Scripts shell (racine)
| Script | Description |
|--------|-------------|
| `run_bank_pipeline.sh` | Pipeline complet import banque |
| `run-tests.sh` | Lancer les tests |
| `start_dev_env.sh` | Démarrer env de développement |

## Notes
- Les scripts `_deprecated/` ne doivent plus être utilisés
- Les fichiers `_sql/` contiennent des migrations SQL manuelles
