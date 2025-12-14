"""Prévisions de consommation via ARIMA simple avec cache."""

from __future__ import annotations

from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any
import warnings

import numpy as np
import pandas as pd

from statsmodels.tsa.arima.model import ARIMA

from core.data_repository import query_df

# Cache global pour les prévisions (TTL de 5 minutes via timestamp arrondi)
_forecast_cache: dict[tuple[int, int, int], dict[int, float]] = {}


FORECAST_SQL = """
    SELECT
        m.produit_id,
        DATE(m.date_mvt) AS jour,
        SUM(CASE WHEN m.type = 'SORTIE' THEN m.quantite ELSE 0 END) AS qty_out
    FROM mouvements_stock m
    WHERE m.tenant_id = :tenant_id
      AND m.date_mvt >= :start_date
    GROUP BY m.produit_id, DATE(m.date_mvt)
"""  # Requête SQL récupérant les sorties quotidiennes par produit


def _safe_series(group: pd.DataFrame) -> pd.Series:
    series = group.set_index("jour")["qty_out"].sort_index()  # Indexe par jour et trie
    series = series.asfreq("D", fill_value=0.0)  # Force une fréquence quotidienne avec 0 pour les jours manquants
    return series  # Renvoie la série normalisée


def _forecast_series(series: pd.Series, horizon: int) -> float:
    """Calcul de prévision optimisé avec fallback sur moyenne mobile."""
    values = series.astype(float)

    # Fallback rapide pour peu de données
    if len(values) < 7:
        window = values.tail(7) if len(values) >= 1 else values
        baseline = float(window.mean()) if not window.empty else 0.0
        return max(0.0, baseline)

    # Pour les séries avec faible variance, utiliser moyenne mobile (plus rapide)
    recent = values.tail(30)
    if recent.std() < 0.1 * recent.mean() if recent.mean() > 0 else True:
        return max(0.0, float(recent.mean()))

    # ARIMA uniquement si variance significative
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(values, order=(1, 1, 0))
            fit = model.fit()
            forecast = fit.forecast(steps=horizon)
            prediction = float(np.maximum(forecast, 0).mean())
            if np.isnan(prediction):
                raise ValueError("NaN forecast")
            return prediction
    except Exception:
        window = values.tail(14)
        baseline = float(window.mean()) if not window.empty else float(values.mean())
        return max(0.0, baseline)


def forecast_daily_consumption(*, tenant_id: int = 1, horizon: int = 30) -> dict[int, float]:
    """
    Calcule les prévisions de consommation quotidienne pour chaque produit.
    Utilise un cache de 5 minutes pour éviter les recalculs fréquents.
    """
    global _forecast_cache

    # Clé de cache basée sur tenant, horizon et timestamp arrondi à 5 min
    cache_key_time = int(datetime.utcnow().timestamp()) // 300  # Arrondi à 5 min
    cache_key = (int(tenant_id), int(horizon), cache_key_time)

    # Retourner depuis le cache si disponible
    if cache_key in _forecast_cache:
        return _forecast_cache[cache_key]

    # Nettoyer les anciennes entrées du cache (garder seulement les 2 dernières périodes)
    old_keys = [k for k in _forecast_cache if k[2] < cache_key_time - 1]
    for k in old_keys:
        del _forecast_cache[k]

    start_date = datetime.utcnow() - timedelta(days=180)
    df = query_df(FORECAST_SQL, params={"tenant_id": int(tenant_id), "start_date": start_date})

    if df.empty:
        _forecast_cache[cache_key] = {}
        return {}

    df["jour"] = pd.to_datetime(df["jour"])

    # Filtrer les produits avec activité significative (au moins 5 mouvements)
    product_counts = df.groupby("produit_id").size()
    active_products = product_counts[product_counts >= 5].index

    forecasts: dict[int, float] = {}
    for product_id in active_products:
        group = df[df["produit_id"] == product_id]
        series = _safe_series(group)
        prediction = _forecast_series(series, horizon)
        if prediction > 0:
            forecasts[int(product_id)] = prediction

    _forecast_cache[cache_key] = forecasts
    return forecasts


__all__ = ["forecast_daily_consumption"]  # Exporte la fonction publique
