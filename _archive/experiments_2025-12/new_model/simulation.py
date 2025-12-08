from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from .model import CapitalSnapshot, Produit, RestaurantIngredient, RestaurantPlat, Tenant, aggregate_stock_value


def sample_data() -> tuple[list[Produit], list[RestaurantPlat], Tenant]:
    tenant = Tenant(id=1, code="epicerie", name="Épicerie HQ")
    sample_produits = [
        Produit(
            id=1,
            tenant=tenant,
            nom="Farine BIO",
            categorie="Basiques",
            prix_achat=Decimal("1.20"),
            prix_vente=Decimal("1.80"),
            tva=Decimal("5.5"),
            stock_actuel=Decimal("120"),
            seuil_alerte=Decimal("30"),
        ),
        Produit(
            id=2,
            tenant=tenant,
            nom="Chocolat noir 70%",
            categorie="Gourmet",
            prix_achat=Decimal("2.00"),
            prix_vente=Decimal("3.10"),
            tva=Decimal("20"),
            stock_actuel=Decimal("60"),
            seuil_alerte=Decimal("15"),
        ),
    ]

    restaurant_tenant = Tenant(id=2, code="restaurant", name="L'Incontournable")
    ingredients = [
        RestaurantIngredient(
            id=1,
            tenant=restaurant_tenant,
            nom="Farine T55",
            unite_base="kg",
            cout_unitaire=Decimal("1.30"),
            stock_actuel=Decimal("50"),
        ),
        RestaurantIngredient(
            id=2,
            tenant=restaurant_tenant,
            nom="Filet de cabillaud",
            unite_base="kg",
            cout_unitaire=Decimal("5.20"),
            stock_actuel=Decimal("25"),
        ),
    ]

    plats = [
        RestaurantPlat(
            id=1,
            tenant=restaurant_tenant,
            nom="Burger Cabillaud",
            categorie="Menu poisson",
            prix_vente_ttc=Decimal("14.50"),
            actif=True,
            ingredients=ingredients,
        )
    ]

    return sample_produits, plats, tenant


def build_snapshot(produits: list[Produit], tenant: Tenant) -> CapitalSnapshot:
    value = aggregate_stock_value(produits)
    snapshot = CapitalSnapshot(
        tenant=tenant,
        snapshot_date=datetime.utcnow(),
        stock_value=value,
        bank_balance=Decimal("3200.00"),
        cash_balance=Decimal("450.00"),
        total_assets=value + Decimal("3650.00"),
    )
    return snapshot


def main() -> None:
    produits, plats, tenant = sample_data()
    snapshot = build_snapshot(produits, tenant)
    print("Snapshot capital", snapshot)


if __name__ == "__main__":
    main()
