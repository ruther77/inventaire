from __future__ import annotations
from typing import Any

from sqlalchemy import text

from .data_repository import query_df
from .catalog_repository import CatalogRepository, ProductSummary


class CatalogSqlRepository(CatalogRepository):
    def list_active_products(self, tenant_id: int) -> list[ProductSummary]:
        sql = text(
            """
            SELECT
                id,
                nom,
                categorie,
                COALESCE(prix_vente, 0) AS prix_vente,
                prix_achat,
                stock_actuel,
                tva
            FROM produits
            WHERE actif = TRUE AND tenant_id = :tenant_id
            ORDER BY nom ASC
            """
        )
        df = query_df(sql, params={"tenant_id": int(tenant_id)})
        if df.empty:
            return []
        return [ProductSummary(**record) for record in df.to_dict("records")]

    def find_product(self, identifier: str | int, tenant_id: int) -> ProductSummary | None:
        sql = text(
            """
            SELECT id, nom, categorie, prix_vente, prix_achat, stock_actuel, tva
            FROM produits
            WHERE tenant_id = :tenant_id AND (id = :pid OR LOWER(nom) = LOWER(:pname))
            LIMIT 1
            """
        )
        params: dict[str, Any] = {"tenant_id": int(tenant_id)}
        try:
            params["pid"] = int(identifier)
        except Exception:
            params["pid"] = -1
        params["pname"] = str(identifier)
        df = query_df(sql, params=params)
        if df.empty:
            return None
        return ProductSummary(**df.iloc[0].to_dict())
