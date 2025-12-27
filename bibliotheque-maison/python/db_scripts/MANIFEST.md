# Module Manifest - db_scripts

## Structure

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
    ├── *.sql
    └── migrations/*.sql
```

## Exports

```python
collect_scripts(base_dir: Path) -> dict
find_sql_files(base_dir: Path, recursive=False) -> list[Path]
read_sql(path: Path) -> str
compute_checksum(path: Path) -> str
```

## Dependencies

Only Python standard library.
