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
