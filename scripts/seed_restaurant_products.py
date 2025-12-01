from __future__ import annotations

from decimal import Decimal
import os
from typing import Any

from sqlalchemy import create_engine, text

# Inserts/mets à jour les produits boissons (bouteilles + portions) pour le tenant Restaurant,
# puis renseigne la table de mapping épicerie -> restaurant avec un ratio.

DB_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@db:5432/epicerie")
TENANT_RESTAURANT = int(os.environ.get("TENANT_RESTAURANT", 2))
TENANT_EPICERIE = int(os.environ.get("TENANT_EPICERIE", 1))

engine = create_engine(DB_URL)


PRODUCTS: list[dict[str, Any]] = [
    # Bières
    {"nom": "Heineken 65cl REST", "categorie": "Bieres", "prix_achat": 1.58, "prix_vente": 5.0, "code": "REST-HEI-65", "epicerie_pattern": "HEINEKEN 5D 65CL", "ratio": 1.0},
    {"nom": "1664 65cl REST", "categorie": "Bieres", "prix_achat": 1.81, "prix_vente": 5.0, "code": "REST-1664-65", "epicerie_pattern": "1664 5.5D 75CL", "ratio": 1.0},
    {"nom": "Leffe 33cl REST", "categorie": "Bieres", "prix_achat": 0.99, "prix_vente": 5.0, "code": "REST-LEF-33", "epicerie_pattern": "LEFFE BLONDE 6.6 BLE 33CL", "ratio": 1.0},
    {"nom": "Leffe 75cl REST", "categorie": "Bieres", "prix_achat": 2.56, "prix_vente": 7.0, "code": "REST-LEF-75", "epicerie_pattern": "LEFFE BLONDE 75CL", "ratio": 1.0},
    {"nom": "Guinness 33cl REST", "categorie": "Bieres", "prix_achat": 1.42, "prix_vente": 5.0, "code": "REST-GUI-33", "epicerie_pattern": "GUINNESS 7.5D 33CL", "ratio": 1.0},
    {"nom": "Desperados 33cl REST", "categorie": "Bieres", "prix_achat": 1.14, "prix_vente": 5.0, "code": "REST-DES-33", "epicerie_pattern": "DESPERADOS 5,9D 12X33CL", "ratio": 1.0},
    # Softs
    {"nom": "Coca 50cl REST", "categorie": "Softs", "prix_achat": 0.90, "prix_vente": 3.0, "code": "REST-COC-50", "epicerie_pattern": "COCA COLA PET 50CL", "ratio": 1.0},
    {"nom": "Eau 50cl REST", "categorie": "Softs", "prix_achat": 0.40, "prix_vente": 1.0, "code": "REST-EAU-50", "epicerie_pattern": None, "ratio": 1.0},
    {"nom": "Red Bull 25cl REST", "categorie": "Softs", "prix_achat": 1.02, "prix_vente": 4.0, "code": "REST-RB-25", "epicerie_pattern": "RED BULL BOITE 25CL", "ratio": 1.0},
    # Spiritueux bouteille
    {"nom": "Chivas 12 70cl REST", "categorie": "Whisky", "prix_achat": 23.88, "prix_vente": 60.0, "code": "REST-CHI-70", "epicerie_pattern": "WHISKY CHIVAS 12A 40D 70CL", "ratio": 1.0},
    {"nom": "Black Label 70cl REST", "categorie": "Whisky", "prix_achat": 20.59, "prix_vente": 60.0, "code": "REST-BL-70", "epicerie_pattern": None, "ratio": 1.0},
    {"nom": "Jack Daniel's 70cl REST", "categorie": "Whisky", "prix_achat": 15.90, "prix_vente": 60.0, "code": "REST-JD-70", "epicerie_pattern": "WH JACK DANIEL'S 40D 70CL", "ratio": 1.0},
    {"nom": "Baileys 70cl REST", "categorie": "Whisky", "prix_achat": 11.24, "prix_vente": 50.0, "code": "REST-BAI-70", "epicerie_pattern": "BAILEYS IRISH CREME", "ratio": 1.0},
    {"nom": "Campari 1L REST", "categorie": "Aperitifs", "prix_achat": 16.47, "prix_vente": 50.0, "code": "REST-CAM-1L", "epicerie_pattern": "CAMPARI 25D 1L", "ratio": 1.0},
    {"nom": "Martini Blanc 1L REST", "categorie": "Aperitifs", "prix_achat": 6.96, "prix_vente": 45.0, "code": "REST-MAR-1L", "epicerie_pattern": "MARTINI BLC 14.4D 1L", "ratio": 1.0},
    {"nom": "Cognac VS 70cl REST", "categorie": "Aperitifs", "prix_achat": 20.59, "prix_vente": 50.0, "code": "REST-COG-70", "epicerie_pattern": "COGNAC VS DELAITRE 40D 70CL", "ratio": 1.0},
    {"nom": "Vodka Absolut 70cl REST", "categorie": "Spiritueux", "prix_achat": 13.57, "prix_vente": 50.0, "code": "REST-VOD-70", "epicerie_pattern": "VODKA ABSOLUT BLUE 40D 70CL", "ratio": 1.0},
    # Champagnes / vins
    {"nom": "Veuve Clicquot 75cl REST", "categorie": "Champagne", "prix_achat": 30.0, "prix_vente": 70.0, "code": "REST-VEU-75", "epicerie_pattern": None, "ratio": 1.0},
    {"nom": "Moet Imperial 150cl REST", "categorie": "Champagne", "prix_achat": 69.0, "prix_vente": 120.0, "code": "REST-MOE-150", "epicerie_pattern": "CH MOET&CHANDON IMPERIAL 150CL", "ratio": 1.0},
    {"nom": "Chardonnay 75cl REST", "categorie": "Vins", "prix_achat": 2.25, "prix_vente": 15.0, "code": "REST-CHA-75", "epicerie_pattern": "VDF CHARD", "ratio": 1.0},
    {"nom": "Sauvignon 75cl REST", "categorie": "Vins", "prix_achat": 2.25, "prix_vente": 15.0, "code": "REST-SAU-75", "epicerie_pattern": "VDF SAUV", "ratio": 1.0},
    {"nom": "Merlot 75cl REST", "categorie": "Vins", "prix_achat": 2.15, "prix_vente": 15.0, "code": "REST-MER-75", "epicerie_pattern": "VDF RIBEAUP MERLOT", "ratio": 1.0},
    {"nom": "Mouton Cadet 75cl REST", "categorie": "Vins", "prix_achat": 0.0, "prix_vente": 30.0, "code": "REST-MOU-75", "epicerie_pattern": None, "ratio": 1.0},
    {"nom": "Talbot 75cl REST", "categorie": "Vins", "prix_achat": 0.0, "prix_vente": 50.0, "code": "REST-TAL-75", "epicerie_pattern": None, "ratio": 1.0},
    # Portions
    {"nom": "1/2 Chivas 12 REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 30.0, "code": "REST-CHI-HALF", "epicerie_pattern": "WHISKY CHIVAS 12A 40D 70CL", "ratio": 0.5},
    {"nom": "1/4 Chivas 12 REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 15.0, "code": "REST-CHI-QUART", "epicerie_pattern": "WHISKY CHIVAS 12A 40D 70CL", "ratio": 0.25},
    {"nom": "1/2 Black Label REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 30.0, "code": "REST-BL-HALF", "epicerie_pattern": None, "ratio": 0.5},
    {"nom": "1/4 Black Label REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 15.0, "code": "REST-BL-QUART", "epicerie_pattern": None, "ratio": 0.25},
    {"nom": "1/2 Jack Daniel's REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 30.0, "code": "REST-JD-HALF", "epicerie_pattern": "WH JACK DANIEL'S 40D 70CL", "ratio": 0.5},
    {"nom": "1/4 Jack Daniel's REST", "categorie": "Whisky", "prix_achat": 0.0, "prix_vente": 15.0, "code": "REST-JD-QUART", "epicerie_pattern": "WH JACK DANIEL'S 40D 70CL", "ratio": 0.25},
]


def main() -> None:
    with engine.begin() as conn:
        id_map: dict[str, int] = {}
        for item in PRODUCTS:
            res = conn.execute(
                text(
                    """
                    INSERT INTO produits (nom, tenant_id, categorie, prix_achat, prix_vente, tva, actif)
                    VALUES (:nom, :tenant, :cat, :pa, :pv, :tva, TRUE)
                    ON CONFLICT (lower(nom)) DO UPDATE
                        SET prix_achat=EXCLUDED.prix_achat,
                            prix_vente=EXCLUDED.prix_vente,
                            categorie=EXCLUDED.categorie
                    RETURNING id
                    """
                ),
                {
                    "nom": item["nom"],
                    "tenant": TENANT_RESTAURANT,
                    "cat": item.get("categorie") or "Boissons",
                    "pa": Decimal(str(item.get("prix_achat", 0) or 0)),
                    "pv": Decimal(str(item.get("prix_vente", 0) or 0)),
                    "tva": Decimal("20.0"),
                },
            )
            pid = res.scalar_one()
            id_map[item["nom"]] = pid
            conn.execute(
                text(
                    """
                    INSERT INTO produits_barcodes (produit_id, tenant_id, code, is_principal)
                    VALUES (:pid, :tenant, :code, TRUE)
                    ON CONFLICT (lower(code)) DO NOTHING
                    """
                ),
                {"pid": pid, "tenant": TENANT_RESTAURANT, "code": item.get("code") or f"REST-{pid}"},
            )

        conn.execute(
            text("DELETE FROM restaurant_epicerie_sku_map WHERE tenant_restaurant=:tr"),
            {"tr": TENANT_RESTAURANT},
        )
        for item in PRODUCTS:
            pattern = item.get("epicerie_pattern")
            if not pattern:
                continue
            row = conn.execute(
                text("SELECT id FROM produits WHERE tenant_id=:t AND nom ILIKE :pat LIMIT 1"),
                {"t": TENANT_EPICERIE, "pat": f"%{pattern}%"},
            ).fetchone()
            if not row:
                continue
            conn.execute(
                text(
                    """
                    INSERT INTO restaurant_epicerie_sku_map (tenant_restaurant, tenant_epicerie, produit_restaurant_id, produit_epicerie_id, ratio)
                    VALUES (:tr, :te, :pr, :pe, :ratio)
                    ON CONFLICT (tenant_restaurant, produit_restaurant_id) DO UPDATE
                        SET produit_epicerie_id=EXCLUDED.produit_epicerie_id,
                            ratio=EXCLUDED.ratio
                    """
                ),
                {
                    "tr": TENANT_RESTAURANT,
                    "te": TENANT_EPICERIE,
                    "pr": id_map[item["nom"]],
                    "pe": row.id,
                    "ratio": Decimal(str(item.get("ratio", 1.0))),
                },
            )

    print("Produits boissons/portions Restaurant + mapping épicerie enregistrés")


if __name__ == "__main__":
    main()
