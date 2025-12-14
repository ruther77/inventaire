-- Data Quality Scan - Nulls, placeholders, defaults, negatives, zeros, high values and duplicates
-- Usage: docker compose --env-file .env exec -T db psql -U postgres -d epicerie < scripts/data_quality_scan.sql > data_quality_report.md
\pset footer off
\pset format unaligned
\pset tuples_only on

-- Résultats agrégés
CREATE TEMP TABLE dq (
  table_name text,
  column_name text,
  issue_type text,
  pattern text,
  occurrences bigint
);

-- Exemples de valeurs (avec ids/ctid pour retrouver les lignes)
CREATE TEMP TABLE dq_examples (
  table_name text,
  column_name text,
  issue_type text,
  pattern text,
  sample_value text,
  sample_rows text,
  occurrences bigint
);

DO $$
DECLARE
  r record;
  ph text;
  cnt bigint;
  placeholders text[] := ARRAY['', 'N/A', 'NA', '?', '-', 'NONE', 'NULL', 'UNKNOWN', 'INCONNU'];
  default_dates text[] := ARRAY['1900-01-01', '1970-01-01', '0001-01-01'];
  rec record;
  pk_cols text;
  row_id_expr text;
  rel_kind text;
  ids_expr text;
BEGIN
  FOR r IN
    SELECT table_name, column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name NOT LIKE 'pg_%'
      AND table_name NOT LIKE 'sql_%'
  LOOP
    -- Identifier for examples: primary key columns if available, else ctid
    SELECT c.relkind
    INTO rel_kind
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'public' AND c.relname = r.table_name
    LIMIT 1;

    SELECT string_agg(quote_ident(a.attname), ', ')
    INTO pk_cols
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(i.indkey)
    WHERE n.nspname = 'public'
      AND c.relname = r.table_name
      AND i.indisprimary;

    IF pk_cols IS NOT NULL THEN
      row_id_expr := format('concat_ws('','', %s)', pk_cols);
    ELSIF rel_kind = 'r' THEN
      row_id_expr := 'ctid::text';
    ELSE
      row_id_expr := NULL;
    END IF;

    -- Nulls
    EXECUTE format('SELECT count(*) FROM %I.%I WHERE %I IS NULL', 'public', r.table_name, r.column_name)
      INTO cnt;
    IF cnt > 0 THEN
      INSERT INTO dq VALUES (r.table_name, r.column_name, 'NULL', 'IS NULL', cnt);
      INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'NULL', 'IS NULL', 'NULL', NULL, cnt);
    END IF;

    -- Placeholders on textual columns
    IF r.data_type IN ('text', 'character varying', 'character', 'citext') THEN
      FOREACH ph IN ARRAY placeholders LOOP
        EXECUTE format(
          'SELECT count(*) FROM %I.%I WHERE %I IS NOT NULL AND btrim(%I) ILIKE %L',
          'public', r.table_name, r.column_name, r.column_name, ph
        ) INTO cnt;
        IF cnt > 0 THEN
          INSERT INTO dq VALUES (r.table_name, r.column_name, 'PLACEHOLDER', ph, cnt);
          INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'PLACEHOLDER', ph, ph, NULL, cnt);
        END IF;
      END LOOP;
    END IF;

    -- Default dates on date/timestamp columns
    IF r.data_type IN ('date', 'timestamp without time zone', 'timestamp with time zone') THEN
      FOREACH ph IN ARRAY default_dates LOOP
        EXECUTE format(
          'SELECT count(*) FROM %I.%I WHERE %I::text LIKE %L',
          'public', r.table_name, r.column_name, ph || '%%'
        ) INTO cnt;
        IF cnt > 0 THEN
          INSERT INTO dq VALUES (r.table_name, r.column_name, 'DEFAULT_DATE', ph, cnt);
          INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'DEFAULT_DATE', ph, ph, NULL, cnt);
        END IF;
      END LOOP;
    END IF;

    -- Numeric heuristics
    IF r.data_type IN ('integer', 'bigint', 'numeric', 'double precision', 'real', 'smallint') THEN
      -- Negative values on money/qty/stock
      IF r.column_name ~* '(prix|price|montant|amount|valeur|value|cost|cout|tva|ht|ttc|quantite|qty|stock|balance|solde)' THEN
        EXECUTE format(
          'SELECT count(*) FROM %I.%I WHERE %I < 0',
          'public', r.table_name, r.column_name
        ) INTO cnt;
        IF cnt > 0 THEN
          INSERT INTO dq VALUES (r.table_name, r.column_name, 'NEGATIVE', '< 0', cnt);
          ids_expr := 'NULL';
          IF row_id_expr IS NOT NULL THEN
            ids_expr := format('string_agg(%1$s, '','' ORDER BY %1$s) FILTER (WHERE %1$s IS NOT NULL)', row_id_expr);
          END IF;
          FOR rec IN EXECUTE format(
            'SELECT %1$I::text AS val, count(*) AS c, %4$s AS ids FROM %2$I.%3$I WHERE %1$I < 0 GROUP BY %1$I ORDER BY c DESC, val',
            r.column_name, 'public', r.table_name, ids_expr
          ) LOOP
            INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'NEGATIVE', '< 0', rec.val, rec.ids, rec.c);
          END LOOP;
        END IF;
      END IF;

      -- Zero prices/amounts
      IF r.column_name ~* '(prix|price|montant|amount|valeur|value|cost|cout|tva|ht|ttc)' THEN
        EXECUTE format(
          'SELECT count(*) FROM %I.%I WHERE %I = 0',
          'public', r.table_name, r.column_name
        ) INTO cnt;
        IF cnt > 0 THEN
          INSERT INTO dq VALUES (r.table_name, r.column_name, 'ZERO', '= 0', cnt);
          ids_expr := 'NULL';
          IF row_id_expr IS NOT NULL THEN
            ids_expr := format('string_agg(%1$s, '','' ORDER BY %1$s) FILTER (WHERE %1$s IS NOT NULL)', row_id_expr);
          END IF;
          FOR rec IN EXECUTE format(
            'SELECT %1$I::text AS val, count(*) AS c, %4$s AS ids FROM %2$I.%3$I WHERE %1$I = 0 GROUP BY %1$I ORDER BY c DESC, val',
            r.column_name, 'public', r.table_name, ids_expr
          ) LOOP
            INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'ZERO', '= 0', rec.val, rec.ids, rec.c);
          END LOOP;
        END IF;
      END IF;

      -- Very large stocks/quantities
      IF r.column_name ~* '(stock|quantite|qty)' THEN
        EXECUTE format(
          'SELECT count(*) FROM %I.%I WHERE %I >= 10000',
          'public', r.table_name, r.column_name
        ) INTO cnt;
        IF cnt > 0 THEN
          INSERT INTO dq VALUES (r.table_name, r.column_name, 'HIGH_VALUE', '>= 10000', cnt);
          ids_expr := 'NULL';
          IF row_id_expr IS NOT NULL THEN
            ids_expr := format('string_agg(%1$s, '','' ORDER BY %1$s) FILTER (WHERE %1$s IS NOT NULL)', row_id_expr);
          END IF;
          FOR rec IN EXECUTE format(
            'SELECT %1$I::text AS val, count(*) AS c, %4$s AS ids FROM %2$I.%3$I WHERE %1$I >= 10000 GROUP BY %1$I ORDER BY c DESC, val',
            r.column_name, 'public', r.table_name, ids_expr
          ) LOOP
            INSERT INTO dq_examples VALUES (r.table_name, r.column_name, 'HIGH_VALUE', '>= 10000', rec.val, rec.ids, rec.c);
          END LOOP;
        END IF;
      END IF;
    END IF;
  END LOOP;
END$$;

-- Duplicate signatures (table-specific)
WITH dup AS (
  SELECT date_operation, amount, count(*) AS cnt
  FROM finance_transactions
  GROUP BY date_operation, amount
  HAVING count(*) > 1
)
INSERT INTO dq VALUES ('finance_transactions', 'date_operation+amount', 'DUPLICATE_GROUPS', 'amount+date', (SELECT count(*) FROM dup));

WITH dup AS (
  SELECT date_operation, amount, count(*) AS cnt
  FROM finance_transactions
  GROUP BY date_operation, amount
  HAVING count(*) > 1
)
INSERT INTO dq VALUES ('finance_transactions', 'date_operation+amount', 'DUPLICATE_ROWS', 'amount+date', (SELECT coalesce(sum(cnt),0) FROM dup));

INSERT INTO dq_examples
SELECT 'finance_transactions', 'date_operation+amount', 'DUPLICATE_SIGNATURE', 'amount+date',
       'date=' || date_operation || ' / amount=' || amount,
       string_agg(coalesce(id::text, ctid::text), ', ' ORDER BY coalesce(id::text, ctid::text)),
       count(*)
FROM finance_transactions
GROUP BY date_operation, amount
HAVING count(*) > 1
ORDER BY count(*) DESC, date_operation, amount;

WITH dup AS (
  SELECT date_operation, montant, count(*) AS cnt
  FROM finance_bank_statement_lines
  GROUP BY date_operation, montant
  HAVING count(*) > 1
)
INSERT INTO dq VALUES ('finance_bank_statement_lines', 'date_operation+montant', 'DUPLICATE_GROUPS', 'amount+date', (SELECT count(*) FROM dup));

WITH dup AS (
  SELECT date_operation, montant, count(*) AS cnt
  FROM finance_bank_statement_lines
  GROUP BY date_operation, montant
  HAVING count(*) > 1
)
INSERT INTO dq VALUES ('finance_bank_statement_lines', 'date_operation+montant', 'DUPLICATE_ROWS', 'amount+date', (SELECT coalesce(sum(cnt),0) FROM dup));

INSERT INTO dq_examples
SELECT 'finance_bank_statement_lines', 'date_operation+montant', 'DUPLICATE_SIGNATURE', 'amount+date',
       'date=' || date_operation || ' / amount=' || montant,
       string_agg(coalesce(id::text, ctid::text), ', ' ORDER BY coalesce(id::text, ctid::text)),
       count(*)
FROM finance_bank_statement_lines
GROUP BY date_operation, montant
HAVING count(*) > 1
ORDER BY count(*) DESC, date_operation, montant;

-- Résultat Markdown
\echo # Data Quality Scan (NULL, placeholders, defaults, negatives, zeros, high values, duplicates)
\echo
\echo '| Table | Colonne | Type | Pattern | Occurrences |'
\echo '|---|---|---|---|---|'
SELECT '| ' || table_name || ' | ' || column_name || ' | ' || issue_type || ' | ' || pattern || ' | ' || occurrences || ' |'
FROM dq
ORDER BY occurrences DESC, table_name, column_name;

\echo
\echo '## Exemples (valeurs les plus fréquentes)'
\echo
\echo '| Table | Colonne | Type | Pattern | Valeur | Rows (ids/ctid) | Occurrences |'
\echo '|---|---|---|---|---|---|---|'
SELECT '| ' || table_name || ' | ' || column_name || ' | ' || issue_type || ' | ' || pattern || ' | ' || coalesce(sample_value,'') || ' | ' || coalesce(sample_rows,'') || ' | ' || occurrences || ' |'
FROM dq_examples
ORDER BY occurrences DESC, table_name, column_name, pattern, sample_value;
