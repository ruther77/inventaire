# Technical Notes - db_scripts

## Layout

```
db_scripts/
├── __init__.py
├── sql_utils.py
├── README.md
├── QUICKSTART.md
├── TECHNICAL.md
├── MANIFEST.md
├── examples.py
├── test_module.py
├── check_installation.py
└── sql/
    ├── 01_schema.sql
    ├── 02_restructuration_tables.sql
    ├── 02_views.sql
    ├── init.sql
    ├── migrations/
    └── epicerie_backup_*.sql
```

## Helper functions

- `find_sql_files(base_dir, recursive=False)`
- `read_sql(path)`
- `compute_checksum(path)`
- `collect_scripts(base_dir)`

These helpers keep the module independent of any database driver.
