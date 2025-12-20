"""Service pour la gestion des vues matérialisées.

Ce module fournit des fonctions pour rafraîchir les vues matérialisées
utilisées pour les statistiques et le reporting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from sqlalchemy import text
from core.data_repository import get_engine

logger = logging.getLogger(__name__)


@dataclass
class RefreshResult:
    """Résultat du rafraîchissement d'une vue."""
    view_name: str
    status: str
    duration_ms: float
    refreshed_at: datetime


MATERIALIZED_VIEWS = [
    "mv_daily_balance",
    "mv_category_monthly",
    "mv_reconciliation_status",
    "mv_top_vendors",
    "mv_import_summary",
]


def refresh_materialized_views(concurrent: bool = True) -> List[RefreshResult]:
    """Rafraîchit toutes les vues matérialisées.

    Args:
        concurrent: Si True, utilise CONCURRENTLY pour éviter les locks.
                   Requiert un index unique sur chaque vue.

    Returns:
        Liste des résultats de rafraîchissement pour chaque vue.
    """
    results: List[RefreshResult] = []
    engine = get_engine()

    keyword = "CONCURRENTLY" if concurrent else ""

    with engine.begin() as conn:
        for view_name in MATERIALIZED_VIEWS:
            start = datetime.now()
            try:
                conn.execute(text(f"REFRESH MATERIALIZED VIEW {keyword} {view_name}"))
                duration_ms = (datetime.now() - start).total_seconds() * 1000
                results.append(RefreshResult(
                    view_name=view_name,
                    status="success",
                    duration_ms=round(duration_ms, 2),
                    refreshed_at=datetime.now(),
                ))
                logger.info(f"Vue {view_name} rafraîchie en {duration_ms:.0f}ms")
            except Exception as e:
                duration_ms = (datetime.now() - start).total_seconds() * 1000
                error_msg = str(e)
                results.append(RefreshResult(
                    view_name=view_name,
                    status=f"error: {error_msg}",
                    duration_ms=round(duration_ms, 2),
                    refreshed_at=datetime.now(),
                ))
                logger.error(f"Erreur lors du rafraîchissement de {view_name}: {error_msg}")

    return results


def refresh_single_view(view_name: str, concurrent: bool = True) -> RefreshResult:
    """Rafraîchit une seule vue matérialisée.

    Args:
        view_name: Nom de la vue à rafraîchir
        concurrent: Si True, utilise CONCURRENTLY

    Returns:
        Résultat du rafraîchissement
    """
    if view_name not in MATERIALIZED_VIEWS:
        return RefreshResult(
            view_name=view_name,
            status=f"error: Vue inconnue. Vues disponibles: {', '.join(MATERIALIZED_VIEWS)}",
            duration_ms=0,
            refreshed_at=datetime.now(),
        )

    engine = get_engine()
    keyword = "CONCURRENTLY" if concurrent else ""
    start = datetime.now()

    try:
        with engine.begin() as conn:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW {keyword} {view_name}"))
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        logger.info(f"Vue {view_name} rafraîchie en {duration_ms:.0f}ms")
        return RefreshResult(
            view_name=view_name,
            status="success",
            duration_ms=round(duration_ms, 2),
            refreshed_at=datetime.now(),
        )
    except Exception as e:
        duration_ms = (datetime.now() - start).total_seconds() * 1000
        error_msg = str(e)
        logger.error(f"Erreur lors du rafraîchissement de {view_name}: {error_msg}")
        return RefreshResult(
            view_name=view_name,
            status=f"error: {error_msg}",
            duration_ms=round(duration_ms, 2),
            refreshed_at=datetime.now(),
        )


def get_view_status() -> dict:
    """Récupère le statut de chaque vue matérialisée.

    Returns:
        Dict avec le nom de chaque vue et ses métadonnées.
    """
    engine = get_engine()
    results = {}

    with engine.connect() as conn:
        for view_name in MATERIALIZED_VIEWS:
            try:
                # Vérifier si la vue existe
                check = conn.execute(text(
                    "SELECT COUNT(*) FROM pg_matviews WHERE matviewname = :name"
                ), {"name": view_name}).scalar()

                if check == 0:
                    results[view_name] = {"exists": False, "row_count": 0}
                    continue

                # Compter les lignes
                row_count = conn.execute(text(
                    f"SELECT COUNT(*) FROM {view_name}"
                )).scalar()

                results[view_name] = {
                    "exists": True,
                    "row_count": row_count,
                }
            except Exception as e:
                results[view_name] = {
                    "exists": False,
                    "error": str(e),
                }

    return results
