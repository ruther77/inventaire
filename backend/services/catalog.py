from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.engine import Connection

from core.data_repository import get_engine
from core.product_service import parse_barcode_input
from core.products_loader import insert_or_update_barcode
from core.events import PriceChangedEvent, get_event_dispatcher
from core.finance.event_sourcing import emit_price_updated

LOGGER = logging.getLogger(__name__)


class CatalogServiceError(Exception):
    """Exception de base pour les opérations catalogue."""


class ProductNotFound(CatalogServiceError):
    """Levée lorsqu'un produit ne peut pas être trouvé."""


PRODUCT_COLUMNS = (
    "id, nom, tenant_id, prix_achat, prix_vente, tva, categorie, seuil_alerte, stock_actuel, actif"
)
# Version préfixée pour les JOINs
PRODUCT_COLUMNS_PREFIXED = (
    "p.id, p.nom, p.tenant_id, p.prix_achat, p.prix_vente, p.tva, p.categorie, p.seuil_alerte, p.stock_actuel, p.actif"
)


def _row_to_dict(row: Any) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, dict):
        return dict(row)
    return dict(row)


def _fetch_barcodes(conn: Connection, product_id: int, tenant_id: int) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT code
            FROM produits_barcodes
            WHERE produit_id = :pid AND tenant_id = :tenant_id
            ORDER BY code ASC
            """
        ),
        {"pid": product_id, "tenant_id": tenant_id},
    ).fetchall()
    return [str(row[0]) for row in rows]


def _derive_status(stock: float, seuil: float) -> str:
    if stock <= 0:
        return "critical"
    if seuil is None:
        return "ok"
    return "warning" if stock < seuil else "ok"


def list_products_page(
    tenant_id: int,
    *,
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    fournisseur: str | None = None,
    supplier_id: int | None = None,
    page: int = 1,
    per_page: int = 25,
) -> Tuple[list[dict[str, Any]], int]:
    page = max(1, page)
    per_page = max(1, min(per_page, 200))
    offset = (page - 1) * per_page

    params: dict[str, Any] = {"tenant_id": tenant_id}

    # Déterminer si on doit joindre avec product_suppliers
    use_supplier_join = fournisseur or supplier_id

    if use_supplier_join:
        # Requête avec JOIN sur product_suppliers
        where_clauses = ["p.tenant_id = :tenant_id"]

        if search:
            where_clauses.append("LOWER(p.nom) LIKE :search")
            params["search"] = f"%{search.lower()}%"
        if category:
            where_clauses.append("p.categorie = :category")
            params["category"] = category
        if status:
            if status == "critical":
                where_clauses.append("p.stock_actuel <= 0")
            elif status == "warning":
                where_clauses.append("(p.stock_actuel > 0 AND p.seuil_alerte > 0 AND p.stock_actuel < p.seuil_alerte)")
            elif status == "ok":
                where_clauses.append("(p.stock_actuel > 0 AND (p.seuil_alerte = 0 OR p.stock_actuel >= p.seuil_alerte))")

        if fournisseur:
            where_clauses.append("LOWER(ps.supplier_name) = LOWER(:fournisseur)")
            params["fournisseur"] = fournisseur
        if supplier_id:
            where_clauses.append("ps.supplier_id = :supplier_id")
            params["supplier_id"] = supplier_id

        where_sql = "WHERE " + " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(DISTINCT p.id)
            FROM produits p
            JOIN product_suppliers ps ON ps.product_id = p.id AND ps.tenant_id = p.tenant_id
            {where_sql}
        """

        base_sql = f"""
            SELECT DISTINCT {PRODUCT_COLUMNS_PREFIXED}, ps.supplier_name
            FROM produits p
            JOIN product_suppliers ps ON ps.product_id = p.id AND ps.tenant_id = p.tenant_id
            {where_sql}
        """
    else:
        # Requête standard sans JOIN
        where_clauses = ["tenant_id = :tenant_id"]

        if search:
            where_clauses.append("LOWER(nom) LIKE :search")
            params["search"] = f"%{search.lower()}%"
        if category:
            where_clauses.append("categorie = :category")
            params["category"] = category
        if status:
            if status == "critical":
                where_clauses.append("stock_actuel <= 0")
            elif status == "warning":
                where_clauses.append("(stock_actuel > 0 AND seuil_alerte > 0 AND stock_actuel < seuil_alerte)")
            elif status == "ok":
                where_clauses.append("(stock_actuel > 0 AND (seuil_alerte = 0 OR stock_actuel >= seuil_alerte))")

        where_sql = "WHERE " + " AND ".join(where_clauses)
        count_sql = f"SELECT COUNT(*) FROM produits {where_sql}"
        base_sql = f"SELECT {PRODUCT_COLUMNS} FROM produits {where_sql}"

    with get_engine().begin() as conn:
        count_row = conn.execute(text(count_sql), params).fetchone()
        total = int(count_row[0] if count_row else 0)

        if use_supplier_join:
            rows = conn.execute(
                text(f"{base_sql} ORDER BY p.nom LIMIT :limit OFFSET :offset"),
                {**params, "limit": per_page, "offset": offset},
            ).fetchall()
        else:
            rows = conn.execute(
                text(f"{base_sql} ORDER BY nom LIMIT :limit OFFSET :offset"),
                {**params, "limit": per_page, "offset": offset},
            ).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            record = _row_to_dict(row)
            record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
            stock = float(record.get("stock_actuel") or 0)
            seuil = record.get("seuil_alerte")
            seuil_value = float(seuil) if seuil is not None else None
            record["status"] = _derive_status(stock, seuil_value if seuil_value is not None else 0)
            results.append(record)

        return results, total


def get_product(product_id: int, tenant_id: int) -> dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(f"SELECT {PRODUCT_COLUMNS} FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row:
            raise ProductNotFound(f"Produit {product_id} introuvable.")
        record = _row_to_dict(row)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record


def create_product(
    payload: dict[str, Any],
    *,
    tenant_id: int,
    codes: Iterable[str] | None = None,
) -> dict[str, Any]:
    codes = parse_barcode_input(codes or [])
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO produits
                (nom, tenant_id, prix_achat, prix_vente, tva, categorie, seuil_alerte, stock_actuel, actif)
                VALUES (:nom, :tenant_id, :prix_achat, :prix_vente, :tva, :categorie, :seuil_alerte, :stock_actuel, :actif)
                RETURNING {cols}
                """.format(cols=PRODUCT_COLUMNS)
            ),
            {**payload, "tenant_id": tenant_id},
        ).fetchone()
        if row is None:
            raise CatalogServiceError("Échec de la création produit (aucun ID retourné).")
        record = _row_to_dict(row)
        for code in codes:
            insert_or_update_barcode(conn, int(record["id"]), code, tenant_id=tenant_id)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record


def update_product(
    product_id: int,
    changes: dict[str, Any],
    codes: Iterable[str] | None = None,
    *,
    tenant_id: int,
) -> dict[str, Any]:
    if not changes and codes is None:
        return get_product(product_id, tenant_id=tenant_id)

    set_clauses = ", ".join(f"{col} = :{col}" for col in changes.keys())
    with get_engine().begin() as conn:
        # Fetch old price before update if prix_achat is changing
        old_price = None
        product_name = None
        product_category = None
        if "prix_achat" in changes and set_clauses:
            old_row = conn.execute(
                text("SELECT prix_achat, nom, categorie FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
                {"pid": product_id, "tenant_id": tenant_id},
            ).fetchone()
            if old_row:
                old_price = float(old_row[0]) if old_row[0] is not None else None
                product_name = old_row[1]
                product_category = old_row[2]

        if set_clauses:
            params = dict(changes)
            params["pid"] = product_id
            params["tenant_id"] = tenant_id
            result = conn.execute(
                text(
                    f"UPDATE produits SET {set_clauses}, updated_at = now() WHERE id = :pid AND tenant_id = :tenant_id"
                ),
                params,
            )
            if result.rowcount == 0:
                raise ProductNotFound(f"Produit {product_id} introuvable.")

            # Emit price change event if prix_achat changed and tenant is Épicerie (tenant_id=1)
            if "prix_achat" in changes and tenant_id == 1:
                new_price = float(changes["prix_achat"])
                # Only emit if price actually changed
                if old_price is None or abs(new_price - old_price) > 0.001:
                    try:
                        event = PriceChangedEvent(
                            product_id=product_id,
                            tenant_id=tenant_id,
                            old_price=old_price,
                            new_price=new_price,
                            changed_at=datetime.now(),
                            source="api",
                            metadata={
                                "product_name": product_name,
                                "category": product_category,
                            },
                        )
                        get_event_dispatcher().publish(event)
                        LOGGER.info(
                            f"Price change event published for product {product_id}: "
                            f"{old_price} -> {new_price}"
                        )
                    except Exception as e:
                        LOGGER.error(f"Failed to publish price change event: {e}", exc_info=True)

                    # Also emit to finance event sourcing system
                    try:
                        emit_price_updated(
                            tenant_id=tenant_id,
                            product_id=product_id,
                            old_price=old_price or 0.0,
                            new_price=new_price,
                            supplier=product_category or "Catalogue",
                            source="api_update",
                        )
                    except Exception as e:
                        LOGGER.warning(f"Failed to emit price updated to event sourcing: {e}")

        if codes is not None:
            desired = set(parse_barcode_input(codes))
            existing = set(_fetch_barcodes(conn, product_id, tenant_id))

            for code in existing - desired:
                conn.execute(
                    text(
                        """
                        DELETE FROM produits_barcodes
                        WHERE produit_id = :pid AND tenant_id = :tenant_id AND lower(code) = lower(:code)
                        """
                    ),
                    {"pid": product_id, "tenant_id": tenant_id, "code": code},
                )
            for code in desired - existing:
                insert_or_update_barcode(conn, product_id, code, tenant_id=tenant_id)

        return get_product(product_id, tenant_id=tenant_id)


def delete_product(product_id: int, *, tenant_id: int) -> None:
    with get_engine().begin() as conn:
        result = conn.execute(
            text("DELETE FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": tenant_id},
        )
        if result.rowcount == 0:
            raise ProductNotFound(f"Produit {product_id} introuvable.")


def get_product_by_barcode(barcode: str, *, tenant_id: int) -> dict[str, Any]:
    normalized_codes = parse_barcode_input([barcode])
    if not normalized_codes:
        raise ProductNotFound("Code-barres invalide.")
    canonical = normalized_codes[0]

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                f"""
                SELECT {PRODUCT_COLUMNS_PREFIXED}
                FROM produits p
                JOIN produits_barcodes pb ON p.id = pb.produit_id
                WHERE pb.code = :code AND p.tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"code": canonical, "tenant_id": tenant_id},
        ).fetchone()

        if not row:
            raise ProductNotFound("Aucun produit pour ce code-barres.")

        record = _row_to_dict(row)
        record["codes"] = _fetch_barcodes(conn, int(record["id"]), tenant_id)
        return record


def list_categories(*, tenant_id: int) -> list[dict[str, Any]]:
    """Liste toutes les categories distinctes de produits."""
    with get_engine().begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT categorie as name, COUNT(*) as product_count
                FROM produits
                WHERE tenant_id = :tenant_id AND categorie IS NOT NULL AND categorie != ''
                GROUP BY categorie
                ORDER BY categorie
                """
            ),
            {"tenant_id": tenant_id},
        ).fetchall()
        return [{"name": row[0], "product_count": int(row[1])} for row in rows]


def list_vendors(*, tenant_id: int) -> list[dict[str, Any]]:
    """Liste tous les fournisseurs depuis processed_invoices ou restaurant_fournisseurs."""
    with get_engine().begin() as conn:
        # Extraire les fournisseurs des factures traitées
        rows = conn.execute(
            text(
                """
                SELECT DISTINCT supplier as name
                FROM processed_invoices
                WHERE tenant_id = :tenant_id AND supplier IS NOT NULL AND supplier != ''
                ORDER BY supplier
                """
            ),
            {"tenant_id": tenant_id},
        ).fetchall()

        if rows:
            return [{"id": idx + 1, "name": row[0]} for idx, row in enumerate(rows)]

        # Repli vers restaurant_fournisseurs si applicable
        try:
            rows = conn.execute(
                text(
                    """
                    SELECT id, nom as name
                    FROM restaurant_fournisseurs
                    WHERE tenant_id = :tenant_id
                    ORDER BY nom
                    """
                ),
                {"tenant_id": tenant_id},
            ).fetchall()
            return [{"id": row[0], "name": row[1]} for row in rows]
        except Exception:
            return []


def get_product_detail(product_id: int, *, tenant_id: int) -> dict[str, Any]:
    """Retourne un produit avec toutes ses métriques enrichies.

    Inclut:
    - Données de base du produit
    - Ventes 30j et 7j
    - Rotation stock
    - Trend stock vs semaine précédente
    - Dernier achat (date, source, prix)
    - Historique des prix récent
    - Mouvements récents
    """
    with get_engine().begin() as conn:
        # 1. Données de base du produit
        row = conn.execute(
            text(f"SELECT {PRODUCT_COLUMNS} FROM produits WHERE id = :pid AND tenant_id = :tenant_id"),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()
        if not row:
            raise ProductNotFound(f"Produit {product_id} introuvable.")

        record = _row_to_dict(row)
        record["codes"] = _fetch_barcodes(conn, product_id, tenant_id)

        # 2. Ventes (sorties) sur 30 jours et 7 jours
        sales_row = conn.execute(
            text("""
                SELECT
                    COALESCE(SUM(CASE WHEN date_mvt >= NOW() - INTERVAL '30 days' THEN quantite ELSE 0 END), 0) AS ventes_30j,
                    COALESCE(SUM(CASE WHEN date_mvt >= NOW() - INTERVAL '7 days' THEN quantite ELSE 0 END), 0) AS ventes_7j,
                    COALESCE(SUM(CASE WHEN date_mvt >= NOW() - INTERVAL '7 days' AND date_mvt < NOW() THEN quantite ELSE 0 END), 0) AS ventes_semaine_actuelle,
                    COALESCE(SUM(CASE WHEN date_mvt >= NOW() - INTERVAL '14 days' AND date_mvt < NOW() - INTERVAL '7 days' THEN quantite ELSE 0 END), 0) AS ventes_semaine_precedente
                FROM mouvements_stock
                WHERE produit_id = :pid
                  AND tenant_id = :tenant_id
                  AND type = 'SORTIE'
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()

        ventes_30j = float(sales_row[0]) if sales_row else 0
        ventes_7j = float(sales_row[1]) if sales_row else 0
        ventes_semaine_actuelle = float(sales_row[2]) if sales_row else 0
        ventes_semaine_precedente = float(sales_row[3]) if sales_row else 0

        # Calcul du trend des ventes
        if ventes_semaine_precedente > 0:
            trend_ventes_pct = ((ventes_semaine_actuelle - ventes_semaine_precedente) / ventes_semaine_precedente) * 100
        else:
            trend_ventes_pct = 100 if ventes_semaine_actuelle > 0 else 0

        record["ventes_30j"] = ventes_30j
        record["ventes_7j"] = ventes_7j
        record["trend_ventes_pct"] = round(trend_ventes_pct, 1)

        # 3. Rotation stock (sorties 30j / stock actuel moyen)
        stock_actuel = float(record.get("stock_actuel") or 0)
        if stock_actuel > 0 and ventes_30j > 0:
            # Jours de stock = stock / (ventes par jour)
            ventes_par_jour = ventes_30j / 30
            jours_de_stock = stock_actuel / ventes_par_jour if ventes_par_jour > 0 else 999
            rotation = ventes_30j / stock_actuel  # Nombre de fois que le stock tourne
        else:
            jours_de_stock = 999 if stock_actuel > 0 else 0
            rotation = 0

        record["rotation"] = round(rotation, 2)
        record["jours_de_stock"] = round(jours_de_stock, 1)

        # 4. Trend stock vs semaine précédente (basé sur les mouvements)
        stock_trend_row = conn.execute(
            text("""
                SELECT
                    COALESCE(SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE -quantite END), 0) AS variation_7j
                FROM mouvements_stock
                WHERE produit_id = :pid
                  AND tenant_id = :tenant_id
                  AND date_mvt >= NOW() - INTERVAL '7 days'
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()

        variation_7j = float(stock_trend_row[0]) if stock_trend_row else 0
        # Calculer le stock d'il y a 7 jours
        stock_il_y_a_7j = stock_actuel - variation_7j
        if stock_il_y_a_7j > 0:
            trend_stock_pct = ((stock_actuel - stock_il_y_a_7j) / stock_il_y_a_7j) * 100
        else:
            trend_stock_pct = 100 if stock_actuel > 0 else 0

        record["trend_stock_pct"] = round(trend_stock_pct, 1)
        record["stock_il_y_a_7j"] = round(stock_il_y_a_7j, 2)

        # 5. Dernier achat (dernière entrée)
        last_purchase_row = conn.execute(
            text("""
                SELECT date_mvt, source, quantite
                FROM mouvements_stock
                WHERE produit_id = :pid
                  AND tenant_id = :tenant_id
                  AND type = 'ENTREE'
                ORDER BY date_mvt DESC
                LIMIT 1
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()

        if last_purchase_row:
            record["dernier_achat"] = {
                "date": last_purchase_row[0].isoformat() if last_purchase_row[0] else None,
                "source": last_purchase_row[1],
                "quantite": float(last_purchase_row[2]) if last_purchase_row[2] else 0,
            }
        else:
            record["dernier_achat"] = None

        # 6. Historique des prix récent (5 derniers)
        price_history_rows = conn.execute(
            text("""
                SELECT prix_achat, facture_date, fournisseur
                FROM produits_price_history
                WHERE produit_id = :pid
                  AND tenant_id = :tenant_id
                ORDER BY facture_date DESC
                LIMIT 5
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchall()

        record["historique_prix"] = [
            {
                "prix": float(row[0]) if row[0] else 0,
                "date": row[1].isoformat() if row[1] else None,
                "fournisseur": row[2],
            }
            for row in price_history_rows
        ]

        # Calculer le trend des prix
        if len(price_history_rows) >= 2:
            prix_actuel = float(price_history_rows[0][0]) if price_history_rows[0][0] else 0
            prix_precedent = float(price_history_rows[1][0]) if price_history_rows[1][0] else 0
            if prix_precedent > 0:
                trend_prix_pct = ((prix_actuel - prix_precedent) / prix_precedent) * 100
            else:
                trend_prix_pct = 0
            record["trend_prix_pct"] = round(trend_prix_pct, 1)
        else:
            record["trend_prix_pct"] = 0

        # 7. Mouvements récents (10 derniers)
        movements_rows = conn.execute(
            text("""
                SELECT id, type, quantite, date_mvt, source, created_at
                FROM mouvements_stock
                WHERE produit_id = :pid
                  AND tenant_id = :tenant_id
                ORDER BY date_mvt DESC, created_at DESC
                LIMIT 10
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchall()

        record["mouvements_recents"] = [
            {
                "id": row[0],
                "type": row[1].lower() if row[1] else "sortie",
                "quantite": float(row[2]) if row[2] else 0,
                "date": row[3].isoformat() if row[3] else None,
                "source": row[4],
            }
            for row in movements_rows
        ]

        # 8. Stock max estimé (basé sur l'historique)
        max_stock_row = conn.execute(
            text("""
                WITH stock_history AS (
                    SELECT
                        date_mvt::date as jour,
                        SUM(CASE WHEN type = 'ENTREE' THEN quantite ELSE -quantite END) OVER (ORDER BY date_mvt) as running_total
                    FROM mouvements_stock
                    WHERE produit_id = :pid AND tenant_id = :tenant_id
                )
                SELECT COALESCE(MAX(running_total), :current_stock * 2) as stock_max_estime
                FROM stock_history
            """),
            {"pid": product_id, "tenant_id": tenant_id, "current_stock": stock_actuel},
        ).fetchone()

        record["stock_max"] = max(float(max_stock_row[0]) if max_stock_row and max_stock_row[0] else stock_actuel * 2, stock_actuel, 10)

        # 9. Consommations par ventes de plats (via restaurant_epicerie_sku_map)
        # Résumé par plat (quels plats utilisent ce produit)
        plat_usage_rows = conn.execute(
            text("""
                SELECT
                    rp.id as plat_id,
                    rp.nom as plat_nom,
                    ri.nom as ingredient_nom,
                    rpi.quantite as qte_par_plat,
                    map.ratio as conversion_ratio,
                    COALESCE(SUM(rs.quantity), 0) as total_plats_vendus,
                    COALESCE(SUM(rs.quantity * rpi.quantite * COALESCE(map.ratio, 1)), 0) as total_consomme
                FROM restaurant_epicerie_sku_map map
                JOIN restaurant_ingredients ri ON ri.id = map.produit_restaurant_id
                JOIN restaurant_plat_ingredients rpi ON rpi.ingredient_id = ri.id
                JOIN restaurant_plats rp ON rp.id = rpi.plat_id
                LEFT JOIN restaurant_sales rs ON rs.plat_id = rp.id AND rs.sold_at >= NOW() - INTERVAL '30 days'
                WHERE map.produit_epicerie_id = :pid
                  AND map.tenant_epicerie = :tenant_id
                GROUP BY rp.id, rp.nom, ri.nom, rpi.quantite, map.ratio
                ORDER BY total_consomme DESC
                LIMIT 10
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchall()

        record["plats_utilisant"] = [
            {
                "plat_id": row[0],
                "plat_nom": row[1],
                "ingredient_nom": row[2],
                "qte_par_plat": float(row[3]) if row[3] else 0,
                "ratio": float(row[4]) if row[4] else 1,
                "ventes_30j": float(row[5]) if row[5] else 0,
                "consomme_30j": round(float(row[6]) if row[6] else 0, 4),
            }
            for row in plat_usage_rows
        ]

        # Total consommé par les ventes de plats (30 jours)
        total_conso_row = conn.execute(
            text("""
                SELECT COALESCE(SUM(rs.quantity * rpi.quantite * COALESCE(map.ratio, 1)), 0) as total_conso_30j
                FROM restaurant_epicerie_sku_map map
                JOIN restaurant_ingredients ri ON ri.id = map.produit_restaurant_id
                JOIN restaurant_plat_ingredients rpi ON rpi.ingredient_id = ri.id
                JOIN restaurant_sales rs ON rs.plat_id = rpi.plat_id AND rs.sold_at >= NOW() - INTERVAL '30 days'
                WHERE map.produit_epicerie_id = :pid
                  AND map.tenant_epicerie = :tenant_id
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchone()

        record["conso_plats_30j"] = round(float(total_conso_row[0]) if total_conso_row and total_conso_row[0] else 0, 4)

        # 10. Dernières consommations par plats (événements récents)
        recent_conso_rows = conn.execute(
            text("""
                SELECT
                    rs.sold_at,
                    rp.nom as plat_nom,
                    rs.quantity as plats_vendus,
                    rpi.quantite as qte_par_plat,
                    map.ratio,
                    (rs.quantity * rpi.quantite * COALESCE(map.ratio, 1)) as quantite_consommee
                FROM restaurant_sales rs
                JOIN restaurant_plats rp ON rp.id = rs.plat_id
                JOIN restaurant_plat_ingredients rpi ON rpi.plat_id = rs.plat_id
                JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
                JOIN restaurant_epicerie_sku_map map ON map.produit_restaurant_id = ri.id
                WHERE map.produit_epicerie_id = :pid
                  AND map.tenant_epicerie = :tenant_id
                ORDER BY rs.sold_at DESC
                LIMIT 15
            """),
            {"pid": product_id, "tenant_id": tenant_id},
        ).fetchall()

        record["consommations_recentes"] = [
            {
                "date": row[0].isoformat() if row[0] else None,
                "plat_nom": row[1],
                "plats_vendus": float(row[2]) if row[2] else 0,
                "quantite_consommee": round(float(row[5]) if row[5] else 0, 4),
            }
            for row in recent_conso_rows
        ]

        return record
