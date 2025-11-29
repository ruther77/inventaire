BEGIN;
LOCK TABLE fact_transactions IN SHARE MODE;
LOCK TABLE fact_invoices IN SHARE MODE;
LOCK TABLE fact_sales IN SHARE MODE;

SELECT COUNT(*) AS fact_transactions_count FROM fact_transactions;
SELECT COUNT(*) AS fact_invoices_count FROM fact_invoices;
SELECT COUNT(*) AS fact_sales_count FROM fact_sales;

SELECT tenant_id, date_id, amount, direction
FROM fact_transactions
ORDER BY tenant_id, date_id
LIMIT 20;

SELECT tenant_id, date_id, supplier_id, product_id, unit_cost_excl_tax, quantity
FROM fact_invoices
ORDER BY tenant_id, date_id
LIMIT 20;

SELECT tenant_id, date_id, product_id, channel, quantity, net_amount
FROM fact_sales
ORDER BY tenant_id, date_id
LIMIT 20;

COMMIT;
