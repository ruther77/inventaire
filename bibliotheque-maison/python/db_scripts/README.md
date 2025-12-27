# DB Scripts Module

Standalone utilities and SQL assets extracted from `/home/ruuuzer/Documents/monprojet/db`.

## Contents

- `sql/` : schema, views, init scripts, and backups
- `sql/migrations/` : incremental migrations
- `sql_utils.py` : helper functions to inspect and read scripts

## Quick use

```python
from pathlib import Path
from db_scripts import collect_scripts, read_sql

base_dir = Path('sql')
manifest = collect_scripts(base_dir)
first = manifest['root'][0]
content = read_sql(base_dir / first)
```

## Notes

This module is standalone and does not depend on the application runtime.
