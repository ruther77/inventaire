from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence

import math

import pandas as pd
from sqlalchemy import exc as sa_exc, text
from sqlalchemy.engine import Connection

from data_repository import get_engine

ALCOHOL_KEYWORDS = [
    "biere",
    "bière",
    "beer",
    "vin",
    "whisky",
    "rhum",
    "vodka",
    "liqueur",
    "champagne",
    "cidre",
    "tequila",
    "gin",
    "pastis",
    "cognac",
    "armagnac",
    "porto",
]

DEFAULT_MARGIN_RATE = 0.40
PRICE_DELTA_THRESHOLD = 0.10


def _empty_summary(rows_received: int = 0) -> Dict[str, Any]:
    return {
        "rows_received": rows_received,
        "rows_processed": 0,
        "created": 0,
        "updated": 0,
        "stock_initialized": 0,
        "barcode": {"added": 0, "conflicts": 0, "skipped": 0},
        "errors": [],
    }


def _to_float(value: Any, default: float | None = 0.0) -> float | None:
    if value is None:
        return default

    if isinstance(value, (int, float)):
        numeric = float(value)
        if math.isnan(numeric):
            return default
        return numeric

    if isinstance(value, str):
        cleaned = (
            value.replace("€", "")
            .replace("\xa0", "")
            .replace(",", ".")
            .strip()
        )
        if not cleaned:
            return default
        try:
            return float(cleaned)
        except ValueError:
            return default

    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def insert_or_update_barcode(conn: Connection, produit_id: int, barcode: str) -> str:
    """Insère un code-barres et renvoie *added*, *skipped* ou *conflict*."""

    normalized = str(barcode or "").strip()
    if not normalized:
        return "skipped"

    existing = conn.execute(
        text(
            """
            SELECT produit_id
            FROM produits_barcodes
            WHERE lower(code) = lower(:code)
            LIMIT 1
            """
        ),
        {"code": normalized},
    ).fetchone()

    if existing:
        return "skipped" if int(existing.produit_id) == int(produit_id) else "conflict"

    conn.execute(
        text(
            """
            INSERT INTO produits_barcodes (produit_id, code)
            VALUES (:pid, :code)
            """
        ),
        {"pid": produit_id, "code": normalized},
    )
    return "added"


def exec_sql_return_id_with_conn(conn: Connection, sql: str, params=None):
    """Exécute une requête SQL et retourne l'ID (colonne 0) en utilisant une connexion ouverte."""

    result = conn.execute(text(sql), params)
    row = result.fetchone()
    return row[0] if row else None


def determine_categorie(nom_produit: Any) -> str:
    """Détermine la catégorie à partir du nom du produit."""

    nom = str(nom_produit).upper()
    if any(k.upper() in nom for k in ALCOHOL_KEYWORDS):
        return "Alcool"
    if any(keyword in nom for keyword in ["JUS", "BOISSON", "EAU", "SODA"]):
        return "Boissons"
    if any(keyword in nom for keyword in ["HYGIENE", "SAVON", "SHAMPOOING"]):
        return "Hygiene"
    if any(keyword in nom for keyword in ["AFRIQUE", "YASSA", "TIÈB", "TIEB"]):
        return "Afrique"
    return "Autre"


def create_initial_stock(
    conn: Connection,
    produit_id: int,
    quantite: float,
    *,
    source: str = "Inventaire Initial",
) -> bool:
    """Insère un mouvement de stock positif et renvoie ``True`` s'il est créé."""

    try:
        qty = float(quantite)
    except (TypeError, ValueError):
        return False

    if qty <= 0:
        return False

    sql = text(
        """
        INSERT INTO mouvements_stock (produit_id, type, quantite, source)
        VALUES (:produit_id, 'ENTREE', :quantite, :source)
        """
    )
    conn.execute(sql, {"produit_id": produit_id, "quantite": qty, "source": source})
    return True


def _find_existing_product_by_barcode(
    conn: Connection, codes: List[str]
) -> tuple[int | None, str | None]:
    """Recherche un produit par ses codes-barres et renvoie l'ID et le code associé."""

    for code in codes:
        normalized = (code or "").strip()
        if not normalized:
            continue

        row = conn.execute(
            text(
                """
                SELECT produit_id
                FROM produits_barcodes
                WHERE lower(code) = lower(:code)
                LIMIT 1
                """
            ),
            {"code": normalized},
        ).fetchone()

        if row:
            if hasattr(row, "produit_id"):
                produit_id = getattr(row, "produit_id")
            elif isinstance(row, dict):
                produit_id = row.get("produit_id")
            else:
                produit_id = row[0]
            if produit_id is not None:
                return int(produit_id), normalized

    return None, None


def _clean_codes(raw_codes: Any) -> List[str]:
    if raw_codes is None:
        return []

    if isinstance(raw_codes, list):
        iterator = raw_codes
    else:
        iterator = str(raw_codes).replace("\n", " ").split(";")

    cleaned: List[str] = []
    for chunk in iterator:
        raw = str(chunk).replace(",", " ")
        for item in raw.split():
            code = item.strip()
            if code:
                cleaned.append(code)
    return cleaned

def _row_as_dict(row: Any, columns: Sequence[str]) -> Dict[str, Any]:
    if row is None:
        return {}
    if hasattr(row, "_mapping"):
        return dict(row._mapping)
    if isinstance(row, Mapping):
        return dict(row)

    result: Dict[str, Any] = {}
    for index, column in enumerate(columns):
        if hasattr(row, column):
            result[column] = getattr(row, column)
        else:
            try:
                result[column] = row[index]
            except (IndexError, TypeError):
                continue
    return result


def _fetch_product_snapshot(conn: Connection, produit_id: int | None) -> Dict[str, Any]:
    if produit_id in (None, ""):
        return {}
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE id = :pid
            LIMIT 1
            """
        ),
        {"pid": int(produit_id)},
    ).fetchone()
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])


def _fetch_product_by_name(conn: Connection, nom: str) -> Dict[str, Any]:
    cleaned = nom.strip()
    if not cleaned:
        return {}
    row = conn.execute(
        text(
            """
            SELECT id, prix_achat, prix_vente, categorie
            FROM produits
            WHERE lower(nom) = lower(:nom)
            LIMIT 1
            """
        ),
        {"nom": cleaned},
    ).fetchone()
    return _row_as_dict(row, ["id", "prix_achat", "prix_vente", "categorie"])


def _apply_margin(purchase: float | None, sale_candidate: float | None, *, margin: float) -> float | None:
    if purchase is None:
        return sale_candidate
    baseline = round(float(purchase) * (1.0 + margin), 2)
    if sale_candidate is None:
        return baseline
    return round(sale_candidate if sale_candidate >= baseline else baseline, 2)


def _has_significant_delta(old: Any, new: Any, *, threshold: float) -> bool:
    new_value = _to_float(new, default=None)
    if new_value is None:
        return False
    old_value = _to_float(old, default=None)
    if old_value is None or abs(old_value) < 1e-9:
        return True
    diff = abs(new_value - old_value)
    if diff < 0.01:
        return False
    return diff / abs(old_value) >= threshold


def _resolve_purchase_price(candidate: float | None, existing: Any) -> float:
    candidate_value = _to_float(candidate, default=None)
    existing_value = _to_float(existing, default=None)

    if candidate_value is None or candidate_value <= 0:
        return existing_value or 0.0
    if existing_value is None or existing_value <= 0:
        return candidate_value
    if _has_significant_delta(existing_value, candidate_value, threshold=PRICE_DELTA_THRESHOLD):
        return candidate_value
    return existing_value


def _resolve_sale_price(
    candidate_sale: float | None,
    existing_sale: Any,
    *,
    purchase_price: float,
    margin: float,
    threshold: float,
) -> float:
    baseline = _apply_margin(purchase_price, None, margin=margin) or 0.0
    target_sale = _apply_margin(purchase_price, candidate_sale, margin=margin) or baseline
    existing_value = _to_float(existing_sale, default=None)

    if existing_value is None or existing_value <= 0:
        return target_sale

    if existing_value < baseline:
        return max(target_sale, baseline)

    if _has_significant_delta(existing_value, target_sale, threshold=threshold):
        return target_sale

    return existing_value


def _resolve_category(row: Mapping[str, Any], existing: Mapping[str, Any] | None, nom: str) -> str:
    for key in ("categorie", "category", "Categorie", "CAT", "TYPE"):
        value = row.get(key) if isinstance(row, Mapping) else None
        if isinstance(value, str) and value.strip():
            return value.strip()

    if existing and existing.get("categorie"):
        existing_value = existing.get("categorie")
        if isinstance(existing_value, str) and existing_value.strip():
            return existing_value.strip()

    return determine_categorie(nom)


def load_products_from_df(df: pd.DataFrame) -> Dict[str, Any]:
    """Charge les produits à partir d'un DataFrame et retourne un résumé détaillé."""

    summary = _empty_summary(rows_received=int(len(df)))

    if df.empty:
        return summary

    engine = get_engine()
    with engine.begin() as conn:
        for idx, row in df.iterrows():
            summary["rows_processed"] += 1
            nom = str(row.get("nom", "")).strip()

            try:
                if not nom:
                    raise ValueError("Nom du produit manquant")

                raw_purchase = _to_float(row.get("prix_achat"), default=None)
                raw_sale = _to_float(row.get("prix_vente"), default=None)

                tva = _to_float(row.get("tva"), default=None)
                if tva is None:
                    raise ValueError("TVA manquante ou invalide")
                    
                seuil_alerte = _to_float(
                    row.get("seuil_alerte_defaut", row.get("seuil_alerte")),
                    default=0.0,
                ) or 0.0
                qte_init = _to_float(
                    row.get("quantite_initiale", row.get("qte_init")),
                    default=0.0,
                ) or 0.0
                codes_list = _clean_codes(row.get("codes"))

                produit_id: int | None = None
                matched_code: str | None = None
                existing_snapshot: Dict[str, Any] | None = None
                if codes_list:
                    produit_id, matched_code = _find_existing_product_by_barcode(
                        conn, codes_list
                    )
                    existing_snapshot = _fetch_product_snapshot(conn, produit_id)

                if produit_id is None:
                    snapshot_by_name = _fetch_product_by_name(conn, nom)
                    if snapshot_by_name.get("id") is not None:
                        produit_id = int(snapshot_by_name.get("id"))
                        existing_snapshot = snapshot_by_name

                categorie = _resolve_category(row, existing_snapshot, nom)

                purchase_price = _resolve_purchase_price(
                    raw_purchase, (existing_snapshot or {}).get("prix_achat")
                )
                sale_price = _resolve_sale_price(
                    raw_sale,
                    (existing_snapshot or {}).get("prix_vente"),
                    purchase_price=purchase_price,
                    margin=DEFAULT_MARGIN_RATE,
                    threshold=PRICE_DELTA_THRESHOLD,
                )

                purchase_price = round(float(purchase_price), 2) if purchase_price is not None else 0.0
                sale_price = round(float(sale_price), 2) if sale_price is not None else 0.0


                params_common = {
                    "prix_achat": purchase_price,
                    "prix_vente": sale_price,
                    "tva": tva,
                    "seuil_alerte": seuil_alerte,
                    "categorie": categorie,
                }

                created_new = False

                if produit_id is not None:
                    conn.execute(
                        text(
                            """
                            UPDATE produits
                            SET prix_achat = :prix_achat,
                                prix_vente = :prix_vente,
                                tva = :tva,
                                seuil_alerte = :seuil_alerte,
                                categorie = :categorie,
                                updated_at = now()
                            WHERE id = :pid
                            """
                        ),
                        {**params_common, "pid": produit_id},
                    )
                    summary["updated"] += 1
                else:
                    params_with_name = {"nom": nom, **params_common}
                    insert_result = conn.execute(
                        text(
                            """
                            INSERT INTO produits (nom, prix_achat, prix_vente, tva, seuil_alerte, categorie)
                            VALUES (:nom, :prix_achat, :prix_vente, :tva, :seuil_alerte, :categorie)
                            RETURNING id
                            """
                        ),
                        params_with_name,
                    )

                    inserted_row = insert_result.fetchone()
                    if inserted_row is None:
                        raise RuntimeError("Insertion du produit sans ID retourné")
                    inserted_data = _row_as_dict(inserted_row, ["id"])
                    inserted_id = inserted_data.get("id")
                    if inserted_id is None:
                        raise RuntimeError("Insertion du produit sans identifiant valide")
                    produit_id = int(inserted_id)
                    summary["created"] += 1
                    created_new = True

                movement_source = "Import facture"
                if created_new:
                    movement_source = "Import facture - création"
                elif matched_code:
                    movement_source = f"Import facture - code {matched_code}"

                if produit_id is not None and create_initial_stock(
                    conn, produit_id, qte_init, source=movement_source
                ):
                    summary["stock_initialized"] += 1

                for code in codes_list:
                    try:
                        status = insert_or_update_barcode(conn, produit_id, code)
                    except sa_exc.IntegrityError:
                        summary["barcode"]["conflicts"] += 1
                    except Exception:
                        summary["barcode"]["skipped"] += 1
                        raise
                    else:
                        if status == "added":
                            summary["barcode"]["added"] += 1
                        elif status == "conflict":
                            summary["barcode"]["conflicts"] += 1
                        else:
                            summary["barcode"]["skipped"] += 1

            except Exception as exc:
                summary["errors"].append(
                    {
                        "ligne": int(idx) + 2,  # 1-based index + header
                        "nom": nom or "<inconnu>",
                        "erreur": str(exc),
                    }
                )
    return summary


def process_products_file(csv_path: str) -> Dict[str, Any]:
    """Lit un fichier CSV puis délègue le traitement à :func:`load_products_from_df`."""

    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        summary = _empty_summary()
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": f"Fichier introuvable: {csv_path}"}
        )
        return summary
    except Exception as exc:
        summary = _empty_summary()
        summary["errors"].append(
            {"ligne": 0, "nom": "", "erreur": str(exc)}
        )
        return summary

    return load_products_from_df(df)


if __name__ == "__main__":
    import sys

    csv_path = sys.argv[1] if len(sys.argv) > 1 else "Produit.csv"
    results = process_products_file(csv_path)

    print("--- RÉSULTATS DE L'IMPORTATION ---")
    print(
        f"Total de lignes reçues : {results['rows_received']} | "
        f"Traitées : {results['rows_processed']}"
    )
    print(
        f"Produits créés : {results['created']} | "
        f"Mis à jour : {results['updated']}"
    )

    if results["errors"]:
        print(f"\n🚨 {len(results['errors'])} erreur(s) rencontrée(s) lors de l'import.")
        for error in results["errors"][:5]:
            print(f"  Ligne {error['ligne']} ({error['nom']}): {error['erreur']}")
    else:
        print("✅ Importation terminée sans erreur bloquante.")
