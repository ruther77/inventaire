"""Seed Restaurant HQ depuis docs/restaurant/menu_seed.yaml.
Usage: DATABASE_URL=... python scripts/seed_restaurant_from_yaml.py
"""
from __future__ import annotations
import os, yaml
from decimal import Decimal
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/epicerie")
TENANT_RESTAURANT = int(os.environ.get("TENANT_RESTAURANT", 2))
TENANT_TRESORERIE = int(os.environ.get("TENANT_TRESORERIE", 3))
TENANT_EPICERIE = int(os.environ.get("TENANT_EPICERIE", 1))
SEED_FILE = os.environ.get("RESTAURANT_SEED_FILE", "docs/restaurant/menu_seed.yaml")

engine = create_engine(DB_URL)
Beverage = dict

# Catalogue boissons (simplifié) pour Restaurant HQ
BEVERAGE_ITEMS = [
    # Apéritifs / consommations
    {"nom": "Campari (conso)", "categorie": "Apéritifs", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Cognac (conso)", "categorie": "Apéritifs", "prix_vente_ttc": 7.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Martini (conso)", "categorie": "Apéritifs", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Rhum (conso)", "categorie": "Apéritifs", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Baileys (conso)", "categorie": "Apéritifs", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Coupe Veuve Clicquot", "categorie": "Champagne", "prix_vente_ttc": 10.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Coupe Moët", "categorie": "Champagne", "prix_vente_ttc": 10.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Café", "categorie": "Boissons chaudes", "prix_vente_ttc": 1.5, "tva_pct": 5.5, "actif": True},
    {"nom": "Whisky (conso)", "categorie": "Whisky", "prix_vente_ttc": 5.0, "tva_pct": 10.0, "actif": True},
    # Whiskies / spiritueux bouteilles
    {"nom": "Black Label (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 60.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Chivas (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 60.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Jack Daniel's (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 60.0, "tva_pct": 20.0, "actif": True},
    {"nom": "JB (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 50.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Baileys (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 50.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Martini (bouteille)", "categorie": "Apéritifs", "prix_vente_ttc": 45.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Glenfiddich (bouteille)", "categorie": "Whisky", "prix_vente_ttc": 80.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/2 Black Label", "categorie": "Whisky", "prix_vente_ttc": 30.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/4 Black Label", "categorie": "Whisky", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/2 Chivas", "categorie": "Whisky", "prix_vente_ttc": 30.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/4 Chivas", "categorie": "Whisky", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/2 Jack Daniel's", "categorie": "Whisky", "prix_vente_ttc": 30.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/4 Jack Daniel's", "categorie": "Whisky", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1/2 Glenfiddich", "categorie": "Whisky", "prix_vente_ttc": 40.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vodka (bouteille)", "categorie": "Spiritueux", "prix_vente_ttc": 50.0, "tva_pct": 10.0, "actif": True},
    {"nom": "1/2 Vodka", "categorie": "Spiritueux", "prix_vente_ttc": 25.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Chivas 18 ans", "categorie": "Whisky", "prix_vente_ttc": 60.0, "tva_pct": 20.0, "actif": True},
    # Vins
    {"nom": "Bordeaux", "categorie": "Vins", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Rosé", "categorie": "Vins", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vin blanc", "categorie": "Vins", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Moelleux", "categorie": "Vins", "prix_vente_ttc": 15.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Moyen vin", "categorie": "Vins", "prix_vente_ttc": 10.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Petit CD", "categorie": "Vins", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vin 25€", "categorie": "Vins", "prix_vente_ttc": 25.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vin 50€", "categorie": "Vins", "prix_vente_ttc": 50.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vin 30€", "categorie": "Vins", "prix_vente_ttc": 30.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Vin 20€", "categorie": "Vins", "prix_vente_ttc": 20.0, "tva_pct": 20.0, "actif": True},
    # Champagne
    {"nom": "Veuve Clicquot (bouteille)", "categorie": "Champagne", "prix_vente_ttc": 70.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Moët (bouteille)", "categorie": "Champagne", "prix_vente_ttc": 60.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Ruinart B2B", "categorie": "Champagne", "prix_vente_ttc": 150.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Nicola", "categorie": "Champagne", "prix_vente_ttc": 50.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Formule Champagne", "categorie": "Champagne", "prix_vente_ttc": 120.0, "tva_pct": 20.0, "actif": True},
    # Bières
    {"nom": "Heineken (petite)", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "33 Export", "categorie": "Bières", "prix_vente_ttc": 6.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Mutzig", "categorie": "Bières", "prix_vente_ttc": 6.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Guinness (grande)", "categorie": "Bières", "prix_vente_ttc": 10.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Guinness (petite)", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Castel", "categorie": "Bières", "prix_vente_ttc": 6.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Beaufort", "categorie": "Bières", "prix_vente_ttc": 6.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Pelfort (grande)", "categorie": "Bières", "prix_vente_ttc": 7.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Leffe (grande)", "categorie": "Bières", "prix_vente_ttc": 7.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Kadji Beer", "categorie": "Bières", "prix_vente_ttc": 6.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Desperados (grande)", "categorie": "Bières", "prix_vente_ttc": 8.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Desperados (petite)", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Leffe (petite)", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "1664", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Booster", "categorie": "Bières", "prix_vente_ttc": 10.0, "tva_pct": 20.0, "actif": True},
    {"nom": "Isenbeck", "categorie": "Bières", "prix_vente_ttc": 8.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Pelfort (petite)", "categorie": "Bières", "prix_vente_ttc": 5.0, "tva_pct": 10.0, "actif": True},
    # Softs
    {"nom": "Jus", "categorie": "Softs", "prix_vente_ttc": 3.0, "tva_pct": 5.5, "actif": True},
    {"nom": "Eau gazeuse", "categorie": "Softs", "prix_vente_ttc": 3.0, "tva_pct": 5.5, "actif": True},
    {"nom": "Eau", "categorie": "Softs", "prix_vente_ttc": 1.0, "tva_pct": 5.5, "actif": True},
    {"nom": "Top", "categorie": "Softs", "prix_vente_ttc": 7.0, "tva_pct": 5.5, "actif": True},
    {"nom": "Malta", "categorie": "Softs", "prix_vente_ttc": 5.0, "tva_pct": 5.5, "actif": True},
    {"nom": "Coca", "categorie": "Softs", "prix_vente_ttc": 3.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Ginger", "categorie": "Softs", "prix_vente_ttc": 5.0, "tva_pct": 10.0, "actif": True},
    {"nom": "Red Bull", "categorie": "Softs", "prix_vente_ttc": 4.0, "tva_pct": 10.0, "actif": True},
]
def main():
    data = yaml.safe_load(open(SEED_FILE, "r", encoding="utf-8"))
    ingredients = data.get("ingredients", [])
    plats = data.get("plats", []) + BEVERAGE_ITEMS
    charges = data.get("charges", [])

    with engine.begin() as conn:
        # Nettoyage restaurant
        conn.execute(text("DELETE FROM restaurant_plat_ingredients WHERE plat_id IN (SELECT id FROM restaurant_plats WHERE tenant_id=:t)"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_plats WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_ingredients WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_depenses WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_depense_categories WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_fournisseurs WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        conn.execute(text("DELETE FROM restaurant_cost_centers WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
        # Pas toucher aux bank statements ici (on conserve le mouvement epicerie->tresorerie existant)

        # Seed catégories/fournisseurs par défaut
        cat_names = {charge.get("categorie", "Charges") for charge in charges} | {plat.get("categorie", "Menus") for plat in plats}
        cat_payload = [{"t": TENANT_RESTAURANT, "nom": name} for name in cat_names if name]
        if cat_payload:
            conn.execute(text("INSERT INTO restaurant_depense_categories (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"), cat_payload)
        conn.execute(text("INSERT INTO restaurant_cost_centers (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"), [
            {"t": TENANT_RESTAURANT, "nom": "Cuisine"},
            {"t": TENANT_RESTAURANT, "nom": "Salle"},
            {"t": TENANT_RESTAURANT, "nom": "Bar"},
            {"t": TENANT_RESTAURANT, "nom": "Administratif"},
        ])
        conn.execute(text("INSERT INTO restaurant_fournisseurs (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"), [{"t": TENANT_RESTAURANT, "nom": "Fournisseur local"}])

        cat_map = {row.nom: row.id for row in conn.execute(text("SELECT id, nom FROM restaurant_depense_categories WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})}
        cc_map = {row.nom: row.id for row in conn.execute(text("SELECT id, nom FROM restaurant_cost_centers WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})}
        supplier_id = conn.execute(text("SELECT id FROM restaurant_fournisseurs WHERE tenant_id=:t LIMIT 1"), {"t": TENANT_RESTAURANT}).scalar_one()

        # Charges
        for charge in charges:
            conn.execute(text("""
                INSERT INTO restaurant_depenses (tenant_id, categorie_id, fournisseur_id, cost_center_id, libelle, unite, quantite, prix_unitaire, montant_ht, tva_pct, date_operation, source)
                VALUES (:t, :cat, :fou, :cc, :lib, 'forfait', 1, :montant, :montant, 20.0, COALESCE(:date_operation, CURRENT_DATE), 'seed')
            """), {
                "t": TENANT_RESTAURANT,
                "cat": cat_map.get(charge.get("categorie")),
                "fou": supplier_id,
                "cc": cc_map.get("Cuisine"),
                "lib": charge.get("libelle", "Charge"),
                "montant": Decimal(charge.get("montant", 0)),
                "date_operation": charge.get("date"),
            })

        # Ingrédients
        ing_ids = {}
        for ing in ingredients:
            res = conn.execute(text("""
                INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                VALUES (:t, :nom, :unite, :cout, :stock)
                RETURNING id
            """), {
                "t": TENANT_RESTAURANT,
                "nom": ing.get("nom"),
                "unite": ing.get("unite_base", "kg"),
                "cout": Decimal(str(ing.get("cout_unitaire", 0))),
                "stock": Decimal(str(ing.get("stock_actuel", 0))),
            })
            ing_ids[ing.get("nom")]= res.scalar_one()

        # Plats + BOM
        for plat in plats:
            plat_id = conn.execute(text("""
                INSERT INTO restaurant_plats (tenant_id, nom, categorie, prix_vente_ttc, actif)
                VALUES (:t, :nom, :cat, :prix, TRUE)
                RETURNING id
            """), {
                "t": TENANT_RESTAURANT,
                "nom": plat.get("nom"),
                "cat": plat.get("categorie"),
                "prix": Decimal(str(plat.get("prix_vente_ttc", 0))),
            }).scalar_one()
            # Compat composition|ingredients
            composition = plat.get("composition") or plat.get("ingredients") or []
            for item in composition:
                ing_id = ing_ids.get(item.get("ingredient"))
                if not ing_id:
                    continue
                conn.execute(text("""
                    INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                    VALUES (:t, :plat, :ing, :qty, :unite)
                    ON CONFLICT (plat_id, ingredient_id) DO NOTHING
                """), {
                    "t": TENANT_RESTAURANT,
                    "plat": plat_id,
                    "ing": ing_id,
                    "qty": Decimal(str(item.get("quantite", 0))),
                    "unite": item.get("unite", "kg"),
                })

    print(f"Seed restaurant YAML appliqué depuis {SEED_FILE} sur {DB_URL}")


if __name__ == "__main__":
    main()
