"""Prévisions de consommation via ARIMA simple."""  # Docstring décrivant le module de prévision

from __future__ import annotations  # Active l'évaluation différée des annotations

from datetime import datetime, timedelta  # Gestion des dates et intervalles
from decimal import Decimal  # Type décimal précis (non utilisé ici mais importé)
from typing import Any  # Typage générique (non utilisé mais disponible)

import numpy as np  # Bibliothèque numérique pour vecteurs/matrices
import pandas as pd  # Manipulation de DataFrame pour les séries temporelles
from sqlalchemy import text  # Construction de requêtes SQL textuelles

from statsmodels.tsa.arima.model import ARIMA  # Modèle ARIMA pour prévisions

from core.data_repository import query_df  # Exécution de requêtes SQL vers DataFrame


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
    values = series.astype(float)  # Convertit la série en float pour ARIMA
    if len(values) < 7:  # Cas de peu de données
        window = values.tail(7) if len(values) >= 1 else values  # Prend jusqu'à 7 derniers points si présents
        baseline = float(window.mean()) if not window.empty else 0.0  # Moyenne comme baseline ou 0
        return max(0.0, baseline)  # Renvoie baseline non négative
    try:  # Bloc principal avec ARIMA
        model = ARIMA(values, order=(1, 1, 0))  # Configure un ARIMA(1,1,0)
        fit = model.fit()  # Ajuste le modèle aux données
        forecast = fit.forecast(steps=horizon)  # Produit des prévisions sur l'horizon demandé
        prediction = float(np.maximum(forecast, 0).mean())  # Coupe à 0 et prend la moyenne
        if np.isnan(prediction):  # Détecte un résultat invalide
            raise ValueError("NaN forecast")  # Force la reprise fallback
        return prediction  # Retourne la prévision positive
    except Exception:  # Fallback en cas d'échec de l'ARIMA
        window = values.tail(14)  # Prend les 14 derniers points
        baseline = float(window.mean()) if not window.empty else float(values.mean())  # Moyenne fallback
        return max(0.0, baseline)  # Retourne baseline non négative


def forecast_daily_consumption(*, tenant_id: int = 1, horizon: int = 30) -> dict[int, float]:
    start_date = datetime.utcnow() - timedelta(days=180)  # Fenêtre de 6 mois en arrière
    df = query_df(FORECAST_SQL, params={"tenant_id": int(tenant_id), "start_date": start_date})  # Charge les mouvements
    if df.empty:  # Aucun historique
        return {}  # Renvoie un dict vide

    df["jour"] = pd.to_datetime(df["jour"])  # Convertit la colonne jour en datetime
    forecasts: dict[int, float] = {}  # Dictionnaire résultat par produit
    for product_id, group in df.groupby("produit_id"):  # Traite chaque produit séparément
        series = _safe_series(group)  # Normalise la série quotidienne
        prediction = _forecast_series(series, horizon)  # Calcule la prévision
        if prediction > 0:  # Ignore les prévisions nulles
            forecasts[int(product_id)] = prediction  # Stocke la valeur prévisionnelle
    return forecasts  # Renvoie toutes les prévisions


__all__ = ["forecast_daily_consumption"]  # Exporte la fonction publique
