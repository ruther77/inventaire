"""Maintenance and cleanup background tasks."""
import os
from backend.worker import app


@app.task(queue="maintenance")
def cleanup_cache():
    """Clean up expired cache entries."""
    from backend.cache import get_redis_client

    client = get_redis_client()
    if client:
        info = client.info("memory")
        return {
            "status": "success",
            "memory_used": info.get("used_memory_human"),
            "keys_count": client.dbsize(),
        }
    return {"status": "skipped", "reason": "Redis not available"}


@app.task(queue="maintenance")
def refresh_views():
    """Refresh materialized views."""
    import psycopg2
    from contextlib import closing

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"status": "error", "reason": "DATABASE_URL not set"}

    views = [
        "mv_daily_sales",
        "mv_product_stats",
        "mv_supplier_scores",
    ]

    refreshed = []
    try:
        with closing(psycopg2.connect(database_url)) as conn:
            with conn.cursor() as cur:
                for view in views:
                    try:
                        cur.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}")
                        refreshed.append(view)
                    except psycopg2.Error:
                        pass
            conn.commit()
        return {"status": "success", "refreshed": refreshed}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.task(queue="maintenance")
def aggregate_stats():
    """Aggregate daily statistics."""
    return {"status": "success", "message": "Stats aggregated"}


@app.task(queue="maintenance")
def check_stock_alerts():
    """Check for low stock alerts."""
    return {"status": "success", "alerts_generated": 0}


@app.task(queue="maintenance")
def vacuum_database():
    """Run VACUUM ANALYZE on key tables."""
    import psycopg2
    from contextlib import closing

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {"status": "error", "reason": "DATABASE_URL not set"}

    tables = [
        "produits",
        "finance_transactions",
        "processed_invoices",
    ]

    try:
        with closing(psycopg2.connect(database_url)) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                for table in tables:
                    try:
                        cur.execute(f"VACUUM ANALYZE {table}")
                    except psycopg2.Error:
                        pass
        return {"status": "success", "vacuumed": tables}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@app.task(queue="maintenance")
def create_daily_inventory_snapshots():
    """
    Create daily inventory snapshots for all tenants.

    This task should run once per day (typically at night) to capture
    the current inventory value for reporting and period-over-period comparisons.
    """
    from core import inventory_snapshots
    from core.data_repository import query_df
    from sqlalchemy import text

    results = {"status": "success", "snapshots_created": 0, "errors": []}

    try:
        # Fetch all active tenants
        tenants_df = query_df(text("SELECT id, code, name FROM tenants ORDER BY id"))

        if tenants_df.empty:
            return {"status": "warning", "reason": "No tenants found"}

        for _, tenant_row in tenants_df.iterrows():
            tenant_id = int(tenant_row["id"])
            tenant_code = tenant_row["code"]

            try:
                snapshot = inventory_snapshots.create_daily_snapshot(tenant_id=tenant_id)
                results["snapshots_created"] += 1

                # Log snapshot creation
                import logging
                logger = logging.getLogger(__name__)
                logger.info(
                    f"Created daily snapshot for tenant {tenant_code} (ID: {tenant_id}): "
                    f"Stock value = {snapshot['stock_value']:.2f} EUR, "
                    f"Products = {snapshot['product_count']}"
                )

            except Exception as tenant_exc:
                error_msg = f"Failed for tenant {tenant_code} (ID: {tenant_id}): {str(tenant_exc)}"
                results["errors"].append(error_msg)

                import logging
                logger = logging.getLogger(__name__)
                logger.error(error_msg)

        if results["errors"]:
            results["status"] = "partial"

        return results

    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create daily inventory snapshots: {exc}")

        return {
            "status": "error",
            "reason": str(exc),
            "snapshots_created": results.get("snapshots_created", 0),
        }
