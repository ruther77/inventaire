"""Analyse les transactions existantes pour proposer des marqueurs de catégorisation.

Parcourt finance_transactions/lines + libellés bancaires, normalise les libellés
et produit un top des occurrences avec une suggestion de catégorie (taxonomy 12 postes).

Usage :
  docker compose exec api python scripts/generate_category_markers.py --limit 200
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.data_repository import get_engine  # noqa: E402

# Taxonomie cible (12 postes)
TARGET_CATEGORIES = [
    "Achats et frais fournisseurs",
    "Salaires & rémunérations",
    "Charges sociales",
    "Impôts & taxes",
    "Frais généraux",
    "Transport & déplacement",
    "Immobilisations & investissements",
    "Loyer & immobilier",
    "Marketing & communication",
    "Frais financiers",
    "Informatique & télécom",
    "Remboursements clients & litiges",
    "Prestations externes",
]

# Heuristiques simples (mots-clés -> catégorie cible)
SUGGESTION_RULES: List[Tuple[List[str], str]] = [
    (["URSSAF", "KLESIA", "MALAKOFF", "MUTUELLE"], "Charges sociales"),
    (["SALAIRE", "PAYE", "PRIME", "INDEMNITE"], "Salaires & rémunérations"),
    (["DGFIP", "IMPOT", "CFE", "CVAE", "TAXE", "TVA"], "Impôts & taxes"),
    (["AGIOS", "FRAIS BAN", "FRAIS CB", "COMMISSION", "INTERET", "INTERETS", "TAUX"], "Frais financiers"),
    (["LOYER", "RESIDENCE", "LOCATION", "BAIL", "ST AN"], "Loyer & immobilier"),
    (["TOTAL", "ESSO", "SHELL", "AVIA", "CARBURANT", "UBER", "SNCF", "IDF", "RATP", "BOLT"], "Transport & déplacement"),
    (["SFR", "ORANGE", "FREE", "BOUYGUES", "GOOGLE", "MICROSOFT", "AZURE", "AWS", "CLOUD", "SLACK", "NOTION", "TELECOM"], "Informatique & télécom"),
    (["META", "FACEBOOK", "GOOGLE ADS", "ADS", "TIKTOK", "LINKEDIN", "MAILJET", "SENDINBLUE", "MAILCHIMP"], "Marketing & communication"),
    (["METRO", "PROMOCASH", "TRANSGOURMET", "SYSCO", "GNANAM", "EXOTI", "EUROCIEL", "RAJAPACK", "RAJA", "LYRECO", "AMAZON", "COCA", "FRANCE BOISSONS", "C10"], "Achats et frais fournisseurs"),
    (["HMD", "AUDIT", "EXPERT", "CABINET", "COMPTABLE", "PRESTATION", "SOUS-TRAITANCE", "CONSEIL"], "Prestations externes"),
    (["ASSUR", "ASSURANCE", "PACIFICA", "AXA", "ALLIANZ", "MAIF", "MATMUT"], "Frais généraux"),
    (["FACTURE", "MACHINE", "EQUIPEMENT", "MATERIEL", "AMENAGEMENT", "TRAVAUX", "ORDINATEUR", "IMPRIMANTE"], "Immobilisations & investissements"),
    (["REMBOURSEMENT", "AVOIR", "LITIGE", "SAV", "RETRO"], "Remboursements clients & litiges"),
]


def normalize_label(label: str) -> str:
    """Normalisation légère : upper + espaces condensés, mais on conserve les préfixes type CB."""
    label = (label or "").upper()
    label = re.sub(r"\s+", " ", label).strip()
    return label


def stem_label(label: str) -> str:
    """Forme tronquée pour regrouper les variantes (dates, montants, refs numériques)."""

    lab = normalize_label(label)
    # retire les dates dd/mm/yy ou dd.mm.yyyy
    lab = re.sub(r"\b\d{2}[/.]\d{2}[/.]\d{2,4}\b", "", lab)
    # retire les montants type 123,45 ou 1.234,56
    lab = re.sub(r"\b\d+[.,]\d{2}\b", "", lab)
    # retire les longues séquences numériques (>=4 chiffres)
    lab = re.sub(r"\b\d{4,}\b", "", lab)
    lab = re.sub(r"\s+", " ", lab).strip()
    return lab


def suggest_category(label: str) -> str | None:
    upper = label.upper()
    for keywords, cat in SUGGESTION_RULES:
        if any(kw in upper for kw in keywords):
            return cat
    return None


def fetch_labels(limit: int | None = None) -> Dict[Tuple[int, str, str], Dict]:
    eng = get_engine()
    sql = """
    SELECT
      t.entity_id,
      t.direction,
      COALESCE(b.libelle_banque, t.note, '') AS label
    FROM finance_transactions t
    LEFT JOIN finance_bank_statement_lines b
      ON t.ref_externe LIKE 'stmtline:%'
     AND b.id = CAST(substring(t.ref_externe FROM 'stmtline:(\\d+)') AS BIGINT)
    WHERE COALESCE(b.libelle_banque, t.note, '') <> ''
    """
    results: Dict[Tuple[int, str, str], Dict] = {}
    with eng.begin() as conn:
        rows = conn.execute(text(sql)).fetchall()
    for r in rows:
        key = normalize_label(r.label)
        k = (int(r.entity_id), str(r.direction), key)
        if k not in results:
            results[k] = {"entity_id": int(r.entity_id), "direction": str(r.direction), "label": key, "count": 0, "examples": []}
        results[k]["count"] += 1
        if len(results[k]["examples"]) < 3:
            results[k]["examples"].append(r.label)
    # Comptage par stem
    stem_counts: Dict[str, int] = defaultdict(int)
    for item in results.values():
        stem = stem_label(item["label"])
        stem_counts[stem] += item["count"]

    # Trier par count desc et tronquer si besoin
    sorted_items = sorted(results.values(), key=lambda x: x["count"], reverse=True)
    if limit is not None and limit > 0:
        sorted_items = sorted_items[:limit]
    final = {}
    for item in sorted_items:
        item["stem"] = stem_label(item["label"])
        item["stem_count"] = stem_counts.get(item["stem"], item["count"])
        final[(item["entity_id"], item["direction"], item["label"])] = item
    return final


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère un top des libellés pour créer des marqueurs de catégorisation.")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Nombre max de libellés (triés par occurrence). 0 ou négatif = tous.",
    )
    parser.add_argument("--output", type=Path, help="Chemin CSV de sortie (sinon stdout).")
    args = parser.parse_args()

    top_map = fetch_labels(limit=args.limit)
    rows = sorted(top_map.values(), key=lambda x: x["count"], reverse=True)

    output = sys.stdout
    close = False
    if args.output:
        output = args.output.open("w", newline="", encoding="utf-8")
        close = True

    writer = csv.writer(output, delimiter=";")
    writer.writerow(["entity_id", "direction", "label_normalized", "count", "stem", "stem_count", "suggested_category", "examples"])
    for item in rows:
        suggestion = suggest_category(item["label"]) or ""
        writer.writerow(
            [
                item["entity_id"],
                item["direction"],
                item["label"],
                item["count"],
                item.get("stem", ""),
                item.get("stem_count", ""),
                suggestion,
                " | ".join(item["examples"]),
            ]
        )

    if close:
        output.close()


if __name__ == "__main__":
    main()
