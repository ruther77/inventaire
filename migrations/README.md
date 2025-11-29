This directory was bootstrapped manually for Alembic migrations. Once the
`alembic` package is installed you can run:

```
alembic upgrade head      # apply migrations
alembic revision --autogenerate -m "message"   # create new revision
```

In this repository the initial schema from `db/init.sql` is captured in the
first revision `0001_base_schema.py`.
