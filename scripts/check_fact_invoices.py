import sys
from pathlib import Path as _Path
sys.path.append(str(_Path(__file__).resolve().parents[1]))

from sqlalchemy import text
from core.data_repository import get_engine

engine = get_engine()
with engine.begin() as conn:
    rows = conn.execute(text("SELECT tenant_id, date_id, invoice_number, quantity FROM fact_invoices ORDER BY id DESC LIMIT 5"))
    for row in rows:
        print(dict(row._mapping))
