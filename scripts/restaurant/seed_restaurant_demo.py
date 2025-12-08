"""Seed Restaurant HQ + Treasury data for demos.

Usage:
  DATABASE_URL=postgresql://... python scripts/seed_restaurant_demo.py
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DATABASE_URL", "sqlite:///demo.db")
TENANT_EPICERIE = int(os.environ.get("TENANT_EPICERIE", 1))
TENANT_RESTAURANT = int(os.environ.get("TENANT_RESTAURANT", 2))
TENANT_TRESORERIE = int(os.environ.get("TENANT_TRESORERIE", 3))

engine = create_engine(DB_URL)

categories = [
    "Frais & produits laitiers",
    "Viandes & poisson",
    "Epices & condiments",
    "Boissons",
    "Emballages",
]

fournisseurs = [
    ("Metro", None, None),
    ("GrandFrais", None, None),
    ("Biocoop", None, None),
]

ingredients = [
    ("Tomates Roma", "kg", 2.8, 35),
    ("Mozzarella fior di latte", "kg", 6.2, 18),
    ("Basilic frais", "botte", 1.2, 24),
    ("Pâte à pizza maison", "kg", 1.1, 50),
    ("Huile d'olive AOP", "L", 7.5, 12),
    ("Boeuf Charolais haché", "kg", 9.8, 20),
]

plats = [
    ("Pizza Margherita HQ", "Pizzas signature", 13.5, {
        "Tomates Roma": 0.18,
        "Mozzarella fior di latte": 0.22,
        "Basilic frais": 0.05,
        "Pâte à pizza maison": 0.28,
        "Huile d'olive AOP": 0.02,
    }),
    ("Burger Bistrot", "Street food", 15.0, {
        "Boeuf Charolais haché": 0.18,
        "Tomates Roma": 0.06,
        "Huile d'olive AOP": 0.01,
    }),
]

charges = [
    ("Loyer cuisine labo", "Structure", "Loyer", 1_200, date.today().replace(day=5)),
    ("Energie / Gaz cuisine", "Energie", "EDF", 540, date.today().replace(day=8)),
    ("Packaging livraison", "Emballages", "DS Smith", 260, date.today().replace(day=12)),
    ("Fournitures ménage", "Opérations", "Bruneau", 180, date.today().replace(day=15)),
]

bank_epicerie_account = "BP-HQ-001"

bank_sample = [
    (bank_epicerie_account, "Vente caisse week-end", 2840.50, "CREDIT"),
    (bank_epicerie_account, "Virement salaire équipe", -3200.00, "DEBIT"),
    (bank_epicerie_account, "Achat stock primeurs", -860.25, "DEBIT"),
    (bank_epicerie_account, "Encaissement Deliveroo", 1124.70, "CREDIT"),
]


with engine.begin() as conn:
    # Ensure tenants (including treasury)
    conn.execute(text("""
        INSERT INTO tenants (id, name, code)
        VALUES (:id, :name, :code)
        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
    """), [
        {"id": TENANT_EPICERIE, "name": "Épicerie HQ", "code": "epicerie"},
        {"id": TENANT_RESTAURANT, "name": "Restaurant HQ", "code": "restaurant"},
        {"id": TENANT_TRESORERIE, "name": "Trésorerie HQ", "code": "tresorerie"},
    ])

    # Clean restaurant demo data
    conn.execute(text("DELETE FROM restaurant_plat_ingredients WHERE plat_id IN (SELECT id FROM restaurant_plats WHERE tenant_id=:t)"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_plats WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_ingredients WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_depenses WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_depense_categories WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_fournisseurs WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_cost_centers WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})

    # Categories, cost centers, fournisseurs
    conn.execute(text("INSERT INTO restaurant_depense_categories (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"),
                 [{"t": TENANT_RESTAURANT, "nom": nom} for nom in categories])
    conn.execute(text("INSERT INTO restaurant_cost_centers (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"),
                 [{"t": TENANT_RESTAURANT, "nom": "Salle"}, {"t": TENANT_RESTAURANT, "nom": "Cuisine"}])
    conn.execute(text("INSERT INTO restaurant_fournisseurs (tenant_id, nom) VALUES (:t, :nom) ON CONFLICT DO NOTHING"),
                 [{"t": TENANT_RESTAURANT, "nom": f[0]} for f in fournisseurs])

    # Map ids
    cat_map = {row.nom: row.id for row in conn.execute(text("SELECT id, nom FROM restaurant_depense_categories WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})}
    cost_map = {row.nom: row.id for row in conn.execute(text("SELECT id, nom FROM restaurant_cost_centers WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})}
    four_map = {row.nom: row.id for row in conn.execute(text("SELECT id, nom FROM restaurant_fournisseurs WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})}

    # Charges
    for libelle, cat_name, fournisseur, montant_ht, d_op in charges:
        conn.execute(text("""
            INSERT INTO restaurant_depenses
            (tenant_id, categorie_id, fournisseur_id, cost_center_id, libelle, unite, quantite, prix_unitaire, montant_ht, tva_pct, date_operation, source)
            VALUES (:t, :cat, :fou, :cc, :lib, 'forfait', 1, :prix_unitaire, :montant_ht, 20.0, :date_operation, 'seed')
        """), {
            "t": TENANT_RESTAURANT,
            "cat": cat_map.get(cat_name),
            "fou": four_map.get(fournisseur),
            "cc": cost_map.get("Cuisine"),
            "lib": libelle,
            "prix_unitaire": Decimal(montant_ht),
            "montant_ht": Decimal(montant_ht),
            "date_operation": d_op,
        })

    # Ingredients
    ing_ids: dict[str, int] = {}
    for nom, unite, cout, stock in ingredients:
        result = conn.execute(text("""
            INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
            VALUES (:t, :nom, :unite, :cout, :stock)
            RETURNING id
        """), {"t": TENANT_RESTAURANT, "nom": nom, "unite": unite, "cout": Decimal(cout), "stock": Decimal(stock)})
        ing_ids[nom] = result.scalar_one()

    # Plats + associations
    for nom, cat, prix, composition in plats:
        plat_id = conn.execute(text("""
            INSERT INTO restaurant_plats (tenant_id, nom, categorie, prix_vente_ttc, actif)
            VALUES (:t, :nom, :cat, :prix, TRUE)
            RETURNING id
        """), {"t": TENANT_RESTAURANT, "nom": nom, "cat": cat, "prix": Decimal(prix)}).scalar_one()
        for ing_name, qty in composition.items():
            ing_id = ing_ids[ing_name]
            conn.execute(text("""
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:t, :plat, :ing, :qty, 'unite')
                ON CONFLICT (plat_id, ingredient_id) DO NOTHING
            """), {"t": TENANT_RESTAURANT, "plat": plat_id, "ing": ing_id, "qty": Decimal(qty)})

    # Bank statements: move epicerie -> tresorerie, clear restaurant
    conn.execute(text("DELETE FROM restaurant_bank_statements WHERE tenant_id=:t"), {"t": TENANT_RESTAURANT})
    conn.execute(text("DELETE FROM restaurant_bank_statements WHERE tenant_id=:t"), {"t": TENANT_TRESORERIE})
    # Copy from epicerie to treasury if exists
    conn.execute(text("""
        INSERT INTO restaurant_bank_statements (tenant_id, account, date, libelle, categorie, montant, type, mois, source)
        SELECT :tres, account, date, libelle, categorie, montant, type, mois, COALESCE(source,'import')
        FROM restaurant_bank_statements WHERE tenant_id=:epi
        ON CONFLICT DO NOTHING
    """), {"tres": TENANT_TRESORERIE, "epi": TENANT_EPICERIE})
    # Seed a few treasury lines if table was empty
    existing = conn.execute(text("SELECT COUNT(*) FROM restaurant_bank_statements WHERE tenant_id=:t"), {"t": TENANT_TRESORERIE}).scalar_one()
    if not existing:
        for account, libelle, montant, typ in bank_sample:
            conn.execute(text("""
                INSERT INTO restaurant_bank_statements (tenant_id, account, date, libelle, categorie, montant, type, mois, source)
                VALUES (:t, :account, CURRENT_DATE, :lib, NULL, :mnt, :typ, to_char(CURRENT_DATE, 'YYYY-MM'), 'seed')
            """), {"t": TENANT_TRESORERIE, "account": account, "lib": libelle, "mnt": Decimal(montant), "typ": typ})

print("Seed Restaurant HQ + Trésorerie effectué sur", DB_URL)
