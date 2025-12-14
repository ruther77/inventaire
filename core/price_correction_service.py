from __future__ import annotations

from typing import Iterable, Mapping, Any, Dict
from sqlalchemy import text
from core.data_repository import get_engine


def _find_product_id(conn, tenant_id: int, item: Mapping[str, Any]) -> int | None:
    pid = item.get("product_id")
    if pid:
        return int(pid)
    code = item.get("code") or item.get("code_barre")
    if not code:
        return None
    row = conn.execute(
        text(
            """
            SELECT produit_id FROM produits_barcodes
            WHERE code = :code AND tenant_id = :tenant_id
            ORDER BY is_principal DESC, id
            LIMIT 1
            """
        ),
        {"code": str(code), "tenant_id": int(tenant_id)},
    ).fetchone()
    return int(row.produit_id) if row else None


def apply_price_corrections(items: Iterable[Mapping[str, Any]], *, tenant_id: int) -> Dict[str, Any]:
    """Met à jour en masse les prix manquants (prix_achat/prix_vente/tva) sur produits."""
    engine = get_engine()
    updated = 0
    skipped: list[dict[str, Any]] = []
    with engine.begin() as conn:
        for item in items:
            pid = _find_product_id(conn, tenant_id, item)
            if not pid:
                skipped.append({"item": item, "reason": "produit_introuvable"})
                continue

            achat = item.get("prix_achat") or item.get("prix_achat_ht")
            vente = item.get("prix_vente") or item.get("prix_vente_ttc")
            tva = item.get("tva")

            if achat is None or vente is None or achat <= 0 or vente <= 0:
                skipped.append({"item": item, "reason": "prix_manquant_ou_zero"})
                continue

            conn.execute(
                text(
                    """
                    UPDATE produits
                    SET prix_achat = :achat,
                        prix_vente = :vente,
                        tva = COALESCE(:tva, tva)
                    WHERE id = :pid AND tenant_id = :tenant_id
                    """
                ),
                {"achat": achat, "vente": vente, "tva": tva, "pid": pid, "tenant_id": tenant_id},
            )
            updated += 1
    return {"updated": updated, "skipped": skipped}
