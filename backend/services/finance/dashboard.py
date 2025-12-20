"""Synthèse finance pour l'overview (part autre, alertes, anomalies/reco)."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import text

from core.data_repository import query_df


def dashboard_summary(entity_id: int | None = None) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    clause_entity = ""
    if entity_id is not None:
        clause_entity = "AND t.entity_id = :entity_id"
        params["entity_id"] = int(entity_id)

    # Part "frais_generaux" (ancien 'autre') et totaux - utilise finance_transactions.amount directement
    # Inclut finance_transaction_classification pour les auto-catégorisations
    part_df = query_df(
        text(
            f"""
            WITH base AS (
              SELECT
                t.direction,
                COALESCE(c.code, 'frais_generaux') AS code,
                t.amount
              FROM finance_transactions t
              LEFT JOIN finance_transaction_lines tl ON tl.transaction_id = t.id
              LEFT JOIN finance_transaction_classification tc ON tc.transaction_id = t.id
              LEFT JOIN finance_categories c ON c.id = COALESCE(tl.category_id, tc.category_id)
              WHERE t.direction IN ('IN','OUT') {clause_entity}
            )
            SELECT
              SUM(CASE WHEN direction = 'IN' THEN amount ELSE 0 END) AS inflow,
              SUM(CASE WHEN direction = 'OUT' THEN amount ELSE 0 END) AS outflow,
              SUM(amount) AS total,
              SUM(CASE WHEN code = 'frais_generaux' THEN amount ELSE 0 END) AS autre_amount,
              COUNT(*) AS lines,
              SUM(CASE WHEN code = 'frais_generaux' THEN 1 ELSE 0 END) AS autre_lines
            FROM base
            """
        ),
        params=params or None,
    )
    inflow = float(part_df.iloc[0]["inflow"] or 0) if not part_df.empty else 0.0
    outflow = float(part_df.iloc[0]["outflow"] or 0) if not part_df.empty else 0.0
    total = float(part_df.iloc[0]["total"] or 0) if not part_df.empty else 0.0
    autre_amount = float(part_df.iloc[0]["autre_amount"] or 0) if not part_df.empty else 0.0
    lines = int(part_df.iloc[0]["lines"] or 0) if not part_df.empty else 0
    autre_lines = int(part_df.iloc[0]["autre_lines"] or 0) if not part_df.empty else 0
    autre_ratio = (autre_amount / total * 100.0) if total else 0.0

    # Anomalies/matches en attente (placeholder: compter les anomalies)
    anomalies = 0
    try:
        anomalies_df = query_df(text("SELECT COUNT(*) AS cnt FROM finance_anomalies"))
        anomalies = int(anomalies_df.iloc[0]["cnt"] or 0) if not anomalies_df.empty else 0
    except Exception:
        anomalies = 0

    return {
        "inflow": inflow,
        "outflow": outflow,
        "net": inflow - outflow,
        "autre_lines": autre_lines,
        "autre_amount": autre_amount,
        "autre_ratio": autre_ratio,
        "lines": lines,
        "alerts": {
          "autre_high": autre_ratio >= 10.0,
          "anomalies": anomalies,
        },
    }
