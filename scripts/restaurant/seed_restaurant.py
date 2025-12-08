"""Seed Restaurant HQ data (ingredients, plats, charges) from docs/restaurant/menu_seed.yaml."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable

import yaml
from sqlalchemy import text

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table


DEFAULT_SEED_PATH = Path("docs/restaurant/menu_seed.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {path}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _fetch_tenant_id(conn, code: str) -> int:
    row = conn.execute(text("SELECT id FROM tenants WHERE code = :code"), {"code": code}).fetchone()
    if not row:
        raise RuntimeError(f"Tenant '{code}' introuvable. Pensez à insérer la ligne dans la table tenants.")
    return int(row.id)


def _upsert_named_record(conn, table: str, tenant_id: int, name: str) -> int:
    row = conn.execute(
        text(
            f"""
            INSERT INTO {table} (tenant_id, nom)
            VALUES (:tenant_id, :nom)
            ON CONFLICT (tenant_id, nom)
            DO UPDATE SET nom = EXCLUDED.nom
            RETURNING id
            """
        ),
        {"tenant_id": tenant_id, "nom": name},
    ).fetchone()
    return int(row.id)


def _seed_categories(conn, tenant_id: int, charges: Iterable[dict[str, Any]]) -> None:
    for charge in charges:
        categorie = charge.get("categorie")
        center = charge.get("cost_center")
        if categorie:
            _upsert_named_record(conn, "restaurant_depense_categories", tenant_id, categorie)
        if center:
            _upsert_named_record(conn, "restaurant_cost_centers", tenant_id, center)


def _seed_charges(conn, tenant_id: int, charges: Iterable[dict[str, Any]]) -> int:
    inserted = 0
    for entry in charges:
        categorie_id = _upsert_named_record(conn, "restaurant_depense_categories", tenant_id, entry["categorie"])
        center_id = _upsert_named_record(conn, "restaurant_cost_centers", tenant_id, entry["cost_center"])
        conn.execute(
            text(
                """
                INSERT INTO restaurant_depenses (
                    tenant_id, categorie_id, cost_center_id, libelle, montant_ht, tva_pct, date_operation
                ) VALUES (
                    :tenant_id, :categorie_id, :cost_center_id, :libelle, :montant_ht, :tva_pct, :date_operation
                )
                ON CONFLICT DO NOTHING
                """
            ),
            {
                "tenant_id": tenant_id,
                "categorie_id": categorie_id,
                "cost_center_id": center_id,
                "libelle": entry["libelle"],
                "montant_ht": float(entry["montant_ht"]),
                "tva_pct": float(entry.get("tva_pct", 20)),
                "date_operation": entry.get("date_operation", date.today()),
            },
        )
        inserted += 1
    return inserted


def _seed_ingredients(conn, tenant_id: int, ingredients: Iterable[dict[str, Any]]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    for ing in ingredients:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                VALUES (:tenant_id, :nom, :unite_base, :cout_unitaire, :stock_actuel)
                ON CONFLICT (tenant_id, nom)
                DO UPDATE SET
                    unite_base = EXCLUDED.unite_base,
                    cout_unitaire = EXCLUDED.cout_unitaire,
                    stock_actuel = EXCLUDED.stock_actuel
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "nom": ing["nom"],
                "unite_base": ing.get("unite_base", "kg"),
                "cout_unitaire": float(ing.get("cout_unitaire", 0)),
                "stock_actuel": float(ing.get("stock_actuel", 0)),
            },
        ).fetchone()
        mapping[ing["nom"]] = int(row.id)
    return mapping


def _seed_plats(conn, tenant_id: int, plats: Iterable[dict[str, Any]], ingredient_ids: dict[str, int]) -> int:
    inserted = 0
    for plat in plats:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_plats (tenant_id, nom, categorie, prix_vente_ttc, actif)
                VALUES (:tenant_id, :nom, :categorie, :prix_vente_ttc, :actif)
                ON CONFLICT (tenant_id, nom)
                DO UPDATE SET categorie = EXCLUDED.categorie,
                              prix_vente_ttc = EXCLUDED.prix_vente_ttc,
                              actif = EXCLUDED.actif
                RETURNING id
                """
            ),
            {
                "tenant_id": tenant_id,
                "nom": plat["nom"],
                "categorie": plat.get("categorie"),
                "prix_vente_ttc": float(plat.get("prix_vente_ttc", 0)),
                "actif": bool(plat.get("actif", True)),
            },
        ).fetchone()
        plat_id = int(row.id)
        conn.execute(
            text("DELETE FROM restaurant_plat_ingredients WHERE tenant_id = :tenant_id AND plat_id = :plat_id"),
            {"tenant_id": tenant_id, "plat_id": plat_id},
        )
        for item in plat.get("ingredients", []):
            ingredient_name = item["ingredient"]
            ingredient_id = ingredient_ids.get(ingredient_name)
            if ingredient_id is None:
                raise RuntimeError(f"Ingrédient '{ingredient_name}' introuvable pour le plat '{plat['nom']}'.")
            conn.execute(
                text(
                    """
                    INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                    VALUES (:tenant_id, :plat_id, :ingredient_id, :quantite, :unite)
                    ON CONFLICT (plat_id, ingredient_id)
                    DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite
                    """
                ),
                {
                    "tenant_id": tenant_id,
                    "plat_id": plat_id,
                    "ingredient_id": ingredient_id,
                    "quantite": float(item.get("quantite", 0)),
                    "unite": item.get("unite"),
                },
            )
        inserted += 1
    return inserted


def main(seed_path: Path, tenant_code: str) -> None:
    payload = _load_yaml(seed_path)
    engine = get_engine()
    ensure_tenants_table()
    with engine.begin() as conn:
        tenant_id = _fetch_tenant_id(conn, tenant_code)
        charges = payload.get("charges", [])
        _seed_categories(conn, tenant_id, charges)
        ingredient_ids = _seed_ingredients(conn, tenant_id, payload.get("ingredients", []))
        plats_count = _seed_plats(conn, tenant_id, payload.get("plats", []), ingredient_ids)
        charges_count = _seed_charges(conn, tenant_id, charges)
    print(f"Tenant '{tenant_code}' mis à jour: {len(ingredient_ids)} ingrédients, {plats_count} plats, {charges_count} charges.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed Restaurant HQ depuis un fichier YAML.")
    parser.add_argument("--file", type=Path, default=DEFAULT_SEED_PATH, help="Chemin du fichier YAML (défaut: docs/restaurant/menu_seed.yaml)")
    parser.add_argument("--tenant", type=str, default="restaurant", help="Code du tenant à alimenter")
    args = parser.parse_args()
    main(args.file, args.tenant)
