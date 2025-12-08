from dataclasses import dataclass
import logging

from sqlalchemy import text

from core.data_repository import exec_sql, query_df


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


@dataclass(frozen=True)
class Mapping:
    plat_name: str
    produit_epicerie_id: int
    ratio: float
    note: str | None = None


MAPPINGS: list[Mapping] = [
    Mapping("1/2 Black Label", 407, 0.5, "Demi-portion depuis 70cl"),
    Mapping("1/2 Chivas", 239, 0.5, "Demi-portion bouteille 70cl"),
    Mapping("1/2 Glenfiddich", 1, 0.5, "Demi-portion"),
    Mapping("1/2 Jack Daniel's", 87, 0.5),
    Mapping("1/2 Vodka", 52, 0.5),
    Mapping("1/4 Black Label", 407, 0.25),
    Mapping("1/4 Chivas", 239, 0.25),
    Mapping("1/4 Jack Daniel's", 87, 0.25),
    Mapping("Baileys (bouteille)", 54, 1.0),
    Mapping("Baileys (conso)", 54, 0.08, "Verre tiré depuis le 70cl"),
    Mapping("Black Label (bouteille)", 407, 1.0),
    Mapping("Campari (conso)", 69, 0.08),
    Mapping("Chivas 18 ans", 223, 1.0),
    Mapping("Chivas (bouteille)", 239, 1.0),
    Mapping("Coca", 5, 1.0, "Bouteille 50cl vendue à 3€"),
    Mapping("Cognac (conso)", 441, 0.08),
    Mapping("Coupe Veuve Clicquot", 106, 0.12),
    Mapping("Desperados (grande)", 297, 1.0),
    Mapping("Desperados (petite)", 297, 0.5),
    Mapping("Eau", 439, 0.5),
    Mapping("Eau gazeuse", 8, 1.0),
    Mapping("Glenfiddich (bouteille)", 1, 1.0),
    Mapping("Guinness (grande)", 240, 1.0),
    Mapping("Guinness (petite)", 240, 0.5),
    Mapping("Heineken (petite)", 23, 1.0, "Plus grand format disponible (65cl)"),
    Mapping("Jack Daniel's (bouteille)", 87, 1.0),
    Mapping("JB (bouteille)", 394, 1.0),
    Mapping("Jus", 34, 1.0),
    Mapping("Leffe (grande)", 121, 1.0),
    Mapping("Leffe (petite)", 39, 0.5),
    Mapping("Martini (bouteille)", 340, 1.0),
    Mapping("Martini (conso)", 340, 0.08),
    Mapping("Moët (bouteille)", 549, 1.0),
    Mapping("Moyen vin", 326, 1.0),
    Mapping("Petit CD", 119, 1.0),
    Mapping("Red Bull", 138, 1.0),
    Mapping("Rhum (conso)", 136, 0.2),
    Mapping("Rosé", 94, 1.0),
    Mapping("Veuve Clicquot (bouteille)", 106, 1.0),
    Mapping("Vin 20€", 326, 1.0, "À bosser si tu veux un vin précis"),
    Mapping("Vin 25€", 326, 1.0),
    Mapping("Vin 30€", 326, 1.0),
    Mapping("Vin 50€", 259, 1.0),
    Mapping("Vin blanc", 326, 1.0),
    Mapping("Vodka (bouteille)", 52, 1.0),
    Mapping("Whisky (conso)", 407, 0.15),
]


INSERT_SQL = text(
    """
    INSERT INTO restaurant_epicerie_sku_map
        (tenant_restaurant, tenant_epicerie, produit_restaurant_id, produit_epicerie_id, ratio)
    VALUES (:tenant_restaurant, :tenant_epicerie, :produit_restaurant_id, :produit_epicerie_id, :ratio)
    ON CONFLICT (tenant_restaurant, produit_restaurant_id)
    DO UPDATE SET produit_epicerie_id = EXCLUDED.produit_epicerie_id, ratio = EXCLUDED.ratio
    """
)


def find_plat_id(name: str) -> int | None:
    result = query_df(
        text(
            """
            SELECT id
            FROM restaurant_plats
            WHERE tenant_id = 2
              AND LOWER(nom) = :name
            LIMIT 1
            """
        ),
        {"name": name.strip().lower()},
    )
    if result.empty:
        return None
    return int(result.iloc[0]["id"])


def seed_mappings() -> None:
    inserted = 0
    missing = []
    for mapping in MAPPINGS:
        plat_id = find_plat_id(mapping.plat_name)
        if plat_id is None:
            missing.append(mapping.plat_name)
            continue
        exec_sql(
            INSERT_SQL,
            {
                "tenant_restaurant": 2,
                "tenant_epicerie": 1,
                "produit_restaurant_id": plat_id,
                "produit_epicerie_id": mapping.produit_epicerie_id,
                "ratio": mapping.ratio,
            },
        )
        inserted += 1
        logger.info(
            "Mapped '%s' → product %s (ratio=%s)%s",
            mapping.plat_name,
            mapping.produit_epicerie_id,
            mapping.ratio,
            f" ({mapping.note})" if mapping.note else "",
        )

    logger.info("Inserted/updated %d mappings", inserted)
    if missing:
        logger.warning("Plats introuvables (vérifie les noms) : %s", ", ".join(missing))


if __name__ == "__main__":
    seed_mappings()
