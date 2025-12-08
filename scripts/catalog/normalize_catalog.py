"""
Utilitaire ponctuel pour normaliser les noms produits et codes-barres existants.

Usage :
    python -m scripts.normalize_catalog

Le script :
    * applique la même logique de nettoyage que l'import facture (_normalize_name/_normalize_barcode)
    * met à jour la table produits si le nom change
    * met à jour/supprime les codes-barres invalides et évite les doublons

⚠️ À exécuter sur une base sauvegardée : le script modifie les données en place.
"""

from __future__ import annotations

from collections import defaultdict

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from core.data_repository import get_engine
from core import products_loader


def _normalize_products(conn) -> dict[str, int]:
    stats = {"updated": 0, "duplicates": 0}
    rows = conn.execute(text("SELECT id, nom FROM produits")).fetchall()
    seen: dict[str, int] = {}
    for row in rows:
        pid = int(row.id)
        original = row.nom or ""
        normalized = products_loader._normalize_name(original)
        if not normalized:
            continue
        owner = seen.setdefault(normalized.lower(), pid)
        if owner != pid:
            stats["duplicates"] += 1
        if normalized != original:
            conn.execute(
                text("UPDATE produits SET nom = :nom, updated_at = now() WHERE id = :pid"),
                {"nom": normalized, "pid": pid},
            )
            stats["updated"] += 1
    return stats


def _normalize_barcodes(conn) -> dict[str, int]:
    stats = defaultdict(int)
    rows = conn.execute(text("SELECT id, produit_id, code FROM produits_barcodes")).fetchall()
    for row in rows:
        barcode_id = int(row.id)
        pid = int(row.produit_id)
        original = row.code or ""
        normalized = products_loader._normalize_barcode(original)
        if not normalized:
            conn.execute(text("DELETE FROM produits_barcodes WHERE id = :bid"), {"bid": barcode_id})
            stats["removed"] += 1
            continue
        if normalized == original:
            continue

        try:
            conn.execute(
                text("UPDATE produits_barcodes SET code = :code WHERE id = :bid"),
                {"code": normalized, "bid": barcode_id},
            )
            stats["updated"] += 1
        except IntegrityError:
            conn.execute(text("DELETE FROM produits_barcodes WHERE id = :bid"), {"bid": barcode_id})
            stats["deduplicated"] += 1
    return stats


def main() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        product_stats = _normalize_products(conn)
        barcode_stats = _normalize_barcodes(conn)

    print("--- Normalisation terminée ---")
    print(f"Noms produits nettoyés : {product_stats['updated']}")
    print(f"Doublons potentiels détectés (manuelle) : {product_stats['duplicates']}")
    print(
        "Codes-barres -> mis à jour: {updated}, supprimés: {removed}, dédupliqués: {deduplicated}".format(
            **{**{"updated": 0, "removed": 0, "deduplicated": 0}, **barcode_stats}
        )
    )


if __name__ == "__main__":
    main()
