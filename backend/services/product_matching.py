"""Service de correspondance floue de produits (rapidfuzz)."""

from __future__ import annotations

import logging
from typing import Any

from rapidfuzz import fuzz, process
from sqlalchemy import text

from core.data_repository import query_df

LOGGER = logging.getLogger(__name__)


def get_fuzzy_product_matches(
    query: str,
    *,
    tenant_id: int = 1,
    max_results: int = 5,
    min_score: float = 60.0,
) -> list[dict[str, Any]]:
    """Trouve les produits correspondant à une requête via correspondance floue.

    Utilise rapidfuzz pour calculer les scores de similarité entre la requête et les noms
    des produits du catalogue. Retourne les meilleurs résultats avec leurs scores de confiance.

    Args:
        query: Nom du produit recherché
        tenant_id: ID du tenant
        max_results: Nombre maximum de résultats (par défaut : 5)
        min_score: Score minimum (0-100) à retenir (par défaut : 60.0)

    Returns:
        Liste de dictionnaires avec produits et scores, par exemple :
        [
            {
                "produit_id": int,
                "produit_nom": str,
                "categorie": str,
                "prix_achat": float,
                "prix_vente": float,
                "barcode": str,
                "score": float (0-100),
                "match_type": "fuzzy_name"
            },
            ...
        ]
    """
    if not query or not query.strip():
        return []

    normalized_query = query.strip().lower()

    # Récupérer tous les produits du catalogue
    sql = text(
        """
        SELECT
            p.id as produit_id,
            p.nom as produit_nom,
            p.categorie,
            COALESCE(p.prix_achat, 0) as prix_achat,
            COALESCE(p.prix_vente, 0) as prix_vente,
            pb.code as barcode
        FROM produits p
        LEFT JOIN LATERAL (
            SELECT code FROM produits_barcodes
            WHERE produit_id = p.id
            ORDER BY is_principal DESC, id
            LIMIT 1
        ) pb ON TRUE
        WHERE p.tenant_id = :tenant_id
          AND p.nom IS NOT NULL
          AND p.nom != ''
        ORDER BY p.nom
        """
    )

    try:
        df = query_df(sql, params={"tenant_id": int(tenant_id)})
    except Exception as exc:
        LOGGER.warning(f"Erreur lors de la récupération des produits: {exc}")
        return []

    if df.empty:
        return []

    # Préparer les noms de produits pour le matching
    product_names = []
    product_data = {}

    for _, row in df.iterrows():
        product_id = int(row["produit_id"])
        product_name = str(row["produit_nom"])
        product_name_lower = product_name.lower()

        product_names.append(product_name_lower)
        product_data[product_name_lower] = {
            "produit_id": product_id,
            "produit_nom": product_name,
            "categorie": row.get("categorie") or "",
            "prix_achat": float(row.get("prix_achat", 0)),
            "prix_vente": float(row.get("prix_vente", 0)),
            "barcode": row.get("barcode") or "",
        }

    # Utiliser rapidfuzz pour trouver les meilleurs matchs
    # Utilisation de token_sort_ratio pour gérer les mots dans un ordre différent
    matches = process.extract(
        normalized_query,
        product_names,
        scorer=fuzz.token_sort_ratio,
        limit=max_results,
    )

    results = []
    for match_name, score, _ in matches:
        if score < min_score:
            continue

        product = product_data[match_name]
        results.append(
            {
                **product,
                "score": round(score, 2),
                "match_type": "fuzzy_name",
            }
        )

    return results


def get_best_product_match(
    query: str,
    *,
    tenant_id: int = 1,
    min_score: float = 75.0,
) -> dict[str, Any] | None:
    """Retourne le meilleur match flou pour une requête produit.

    Args:
        query: Nom du produit recherché
        tenant_id: ID du tenant
        min_score: Score minimum pour considérer un match valide (par défaut : 75.0)

    Returns:
        Le dictionnaire du produit le mieux classé ou None si aucun match satisfaisant
    """
    matches = get_fuzzy_product_matches(
        query,
        tenant_id=tenant_id,
        max_results=1,
        min_score=min_score,
    )

    if matches:
        return matches[0]

    return None


def enrich_lines_with_fuzzy_matches(
    lines: list[dict[str, Any]],
    *,
    tenant_id: int = 1,
    max_suggestions: int = 3,
    min_score: float = 60.0,
) -> list[dict[str, Any]]:
    """Enrichit les lignes de facture avec des suggestions de matching flou.

    Pour les lignes sans product_id, on ajoute des suggestions issues du matching flou.

    Args:
        lines: Liste de dictionnaires représentant les lignes de facture
        tenant_id: ID du tenant
        max_suggestions: Nombre maximum de suggestions par ligne (défaut : 3)
        min_score: Seuil minimum de score (défaut : 60.0)

    Returns:
        Lignes enrichies avec le champ "fuzzy_suggestions"
    """
    enriched_lines = []

    for line in lines:
        enriched_line = line.copy()

        # Ajouter des suggestions uniquement si aucun product_id n'est renseigné
        produit_id = line.get("produit_id")
        if not produit_id or produit_id == 0:
            product_name = line.get("nom", "")
            if product_name and str(product_name).strip():
                suggestions = get_fuzzy_product_matches(
                    str(product_name),
                    tenant_id=tenant_id,
                    max_results=max_suggestions,
                    min_score=min_score,
                )
                enriched_line["fuzzy_suggestions"] = suggestions
            else:
                enriched_line["fuzzy_suggestions"] = []
        else:
            enriched_line["fuzzy_suggestions"] = []

        enriched_lines.append(enriched_line)

    return enriched_lines


__all__ = [
    "get_fuzzy_product_matches",
    "get_best_product_match",
    "enrich_lines_with_fuzzy_matches",
]
