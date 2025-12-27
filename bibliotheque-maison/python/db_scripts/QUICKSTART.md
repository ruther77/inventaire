# Quickstart - db_scripts

1) List SQL scripts

```python
from pathlib import Path
from db_scripts import collect_scripts

manifest = collect_scripts(Path('sql'))
print(manifest)
```

2) Read a SQL file

```python
from pathlib import Path
from db_scripts import read_sql

sql_text = read_sql(Path('sql/01_schema.sql'))
```
