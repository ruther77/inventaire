"""Script d’automatisation local : applique schéma + Restaurant HQ SQL/seed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.data_repository import get_engine
from core.tenant_service import ensure_tenants_table
from scripts.apply_restaurant_sql import DEFAULT_FILES, apply_sql_file
from scripts.seed_restaurant import DEFAULT_SEED_PATH, main as seed_restaurant_main


def _resolve_file(path: Path) -> Path:
    return path if path.is_absolute() else Path.cwd() / path


def _apply_sql(conn, path: Path) -> None:
    resolved = _resolve_file(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Fichier introuvable : {resolved}")
    print(f"[bootstrap-local] Application de {resolved} …")
    apply_sql_file(conn, resolved)


def _apply_schema(schema_path: Path) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        _apply_sql(conn, schema_path)


def _ensure_restaurant_prereqs(conn) -> None:
    conn.exec_driver_sql(
        """
        ALTER TABLE plat_categories
        ADD COLUMN IF NOT EXISTS categorie_id INT;

        ALTER TABLE plat_categories
        ALTER COLUMN categorie_id SET DEFAULT 2;

        CREATE OR REPLACE VIEW v_prix_unitaire_normalise AS
        SELECT i.id AS ingredient_id, 0::numeric AS prix_par_unite
        FROM ingredients i;

        CREATE OR REPLACE VIEW v_bundle_explode AS
        SELECT bi.bundle_id, b.nom AS bundle_nom,
               bi.item_plat_id, pi.nom AS item_nom, bi.quantite
        FROM bundle_items bi
        JOIN plats b  ON b.id  = bi.bundle_id   AND b.type = 'bundle'
        JOIN plats pi ON pi.id = bi.item_plat_id;

        CREATE OR REPLACE VIEW v_bundle_equivalents AS
        SELECT bi.bundle_id, e.ingredient_id,
               SUM(bi.quantite * e.qte_ingredient) AS qte_ingredient_total
        FROM bundle_items bi
        JOIN plat_equivalences e ON e.plat_id = bi.item_plat_id
        GROUP BY bi.bundle_id, e.ingredient_id;
        """
    )

def _apply_restaurant_sql(files: Iterable[Path]) -> None:
    engine = get_engine()
    for path in files:
        with engine.begin() as conn:
            _ensure_restaurant_prereqs(conn)
            try:
                _apply_sql(conn, path)
            except Exception as exc:  # pragma: no cover
                print(f"[bootstrap-local] Ignoré {path} ({exc})")


def main(
    *,
    schema_path: Path = Path("db/init.sql"),
    sql_files: Iterable[Path] = DEFAULT_FILES,
    seed_path: Path = DEFAULT_SEED_PATH,
    tenant_code: str = "restaurant",
    skip_schema: bool = False,
    skip_restaurant_sql: bool = False,
    skip_seeding: bool = False,
) -> None:
    print("[bootstrap-local] Vérification des tenants…")
    ensure_tenants_table()

    if not skip_schema:
        print("[bootstrap-local] Application du schéma principal…")
        _apply_schema(schema_path)

    if not skip_restaurant_sql:
        print("[bootstrap-local] Déploiement des fichiers Restaurant HQ…")
        _apply_restaurant_sql(sql_files)

    if not skip_seeding:
        print("[bootstrap-local] Seed des données Restaurant HQ…")
        seed_restaurant_main(seed_path, tenant_code)

    print("[bootstrap-local] Terminé.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Prépare localement la base Epicerie/Restaurant (schéma + seed)."
    )
    parser.add_argument(
        "--schema-file",
        type=Path,
        default=Path("db/init.sql"),
        help="Chemin vers le script SQL principal (défaut: db/init.sql)",
    )
    parser.add_argument(
        "--restaurant-sql",
        nargs="*",
        type=Path,
        default=list(DEFAULT_FILES),
        help="Fichiers SQL Restaurant à appliquer (ordre respecté)",
    )
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DEFAULT_SEED_PATH,
        help="Fichier YAML de seed Restaurant (défaut: docs/restaurant/menu_seed.yaml)",
    )
    parser.add_argument(
        "--tenant",
        type=str,
        default="restaurant",
        help="Code du tenant à mettre à jour (défaut: restaurant)",
    )
    parser.add_argument(
        "--skip-schema",
        action="store_true",
        help="Ne pas ré-appliquer le schéma db/init.sql",
    )
    parser.add_argument(
        "--skip-restaurant-sql",
        action="store_true",
        help="Ne pas exécuter les SQL métiers dans docs/restaurant",
    )
    parser.add_argument(
        "--skip-seed",
        action="store_true",
        help="Ne pas insérer les ingrédients/plats/charges depuis le YAML",
    )
    args = parser.parse_args()
    main(
        schema_path=args.schema_file,
        sql_files=args.restaurant_sql,
        seed_path=args.seed_file,
        tenant_code=args.tenant,
        skip_schema=args.skip_schema,
        skip_restaurant_sql=args.skip_restaurant_sql,
        skip_seeding=args.skip_seed,
    )
