"""Services pour les modules restaurant (charges, ingrédients, plats)."""

from __future__ import annotations

import io
import math
import re
from collections import defaultdict, OrderedDict
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from sqlalchemy import text

from pypdf import PdfReader

from backend.services.catalog_data import fetch_customer_catalog
from core.data_repository import get_engine, query_df
from core.inventory_forecast import forecast_daily_consumption
from core.vendor_categories import load_vendor_category_rules
from core import restaurant_costs
from core.data_repository import exec_sql, exec_sql_return_id  # type: ignore


def _safe_float(value: Any) -> float:
    """Convertit prudemment une valeur en float sans lever d'exception."""

    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


TRANSACTION_LINE_RE = re.compile(
    r'^(?P<op>\d{2}\.\d{2})\s+(?P<val>\d{2}\.\d{2}\.\d{2})\s+(?P<body>.+)$'
)
AMOUNT_RE = re.compile(r'(\d[\d\s]*,\d{2})')
CREDIT_KEYWORDS = [
    "VERSEMENT",
    "REMISE",
    "DEPOT",
    "BRUT",
]
DEBIT_KEYWORDS = [
    "PRLV",
    "VIR",
    "TRAIT",
    "CB ",
    "CB",
    "ABON",
    "LOYER",
    "URSSAF",
    "ENGIE",
    "SFR",
    "CANAL",
]
IGNORED_PREFIXES = (
    "PAGE ",
    "ECRITURES DE LA PERIODE",
    "DATE LIBELLE VALEUR",
    "ANCIEN SOLDE",
    "SOLDE INTERMEDIAIRE",
    "Titulaire du compte",
    "Votreconseiller",
    "Crédit Lyonnais",
    "RELEVE D'IDENTITE",
)
IGNORED_PREFIXES_UPPER = tuple(prefix.upper() for prefix in IGNORED_PREFIXES)


def _normalize_amount(raw: str) -> float:
    """Transforme une chaîne `1 234,56` en float Python."""

    return _safe_float(raw.replace(" ", "").replace(",", "."))


HEADER_START_PREFIXES = (
    "PRLV",
    "VIR",
    "VIREMENT",
    "VERSEMENT",
    "VERSEMENTS",
    "REMISE",
    "REM CB",
    "CB",
    "CHEQUE",
    "CHQ",
    "DEPOT",
    "DEBLOC",
    "DEBLOCSUR",
    "DEBLOC SUR",
    "FRAIS",
    "AGIOS",
    "PAIEMENT",
    "PREFILOC",
    "LOYER",
    "RESIDENCE",
    "METRO",
    "GNANAM",
    "NOUTAM",
    "ENGIE",
    "GAZ",
    "GAZELENERGIE",
    "SFR",
    "CANAL",
    "ASSURANCE",
    "AVEM",
    "SPB",
    "URSSAF",
    "KLESIA",
    "HMD",
    "FACTURE",
    "INT",
    "AVIS",
    "SALAIRE",
)

DETAIL_PREFIXES = (
    "LIBELLE",
    "REF",
    "ID",
    "BRUT",
    "COM",
    "PCE",
    "REG",
    "N°",
    "NO",
    "NUMÉRO",
    "NUMERO",
    "BIC",
    "IBAN",
    "CLIENT",
    "RIB",
    "DUPLICATA",
    "COTIS",
    "HEANCE",
)

STOP_PREFIXES = tuple(
    s.upper()
    for s in (
        "PAGE",
        "ECRITURES",
        "DATE LIBELLE",
        "ANCIEN SOLDE",
        "SOLDE INTERMEDIAIRE",
        "TITULAIRE DU COMPTE",
        "VOTRECONSEILLER",
        "CRÉDIT",
        "CREDIT",
        "RELEVE",
        "L INCONTOURNABLE",
        "DOMICILIATION",
        "RÉFÉRENCES",
        "REFERENCES",
        "PRENEZ",
        "IBAN",
        "BIC",
        "BETTY",
        "COMPTE :",
    )
)

CATEGORY_RULES: tuple[tuple[tuple[str, ...], str, tuple[str, ...] | None], ...] = (
    (("VERSEMENT ALS",), "Encaissement", ("Entrée",)),
    (("REMISE CB", "REM CB", "CB NO", "CB ", "CARTE"), "Encaissement", ("Entrée",)),
    (("CB12",), "Encaissement", ("Entrée",)),
    (("DEPOT", "VIR RECU", "VERSEMENT", "REMISE CHEQUE", "ALIMENTATION"), "Encaissement", ("Entrée",)),
    (("LYDIA", "PAYLIB"), "Encaissement mobile", ("Entrée",)),
    (("STRIPE", "SUMUP", "ZETTLE", "PAYPAL"), "Frais d'encaissement", ("Sortie",)),
    (("SALAIRE", "PAYE"), "Salaires", ("Sortie",)),
    (("URSSAF",), "Charges sociales", ("Sortie",)),
    (("AGIRC", "ARRCO", "MALAKOFF", "KLESIA", "HUMANIS"), "Retraite / Prévoyance", ("Sortie",)),
    (("DGFIP", "IMPOTS", "TVA", "CFE", "CET"), "Fiscalité", ("Sortie",)),
    (("TOTALENERGIES", "TOTAL", "TOTAL ENERGIES", "TEF"), "Énergie", ("Sortie",)),
    (("TOTALENERGIES CHARGING", "DIGITAL CHARGING", "CHARGING"), "Carburant / Déplacements", ("Sortie",)),
    (("EDF", "E.D.F."), "Énergie", ("Sortie",)),
    (("ENGIE", "GAZ DE FRANCE"), "Énergie", ("Sortie",)),
    (("GAZEL", "GAZELENERGIE"), "Énergie", ("Sortie",)),
    (("ENI", "ILEK", "PLANETE OUI", "MINT ENERGIE"), "Énergie", ("Sortie",)),
    (("EAU DE PARIS", "VEOLIA EAU", "SUEZ EAU", "SAUR"), "Eau", ("Sortie",)),
    (("RESIDENCE", "LOYER", "LOCATION", "LOCAT", "ST AN"), "Loyer/Location", ("Sortie",)),
    (("FREE", "FREE PRO"), "Télécom", ("Sortie",)),
    (("SFR", "SFR BUSINESS"), "Télécom", ("Sortie",)),
    (("ORANGE", "ORANGE PRO"), "Télécom", ("Sortie",)),
    (("BOUYGUES", "BBOX", "BYTEL"), "Télécom", ("Sortie",)),
    (("CANAL", "CANALSAT"), "Abonnements TV", ("Sortie",)),
    (("NETFLIX", "SPOTIFY", "ABONNEMENT"), "Abonnements", ("Sortie",)),
    (
        (
            "SPB",
            "PACIFICA",
            "CREDIT AGRICOLE ASSURANCE",
            "AXA",
            "ALLIANZ",
            "MAIF",
            "MAAF",
            "MATMUT",
            "HISCOX",
            "ASSURANCE LCL",
        ),
        "Assurance",
        ("Sortie",),
    ),
    (("HMD", "AUDIT", "EXPERT COMPTABLE", "CABINET COMPTABLE", "HMD AUDIT ET CONSEIL"), "Comptabilité", ("Sortie",)),
    (
        (
            "METRO",
            "PROMOCASH",
            "TRANS GOURMET",
            "TRANSGOURMET",
            "DAVIGEL",
            "SYSCO",
            "BOUCH. BVS",
            "BOUCH BVS",
            "BOUCH",
            "GNANAM",
            "EXOTI",
            "EUROCIEL",
            "KEDY PACK",
            "TAI YAT",
            "RETRAIT",
            "LINCONTOURNABLE",
            "LEADER PRICE",
            "LE VINCI",
        ),
        "Approvisionnement",
        ("Sortie",),
    ),
    (("CENTRAKOR",), "Fournitures / Matériel", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Crédit", ("Sortie",)),
    (("AVEM", "LOCATION TPE", "TPE AVEM"), "Frais d'encaissement", ("Sortie",)),
    (("FRANCE BOISSONS", "C10", "COCA", "COCA COLA", "COCA-COLA", "HEINEKEN FRANCE", "LES GRANDS CHAIS", "CASTEL FRERES"), "Boissons", ("Sortie",)),
    (("RAJAPACK", "RAJA", "PAREDES", "PROD'HYGIENE", "PRO HYGIENE", "HYGIAL"), "Hygiène / Emballages", ("Sortie",)),
    (("NESPRESSO", "LAVAZZA", "MAHLKOENIG", "BUNN"), "Café / Matériel bar", ("Sortie",)),
    (("BRAGARD", "ROBUR"), "Tenues / Uniformes", ("Sortie",)),
    (("KILOUTOU", "LOXAM"), "Location matériel", ("Sortie",)),
    (("UBER EATS", "DELIVEROO", "JUST EAT", "UBER "), "Plateformes / Commissions", ("Sortie",)),
    (("DPD", "CHRONOPOST", "COLISSIMO", "LA POSTE", "MONDIAL RELAY", "GLS", "UPS", "DHL"), "Logistique / Transport", ("Sortie",)),
    (("MICROSOFT", "OFFICE 365", "AZURE", "GOOGLE", "WORKSPACE", "GSUITE", "ADOBE", "CREATIVE CLOUD", "CANVA", "NOTION", "SLACK"), "SaaS / Informatique", ("Sortie",)),
    (("SACEM", "SPRE"), "Droits d’auteur / Musique d’ambiance", ("Sortie",)),
    (("AMAZON", "AMZN", "FNAC", "LDLC", "MATERIEL.NET", "DARTY", "BOULANGER"), "Fournitures / Matériel", ("Sortie",)),
    (("BRUNEAU", "LYRECO"), "Fournitures de bureau", ("Sortie",)),
    (("PAPREC", "VEOLIA PROPRETE", "SUEZ RECYCLAGE"), "Déchets / Recyclage", ("Sortie",)),
    (("VERISURE", "EPS"), "Sécurité", ("Sortie",)),
    (("ELIS", "INITIAL"), "Blanchisserie / Linge pro", ("Sortie",)),
    (("RATP", "SNCF", "IDF MOBILITES"), "Transports", ("Sortie",)),
    (("UBER", "UBER EATS", "UBER *"), "Transports", ("Sortie",)),
    (("TOTAL STATION", "ESSO", "SHELL", "AVIA", "TOTALENERGIES", "TOTAL ENERGIES"), "Carburant / Déplacements", ("Sortie",)),
    (("SPB", "PACIFICA", "ASSUR", "ASSURANCE", "ASSURANCE LCL"), "Assurance", ("Sortie",)),
    (("PREFILOC", "FINANCEMENT", "CREDIT"), "Financement / Crédit", ("Sortie",)),
    (("ABON LCL ACCESS", "COTISATION CARTE", "COTISATION MENSUELLE CARTE", "OPTION PRO", "COTISATION MENSUELLE"), "Frais bancaires", None),
    (("COMMISSIONS SUR REMISE CB",), "Frais bancaires", None),
    (("RESULTAT ARRETE COMPTE",), "Frais bancaires", None),
    (("RESIDENCE", "LOYER", "ST AN", "LOCATION", "LOCAT"), "Loyer/Location", ("Sortie",)),
    (("GNANAM", "NOUTAM", "FOURNISSEUR"), "Fournisseur", ("Sortie",)),
    (("FRAIS", "AGIOS", "COMMISSION", "ABONNEMENT", "COTISATION CARTE"), "Frais bancaires", None),
    (("CHANTIER", "FACTURE"), "Autre", None),
) + load_vendor_category_rules()

CATEGORY_GROUP_PRESETS: Dict[str, Dict[str, Any]] = {
    "default": {
        "label": "Vue standard",
        "groups": {
            "Recettes": {"categories": ("Encaissement",), "types": ("Entrée",)},
            "Encaissement & commissions": {
                "categories": ("Encaissement / Commission", "Encaissement mobile", "Frais d'encaissement"),
                "types": None,
            },
            "Transferts & change": {
                "categories": ("Transfert / Paiement mobile", "Transfert / Change"),
                "types": None,
            },
            "Banque & Financement": {
                "categories": ("Banque", "Banque en ligne", "Financement / Crédit", "Crédit / Financement"),
                "types": ("Sortie",),
            },
            "Fournisseurs alimentaires": {"categories": ("Fournisseur alimentaire",), "types": ("Sortie",)},
            "Fournisseurs": {"categories": ("Fournisseur",), "types": ("Sortie",)},
            "Approvisionnement": {"categories": ("Approvisionnement",), "types": ("Sortie",)},
            "Charge salariale et sociale": {
                "categories": ("Salaires", "Charges sociales", "Retraite / Prévoyance"),
                "types": ("Sortie",),
            },
            "Charges fixes": {
                "categories": ("Loyer/Location", "Télécom", "Abonnements", "Services professionnels"),
                "types": ("Sortie",),
            },
            "Énergie & eau": {"categories": ("Énergie", "Gaz", "Eau"), "types": ("Sortie",)},
            "Télécom & SaaS": {
                "categories": ("Télécom", "Abonnements", "Abonnements TV", "SaaS / Informatique"),
                "types": ("Sortie",),
            },
            "Assurances": {"categories": ("Assurance",), "types": ("Sortie",)},
            "Fiscalité": {"categories": ("Fiscalité", "Impôts et taxes"), "types": ("Sortie",)},
            "Logistique & plateau": {
                "categories": ("Logistique / Transport", "Plateformes / Commissions"),
                "types": ("Sortie",),
            },
            "Boissons & hygiène": {
                "categories": ("Boissons", "Hygiène / Emballages", "Déchets / Recyclage"),
                "types": ("Sortie",),
            },
            "Bar & café": {"categories": ("Café / Matériel bar",), "types": ("Sortie",)},
            "Tenues & location": {"categories": ("Tenues / Uniformes", "Location matériel"), "types": ("Sortie",)},
            "Fournitures & matériel": {
                "categories": ("Fournitures / Matériel", "Fournitures de bureau"),
                "types": ("Sortie",),
            },
            "Sécurité & entretien": {
                "categories": ("Sécurité", "Blanchisserie / Linge pro"),
                "types": ("Sortie",),
            },
            "Transports & déplacements": {
                "categories": ("Transports", "Carburant / Déplacements"),
                "types": ("Sortie",),
            },
            "Financement": {"categories": ("Financement",), "types": ("Sortie",)},
            "Services pro & comptabilité": {
                "categories": ("Comptabilité", "Services professionnels"),
                "types": ("Sortie",),
            },
            "Autres charges": {"categories": ("Autre",), "types": ("Sortie",)},
        },
        "fallback": {"Entrée": "Autres recettes", "Sortie": "Autres charges", "default": "Autres"},
    }
}


def _is_stop_line(line: str) -> bool:
    """Détecte les lignes système indiquant qu'on sort du bloc de transactions."""

    upper = line.upper()
    return any(upper.startswith(prefix) for prefix in STOP_PREFIXES)


def _looks_like_header_line(line: str) -> bool:
    """Identifie les débuts d'en-têtes (codes opération, postes bancaires...)."""

    upper = line.upper()
    return any(upper.startswith(prefix) for prefix in HEADER_START_PREFIXES)


def _is_detail_line(line: str) -> bool:
    """Reconnaît les lignes de détails qui complètent l'en-tête d'opération."""

    upper = line.upper()
    if any(upper.startswith(prefix) for prefix in DETAIL_PREFIXES):
        return True
    cleaned = upper.replace(" ", "")
    return cleaned.isdigit()


def _normalize_description(parts: list[str]) -> str:
    """Concatène et nettoie les segments de description pour un mouvement."""

    text = " ".join(parts)
    return re.sub(r"\s+", " ", text).strip()


def _extract_descriptions(header_lines: list[str]) -> list[str]:
    """Regroupe les lignes extraites du PDF en descriptions lisibles."""

    descriptions: list[str] = []
    current: list[str] = []
    capturing = False
    for raw in header_lines:
        line = raw.strip()
        if not line:
            continue
        if _is_stop_line(line):
            if current:
                descriptions.append(_normalize_description(current))
                current = []
            capturing = False
            continue
        if _looks_like_header_line(line):
            if current:
                descriptions.append(_normalize_description(current))
            current = [line]
            capturing = True
            continue
        if capturing:
            if _is_detail_line(line):
                current.append(line)
            else:
                descriptions.append(_normalize_description(current))
                current = [line]
                capturing = True
    if current:
        descriptions.append(_normalize_description(current))
    return [desc for desc in descriptions if desc]


def _align_descriptions(descriptions: list[str], target_count: int) -> list[str]:
    """Ajuste le nombre d'intitulés pour coller au nombre de montants trouvés."""

    if target_count <= 0:
        return []
    if not descriptions:
        return [""] * target_count
    if len(descriptions) == target_count:
        return descriptions
    if len(descriptions) > target_count:
        drop = len(descriptions) - target_count
        trimmed = descriptions[drop:]
        if len(trimmed) < target_count:
            trimmed.extend([""] * (target_count - len(trimmed)))
        return trimmed
    padded = descriptions[:]
    padded.extend([""] * (target_count - len(descriptions)))
    return padded


def _get_grouping_preset(name: str | None) -> Tuple[str, Dict[str, Any]]:
    """Sélectionne le préréglage de regroupement à utiliser pour les résumés."""

    if name and name in CATEGORY_GROUP_PRESETS:
        return name, CATEGORY_GROUP_PRESETS[name]
    return "default", CATEGORY_GROUP_PRESETS["default"]


def _resolve_group_name(categorie: str | None, entry_type: str, preset: Dict[str, Any]) -> str:
    """Mappe une catégorie individuelle vers un libellé de regroupement."""

    cat = (categorie or "").strip()
    entry_type = entry_type or "Sortie"
    groups = preset.get("groups", {})
    for group_name, definition in groups.items():
        allowed_types = definition.get("types")
        categories = definition.get("categories") or ()
        keywords = definition.get("keywords") or ()
        if allowed_types and entry_type not in allowed_types:
            continue
        if cat and cat in categories:
            return group_name
        if keywords and any(keyword.upper() in cat.upper() for keyword in keywords):
            return group_name
    fallback = preset.get("fallback", {})
    if entry_type in fallback:
        return fallback[entry_type]
    return fallback.get("default", "Autres")


def _normalize_for_keyword(text: str) -> str:
    """Supprime la ponctuation pour effectuer des comparaisons robustes."""

    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _keyword_matches(label_upper: str, normalized_label: str, keyword: str) -> bool:
    """Teste la présence d'un mot-clé dans une étiquette brute ou normalisée."""

    if not keyword:
        return False
    keyword_clean = keyword.upper().strip()
    keyword_trimmed = keyword_clean.replace("%", "")
    if keyword_trimmed and keyword_trimmed in label_upper:
        return True
    normalized_keyword = _normalize_for_keyword(keyword_trimmed)
    if normalized_keyword and normalized_keyword in normalized_label:
        return True
    return False


def _guess_category(label: str | None, entry_type: str) -> str | None:
    """Essaye de catégoriser une ligne bancaire en se basant sur les mots-clés connues."""

    if not label:
        return "Encaissement" if entry_type == "Entrée" else "Autres"
    upper = label.upper()
    normalized_label = _normalize_for_keyword(label)
    for keywords, category, allowed_types in CATEGORY_RULES:
        if allowed_types and entry_type not in allowed_types:
            continue
        if any(_keyword_matches(upper, normalized_label, keyword) for keyword in keywords):
            return category
    if entry_type == "Entrée":
        return "Encaissement"
    return "Autres"


def _looks_like_credit(label: str) -> bool:
    """Renvoie True si le libellé ressemble à un encaissement (utile pour les relevés PDF)."""

    label_upper = label.upper()
    if any(keyword in label_upper for keyword in CREDIT_KEYWORDS):
        return True
    if any(keyword in label_upper for keyword in DEBIT_KEYWORDS):
        return False
    return True


def _should_skip_line(line: str) -> bool:
    """Ignore les lignes vides ou les en-têtes parasites lors du parsing PDF."""

    if not line:
        return True
    return _is_stop_line(line)


def parse_bank_statement_pdf(pdf_bytes: bytes) -> List[dict[str, Any]]:
    """Détecte le format (LCL vs SumUp) puis extrait les lignes bancaires du PDF."""

    reader = PdfReader(io.BytesIO(pdf_bytes))
    first_page_text = ""
    if reader.pages:
        first_page_text = reader.pages[0].extract_text() or ""
    upper_text = first_page_text.upper()
    if "RELEVÉ DE COMPTE SUMUP" in upper_text or "RELEVE DE COMPTE SUMUP" in upper_text:
        return _parse_sumup_bank_statement(reader)
    return _parse_lcl_bank_statement(reader)


# --- Charges & fournisseurs (écran Restaurant HQ)

def list_depense_categories(tenant_id: int) -> List[dict[str, Any]]:
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_depense_categories
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_depense_category(tenant_id: int, nom: str) -> dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depense_categories (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def _ensure_depense_category(conn, tenant_id: int, nom: str | None) -> int | None:
    if not nom:
        return None
    normalized = nom.strip()
    if not normalized:
        return None
    row = conn.execute(
        text(
            """
            SELECT id FROM restaurant_depense_categories
            WHERE tenant_id = :tenant AND UPPER(nom) = UPPER(:nom)
            """
        ),
        {"tenant": tenant_id, "nom": normalized},
    ).fetchone()
    if row:
        return row.id
    row = conn.execute(
        text(
            """
            INSERT INTO restaurant_depense_categories (tenant_id, nom)
            VALUES (:tenant, :nom)
            RETURNING id
            """
        ),
        {"tenant": tenant_id, "nom": normalized},
    ).fetchone()
    return int(row.id) if row else None


def list_cost_centers(tenant_id: int) -> List[dict[str, Any]]:
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_cost_centers
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_cost_center(tenant_id: int, nom: str) -> dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_cost_centers (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def list_fournisseurs(tenant_id: int) -> List[dict[str, Any]]:
    df = query_df(
        text(
            """
            SELECT id, nom
            FROM restaurant_fournisseurs
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_fournisseur(tenant_id: int, nom: str) -> dict[str, Any]:
    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_fournisseurs (tenant_id, nom)
                VALUES (:tenant, :nom)
                RETURNING id, nom
                """
            ),
            {"tenant": tenant_id, "nom": nom},
        ).fetchone()
    return dict(row._mapping)


def list_expenses(tenant_id: int) -> List[dict[str, Any]]:
    sql = """
        SELECT d.id,
               d.libelle,
               d.date_operation,
               COALESCE(dc.nom, '') AS categorie,
               COALESCE(cc.nom, '') AS cost_center,
               COALESCE(f.nom, '') AS fournisseur,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) AS montant_ht,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * (1 + COALESCE(d.tva_pct,0)/100.0) AS montant_ttc
        FROM restaurant_depenses d
        LEFT JOIN restaurant_depense_categories dc ON dc.id = d.categorie_id
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        LEFT JOIN restaurant_fournisseurs f ON f.id = d.fournisseur_id
        WHERE d.tenant_id = :tenant
        ORDER BY d.date_operation DESC, d.id DESC
    """
    df = query_df(text(sql), {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


def get_expense_detail(tenant_id: int, expense_id: int) -> dict[str, Any] | None:
    sql = """
        SELECT d.id,
               d.libelle,
               d.date_operation,
               COALESCE(dc.nom, '') AS categorie,
               COALESCE(cc.nom, '') AS cost_center,
               COALESCE(f.nom, '') AS fournisseur,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) AS montant_ht,
               COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * (1 + COALESCE(d.tva_pct,0)/100.0) AS montant_ttc
        FROM restaurant_depenses d
        LEFT JOIN restaurant_depense_categories dc ON dc.id = d.categorie_id
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        LEFT JOIN restaurant_fournisseurs f ON f.id = d.fournisseur_id
        WHERE d.tenant_id = :tenant AND d.id = :id
        LIMIT 1
    """
    df = query_df(text(sql), {"tenant": tenant_id, "id": expense_id})
    if df.empty:
        return None
    return df.to_dict("records")[0]


def create_expense(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Insère une charge puis recharge sa fiche enrichie (catégorie, fournisseur...)."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depenses (
                    tenant_id, categorie_id, cost_center_id, fournisseur_id,
                    libelle, unite, quantite, prix_unitaire, montant_ht, tva_pct,
                    date_operation, source, ref_externe
                ) VALUES (
                    :tenant_id, :categorie_id, :cost_center_id, :fournisseur_id,
                    :libelle, :unite, :quantite, :prix_unitaire, :montant_ht, :tva_pct,
                    :date_operation, :source, :ref_externe
                )
                RETURNING id
                """
            ),
            payload,
        ).fetchone()
    expense = get_expense_detail(tenant_id, row.id)
    if not expense:
        raise RuntimeError("Impossible de récupérer la dépense créée")
    return expense


def expense_summary_by_month(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
    """Agrège les charges HT par mois sur la période glissante demandée."""

    sql = """
        SELECT TO_CHAR(DATE_TRUNC('month', date_operation), 'YYYY-MM') AS label,
               SUM(COALESCE(montant_ht, quantite * prix_unitaire)) AS total_ht
        FROM restaurant_depenses
        WHERE tenant_id = :tenant
          AND date_operation >= (CURRENT_DATE - INTERVAL ':months months')
        GROUP BY 1
        ORDER BY 1 DESC
    """
    df = query_df(text(sql.replace(':months', str(max(1, months)))), {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


# --- Ingrédients, plats et marges

def list_ingredients(tenant_id: int) -> List[dict[str, Any]]:
    """Retourne les ingrédients disponibles, utilisés pour composer les plats."""

    df = query_df(
        text(
            """
            SELECT id, nom, unite_base, cout_unitaire, stock_actuel
            FROM restaurant_ingredients
            WHERE tenant_id = :tenant
            ORDER BY nom
            """
        ),
        {"tenant": tenant_id},
    )
    return df.to_dict("records") if not df.empty else []


def create_ingredient(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Crée un ingrédient (prix unitaire, unité de base, stock initial)."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                VALUES (:tenant, :nom, :unite_base, :cout_unitaire, :stock_actuel)
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel
                """
            ),
            {**payload, "tenant": tenant_id},
        ).fetchone()
    return dict(row._mapping)


def update_ingredient_price(tenant_id: int, ingredient_id: int, new_price: float) -> dict[str, Any]:
    """Met à jour le coût d'un ingrédient puis recalcule les marges des plats."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_ingredients
                SET cout_unitaire = :price
                WHERE tenant_id = :tenant AND id = :ingredient_id
                RETURNING id, nom, unite_base, cout_unitaire, stock_actuel
                """
            ),
            {"tenant": tenant_id, "ingredient_id": ingredient_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Ingrédient introuvable")
    refresh_plat_costs(tenant_id)
    return dict(row._mapping)


def list_plats(tenant_id: int) -> List[dict[str, Any]]:
    """Charge les plats avec marge brute et pourcentage calculés à partir des ingrédients liés."""

    plats_df = query_df(
        text(
            """
            WITH couts AS (
                SELECT
                    rpi.plat_id,
                    SUM(rpi.quantite * COALESCE(ri.cout_unitaire, 0)) AS cout_matiere
                FROM restaurant_plat_ingredients rpi
                JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
                WHERE rpi.tenant_id = :tenant
                GROUP BY rpi.plat_id
            )
            SELECT
                p.id,
                p.nom,
                p.categorie,
                p.prix_vente_ttc,
                p.actif,
                COALESCE(c.cout_matiere, 0) AS cout_matiere
            FROM restaurant_plats p
            LEFT JOIN couts c ON c.plat_id = p.id
            WHERE p.tenant_id = :tenant
            ORDER BY p.nom
            """
        ),
        {"tenant": tenant_id},
    )
    if plats_df.empty:
        return []

    plats_df["cout_matiere"] = plats_df["cout_matiere"].fillna(0.0)
    plats_df["marge_brute"] = plats_df["prix_vente_ttc"].fillna(0.0) - plats_df["cout_matiere"]
    plats_df["marge_pct"] = plats_df.apply(
        lambda row: (row["marge_brute"] / row["prix_vente_ttc"] * 100) if row["prix_vente_ttc"] else 0.0,
        axis=1,
    )

    plat_ids = plats_df["id"].tolist()
    ing_df = None
    if plat_ids:
        placeholder_tokens = []
        params: Dict[str, Any] = {"tenant": tenant_id}
        for idx, pid in enumerate(plat_ids):
            token = f"pid_{idx}"
            placeholder_tokens.append(f":{token}")
            params[token] = pid

        sql = text(
            f"""
            SELECT rpi.id,
                   rpi.plat_id,
                   rpi.ingredient_id,
                   ri.nom,
                   rpi.quantite,
                   rpi.unite
            FROM restaurant_plat_ingredients rpi
            JOIN restaurant_ingredients ri ON ri.id = rpi.ingredient_id
            WHERE rpi.tenant_id = :tenant
              AND rpi.plat_id IN ({", ".join(placeholder_tokens)})
            """
        )
        ing_df = query_df(sql, params=params)

    grouped = {}
    if ing_df is not None and not ing_df.empty:
        for row in ing_df.to_dict("records"):
            grouped.setdefault(row["plat_id"], []).append(row)

    results = []
    for plat in plats_df.to_dict("records"):
        plat["ingredients"] = grouped.get(plat["id"], [])
        plat["cout_matiere"] = _safe_float(plat.get("cout_matiere"))
        plat["marge_brute"] = _safe_float(plat.get("marge_brute"))
        plat["marge_pct"] = _safe_float(plat.get("marge_pct"))
        results.append(plat)
    return results


def refresh_plat_costs(tenant_id: int, margin_threshold: float = 35.0) -> dict[str, Any]:
    """Délègue le recalcul des coûts matière/marges aux utilitaires partagés."""

    return restaurant_costs.refresh_plat_costs(tenant_id=tenant_id, margin_threshold=margin_threshold)


def list_plat_alerts(tenant_id: int) -> List[dict[str, Any]]:
    """Retourne les alertes de marge générées par le recalcul précédent."""

    return restaurant_costs.list_margin_alerts(tenant_id=tenant_id)


def create_plat(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Crée un plat et initialise les totaux/marges à partir des ingrédients liés (s'il y en a)."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_plats (tenant_id, nom, categorie, prix_vente_ttc, actif)
                VALUES (:tenant, :nom, :categorie, :prix_vente_ttc, :actif)
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {**payload, "tenant": tenant_id},
        ).fetchone()
    base = dict(row._mapping)
    price = _safe_float(base.get("prix_vente_ttc"))
    base.update(
        {
            "cout_matiere": 0.0,
            "marge_brute": price,
            "marge_pct": 100.0 if price else 0.0,
            "ingredients": [],
        }
    )
    refresh_plat_costs(tenant_id)
    return base


def attach_ingredient_to_plat(tenant_id: int, plat_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Associe un ingrédient à un plat (quantité + unité) avec recalcul des coûts."""

    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unite)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, **payload},
        )
    refresh_plat_costs(tenant_id)
    return {"status": "ok"}


def update_plat_price(tenant_id: int, plat_id: int, new_price: float) -> dict[str, Any]:
    """Met à jour le prix TTC d'un plat, puis recalcule les marges liées."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_plats
                SET prix_vente_ttc = :price
                WHERE tenant_id = :tenant AND id = :plat_id
                RETURNING id, nom, categorie, prix_vente_ttc, actif
                """
            ),
            {"tenant": tenant_id, "plat_id": plat_id, "price": new_price},
        ).fetchone()
        if not row:
            raise RuntimeError("Plat introuvable")
    refresh_plat_costs(tenant_id)
    plats = list_plats(tenant_id)
    updated = next((plat for plat in plats if plat["id"] == plat_id), None)
    return updated or dict(row._mapping)


def list_ingredient_price_history(tenant_id: int, ingredient_id: int) -> List[dict[str, Any]]:
    """Affiche l'historique de prix d'un ingrédient donné."""

    df = query_df(
        text(
            """
            SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
            FROM restaurant_ingredient_price_history h
            JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
            WHERE h.tenant_id = :tenant AND h.ingredient_id = :ingredient
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "ingredient": ingredient_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_plat_price_history(tenant_id: int, plat_id: int) -> List[dict[str, Any]]:
    """Affiche l'historique des prix d'un plat donné."""

    df = query_df(
        text(
            """
            SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
            FROM restaurant_plat_price_history h
            JOIN restaurant_plats p ON p.id = h.plat_id
            WHERE h.tenant_id = :tenant AND h.plat_id = :plat
            ORDER BY h.changed_at DESC
            """
        ),
        {"tenant": tenant_id, "plat": plat_id},
    )
    return df.to_dict("records") if not df.empty else []


def list_recent_price_changes(tenant_id: int, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
    """Retourne les dernières modifications de prix côté ingrédients et plats."""

    safe_limit = max(1, min(limit, 200))
    ingredient_sql = text(
        f"""
        SELECT h.id, h.ingredient_id, ri.nom AS ingredient_nom, h.cout_unitaire, h.changed_at
        FROM restaurant_ingredient_price_history h
        JOIN restaurant_ingredients ri ON ri.id = h.ingredient_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    plat_sql = text(
        f"""
        SELECT h.id, h.plat_id, p.nom AS plat_nom, h.prix_vente_ttc, h.changed_at
        FROM restaurant_plat_price_history h
        JOIN restaurant_plats p ON p.id = h.plat_id
        WHERE h.tenant_id = :tenant
        ORDER BY h.changed_at DESC
        LIMIT {safe_limit}
        """
    )
    ingredient_df = query_df(ingredient_sql, {"tenant": tenant_id})
    plat_df = query_df(plat_sql, {"tenant": tenant_id})
    return {
        "ingredients": ingredient_df.to_dict("records") if not ingredient_df.empty else [],
        "plats": plat_df.to_dict("records") if not plat_df.empty else [],
    }


# --- Relevés bancaires et rapprochement charges

def list_bank_statements(tenant_id: int, account: str | None = None) -> List[dict[str, Any]]:
    """Retourne les lignes de relevés bancaires (filtrées par compte si besoin)."""

    clause = "AND account = :account" if account else ""
    sql = text(
        f"""
        SELECT id, account, date, libelle, categorie, montant, type, mois, depense_id
        FROM restaurant_bank_statements
        WHERE tenant_id = :tenant {clause}
        ORDER BY date DESC, id DESC
        """
    )
    params: dict[str, Any] = {"tenant": tenant_id}
    if account:
        params["account"] = account
    df = query_df(sql, params)
    if df.empty:
        return []

    # Pydantic n'aime pas les NaN: on convertit toutes les valeurs NaN en None
    # (incluant depense_id et toute colonne nullable) avant de sérialiser.
    df = df.where(pd.notna(df), None)
    # S'assurer que depense_id reste en object pour ne pas retransformer None en NaN
    if "depense_id" in df.columns:
        df["depense_id"] = df["depense_id"].astype(object).where(pd.notna(df["depense_id"]), None)
    return df.to_dict("records")


def list_bank_accounts_overview(tenant_id: int) -> List[dict[str, Any]]:
    """Synthèse par compte (volumétrie, flux, dernière activité)."""

    sql = text(
        """
        SELECT
            account,
            COUNT(*) AS operations,
            SUM(CASE WHEN type = 'Entrée' THEN montant ELSE 0 END) AS inflow,
            SUM(CASE WHEN type = 'Sortie' THEN montant ELSE 0 END) AS outflow,
            MAX(date) AS last_activity
        FROM restaurant_bank_statements
        WHERE tenant_id = :tenant
        GROUP BY account
        ORDER BY account
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    overview: List[dict[str, Any]] = []
    today = date.today()
    if df.empty:
        return overview

    for record in df.to_dict("records"):
        last_activity = record.get("last_activity")
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.strptime(last_activity, "%Y-%m-%d").date()
            except ValueError:
                last_activity = None
        balance = _safe_float(record.get("inflow")) - _safe_float(record.get("outflow"))
        days_since: Optional[int] = None
        if isinstance(last_activity, date):
            days_since = (today - last_activity).days

        if days_since is None:
            status = "disconnected"
        elif days_since <= 7:
            status = "connected"
        elif days_since <= 30:
            status = "warning"
        else:
            status = "error"

        overview.append(
            {
                "account": record.get("account"),
                "display_name": record.get("account"),
                "provider": (record.get("account") or "").split()[0] if record.get("account") else None,
                "status": status,
                "balance": round(balance, 2),
                "inflow": round(_safe_float(record.get("inflow")), 2),
                "outflow": round(_safe_float(record.get("outflow")), 2),
                "operations": int(record.get("operations") or 0),
                "last_activity": last_activity,
                "currency": "EUR",
            }
        )
    return overview


def create_bank_statement(tenant_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Insère une ligne importée/éditée de relevé bancaire."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                INSERT INTO restaurant_bank_statements (
                    tenant_id, account, date, libelle, categorie, montant, type, mois
                ) VALUES (
                    :tenant, :account, :date, :libelle, :categorie, :montant, :type, :mois
                )
                RETURNING id, account, date, libelle, categorie, montant, type, mois, depense_id
                """
            ),
            {
                **payload,
                "tenant": tenant_id,
            },
        ).fetchone()
    return dict(row._mapping)


def update_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Met à jour un relevé existant et renvoie la version enrichie."""

    with get_engine().begin() as conn:
        row = conn.execute(
            text(
                """
                UPDATE restaurant_bank_statements
                SET account = :account,
                    date = :date,
                    libelle = :libelle,
                    categorie = :categorie,
                    montant = :montant,
                    type = :type,
                    mois = :mois,
                    depense_id = COALESCE(:depense_id, depense_id)
                WHERE tenant_id = :tenant AND id = :id
                RETURNING id, account, date, libelle, categorie, montant, type, mois, depense_id
                """
            ),
            {
                **payload,
                "tenant": tenant_id,
                "id": entry_id,
            },
        ).fetchone()
        if not row:
            raise RuntimeError("Relevé introuvable")
    return dict(row._mapping)


def import_bank_statements_from_pdf(tenant_id: int, account: str, pdf_bytes: bytes) -> dict[str, int]:
    """Parse un relevé PDF et insère les opérations inexistantes pour le compte donné."""

    entries = parse_bank_statement_pdf(pdf_bytes)
    if not entries:
        return {"inserted": 0, "total": 0}

    inserted = 0
    with get_engine().begin() as conn:
        for entry in entries:
            params = {
                "tenant": tenant_id,
                "account": account,
                "date": entry["date"],
                "libelle": entry["libelle"],
                "categorie": entry.get("categorie"),
                "montant": entry["montant"],
                "type": entry["type"],
                "mois": entry["mois"],
                "source": entry.get("source", "pdf"),
            }
            row = conn.execute(
                text(
                    """
                    INSERT INTO restaurant_bank_statements (
                        tenant_id, account, date, libelle, categorie,
                        montant, type, mois, source
                    ) VALUES (
                        :tenant, :account, :date, :libelle, :categorie,
                        :montant, :type, :mois, :source
                    )
                    ON CONFLICT DO NOTHING
                    RETURNING id
                    """
                ),
                params,
            ).fetchone()
            if row:
                inserted += 1
    return {"inserted": inserted, "total": len(entries)}


def create_expense_from_bank_statement(tenant_id: int, entry_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    """Crée une dépense à partir d'un relevé bancaire, puis lie les deux en base."""

    eng = get_engine()
    with eng.begin() as conn:
        statement = conn.execute(
            text(
                """
                SELECT id, account, date, libelle, categorie, montant, type, mois, depense_id
                FROM restaurant_bank_statements
                WHERE tenant_id = :tenant AND id = :id
                """
            ),
            {"tenant": tenant_id, "id": entry_id},
        ).fetchone()
        if not statement:
            raise RuntimeError("Relevé introuvable")
        if statement.depense_id:
            raise RuntimeError("Une dépense est déjà associée à ce relevé")

        libelle = payload.get("libelle") or statement.libelle
        montant_ht = payload.get("montant_ht")
        if montant_ht is None:
            montant_ht = abs(_safe_float(statement.montant))
        date_operation = payload.get("date_operation") or statement.date
        category_name = payload.get("categorie_nom") or statement.categorie
        category_id = payload.get("categorie_id")
        if not category_id:
            category_id = _ensure_depense_category(conn, tenant_id, category_name)
        params = {
            "tenant": tenant_id,
            "categorie_id": category_id,
            "fournisseur_id": payload.get("fournisseur_id"),
            "cost_center_id": payload.get("cost_center_id"),
            "libelle": libelle,
            "unite": payload.get("unite"),
            "quantite": payload.get("quantite"),
            "prix_unitaire": payload.get("prix_unitaire"),
            "montant_ht": montant_ht,
            "tva_pct": payload.get("tva_pct", 20.0),
            "date_operation": date_operation,
            "source": "bank_statement",
            "ref_externe": f"statement:{entry_id}",
        }
        expense_row = conn.execute(
            text(
                """
                INSERT INTO restaurant_depenses (
                    tenant_id, categorie_id, fournisseur_id, cost_center_id,
                    libelle, unite, quantite, prix_unitaire, montant_ht,
                    tva_pct, date_operation, source, ref_externe
                ) VALUES (
                    :tenant, :categorie_id, :fournisseur_id, :cost_center_id,
                    :libelle, :unite, :quantite, :prix_unitaire, :montant_ht,
                    :tva_pct, :date_operation, :source, :ref_externe
                )
                RETURNING id, libelle, montant_ht, date_operation
                """
            ),
            params,
        ).fetchone()

        conn.execute(
            text(
                """
                UPDATE restaurant_bank_statements
                SET depense_id = :depense_id
                WHERE tenant_id = :tenant AND id = :id
                """
            ),
            {"tenant": tenant_id, "id": entry_id, "depense_id": expense_row.id},
        )

    expense = get_expense_detail(tenant_id, expense_row.id)
    updated_statement = list_bank_statements(tenant_id, account=statement.account)
    statement_dict = next((item for item in updated_statement if item["id"] == entry_id), None)
    return {"expense": expense, "statement": statement_dict}


def transfer_from_epicerie(tenant_id: int, produit_restaurant_id: int, quantite: float = 1.0) -> Dict[str, Any]:
    """Appelle la fonction SQL transfer_from_epicerie pour générer les mouvements croisés épicerie → restaurant."""

    eng = get_engine()
    with eng.begin() as conn:
        rows = conn.execute(
            text("SELECT * FROM transfer_from_epicerie(:pid, :qty)"),
            {"pid": int(produit_restaurant_id), "qty": float(quantite)},
        ).mappings().all()
    if not rows:
        raise RuntimeError("Aucun mouvement généré (mapping manquant ?)")
    return {"movements": rows}


def get_bank_statement_summary(
    tenant_id: int, account: str | None = None, months: int = 6, grouping: str | None = None
) -> Dict[str, Any]:
    """Construit les agrégats journaliers/hebdomadaires/mensuels et par groupe de catégories."""

    window: int | None = None
    if months and months > 0:
        # Cap to a reasonable upper bound to avoid accidental huge scans.
        window = max(1, min(months, 120))
    preset_name, preset = _get_grouping_preset(grouping)
    account_clause = "AND account = :account" if account else ""
    date_clause = ""
    if window is not None:
        date_clause = f"AND date >= (CURRENT_DATE - INTERVAL '{window} months')"
    sql = text(
        f"""
        SELECT date, mois, categorie, montant, type
        FROM restaurant_bank_statements
        WHERE tenant_id = :tenant {account_clause}
          {date_clause}
        ORDER BY date ASC, id ASC
        """
    )
    params: Dict[str, Any] = {"tenant": tenant_id}
    if account:
        params["account"] = account
    df = query_df(sql, params)

    monthly_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    weekly_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    daily_ordered: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    groups_totals: Dict[str, Dict[str, float]] = defaultdict(lambda: {"entrees": 0.0, "sorties": 0.0})

    if not df.empty:
        for row in df.to_dict("records"):
            row_date = row.get("date")
            if isinstance(row_date, str):
                try:
                    row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
                except ValueError:
                    row_date = None
            if not isinstance(row_date, date):
                row_date = date.today()
            month_key = row.get("mois") or row_date.strftime("%Y-%m")
            iso_week = row_date.isocalendar()
            week_key = f"{iso_week.year}-W{iso_week.week:02d}"
            week_start = row_date - timedelta(days=row_date.weekday())
            week_end = week_start + timedelta(days=6)
            day_key = row_date.isoformat()
            entry_type = row.get("type") or "Sortie"
            amount = _safe_float(row.get("montant"))
            month_bucket = monthly_ordered.setdefault(
                month_key, {"mois": month_key, "entrees": 0.0, "sorties": 0.0}
            )
            week_bucket = weekly_ordered.setdefault(
                week_key,
                {
                    "semaine": week_key,
                    "start_date": week_start,
                    "end_date": week_end,
                    "entrees": 0.0,
                    "sorties": 0.0,
                },
            )
            day_bucket = daily_ordered.setdefault(
                day_key,
                {
                    "jour": row_date,
                    "entrees": 0.0,
                    "sorties": 0.0,
                },
            )
            if entry_type == "Entrée":
                month_bucket["entrees"] += amount
                week_bucket["entrees"] += amount
                day_bucket["entrees"] += amount
            else:
                month_bucket["sorties"] += amount
                week_bucket["sorties"] += amount
                day_bucket["sorties"] += amount

            group_name = _resolve_group_name(row.get("categorie"), entry_type, preset)
            group_bucket = groups_totals[group_name]
            if entry_type == "Entrée":
                group_bucket["entrees"] += amount
            else:
                group_bucket["sorties"] += amount

    monthly_summary: List[Dict[str, Any]] = []
    for bucket in monthly_ordered.values():
        bucket["net"] = bucket["entrees"] - bucket["sorties"]
        monthly_summary.append(
            {
                "mois": bucket["mois"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(bucket["net"], 2),
            }
        )

    weekly_summary: List[Dict[str, Any]] = []
    for bucket in weekly_ordered.values():
        net = bucket["entrees"] - bucket["sorties"]
        weekly_summary.append(
            {
                "semaine": bucket["semaine"],
                "start_date": bucket["start_date"],
                "end_date": bucket["end_date"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(net, 2),
            }
        )

    daily_summary: List[Dict[str, Any]] = []
    for bucket in daily_ordered.values():
        net = bucket["entrees"] - bucket["sorties"]
        daily_summary.append(
            {
                "jour": bucket["jour"],
                "entrees": round(bucket["entrees"], 2),
                "sorties": round(bucket["sorties"], 2),
                "net": round(net, 2),
            }
        )

    group_summary: List[Dict[str, Any]] = []
    for group_name, totals in groups_totals.items():
        net = totals["entrees"] - totals["sorties"]
        group_summary.append(
            {
                "group": group_name,
                "entrees": round(totals["entrees"], 2),
                "sorties": round(totals["sorties"], 2),
                "net": round(net, 2),
            }
        )
    group_summary.sort(key=lambda item: item["sorties"], reverse=True)

    forecast_value: float | None = None
    if monthly_summary:
        recent = [item["net"] for item in monthly_summary[-3:] if item["net"] is not None]
        if recent:
            forecast_value = round(sum(recent) / len(recent), 2)

    presets_meta = [
        {
            "name": key,
            "label": value.get("label", key.title()),
            "groups": list(value.get("groups", {}).keys()),
        }
        for key, value in CATEGORY_GROUP_PRESETS.items()
    ]

    effective_months = window if window is not None else 0
    return {
        "account": account,
        "months": effective_months,
        "grouping": preset_name,
        "monthly": monthly_summary,
        "weekly": weekly_summary,
        "daily": daily_summary,
        "groups": group_summary,
        "forecast_next_month": forecast_value,
        "presets": presets_meta,
    }


def expense_summary_by_cost_center(tenant_id: int, months: int = 3) -> List[dict[str, Any]]:
    """Répartit les charges par centre de coûts sur la période récente."""

    window = max(1, months)
    sql = """
        SELECT
            COALESCE(NULLIF(cc.nom, ''), 'Non affecté') AS label,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire)) AS total_ht
        FROM restaurant_depenses d
        LEFT JOIN restaurant_cost_centers cc ON cc.id = d.cost_center_id
        WHERE d.tenant_id = :tenant
          AND d.date_operation >= (CURRENT_DATE - INTERVAL ':window months')
        GROUP BY label
        ORDER BY total_ht DESC NULLS LAST
        """
    clause = text(sql.replace(":window", str(window)))
    df = query_df(clause, {"tenant": tenant_id})
    return df.to_dict("records") if not df.empty else []


def expense_summary_by_tva(tenant_id: int, months: int = 6) -> List[dict[str, Any]]:
    """Synthèse des montants HT/TVA/TTC pour faciliter la déclaration."""

    window = max(1, months)
    sql = """
        SELECT
            DATE_TRUNC('month', d.date_operation)::date AS periode,
            COALESCE(d.tva_pct, 0) AS taux,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire)) AS montant_ht,
            SUM(COALESCE(d.montant_ht, d.quantite * d.prix_unitaire) * COALESCE(d.tva_pct, 0) / 100.0) AS montant_tva
        FROM restaurant_depenses d
        WHERE d.tenant_id = :tenant
          AND d.date_operation >= (CURRENT_DATE - INTERVAL ':window months')
        GROUP BY periode, taux
        ORDER BY periode ASC, taux ASC
    """
    clause = text(sql.replace(":window", str(window)))
    df = query_df(clause, {"tenant": tenant_id})
    if df.empty:
        return []
    df["montant_ht"] = df["montant_ht"].fillna(0.0)
    df["montant_tva"] = df["montant_tva"].fillna(0.0)
    df["montant_ttc"] = df["montant_ht"] + df["montant_tva"]
    return df.to_dict("records")


def build_dashboard_overview(tenant_id: int) -> dict[str, Any]:
    """Assemble les indicateurs de la page Dashboard (charges, marge plats, stocks)."""

    monthly = expense_summary_by_month(tenant_id, months=6)
    by_center = expense_summary_by_cost_center(tenant_id, months=3)
    plats = list_plats(tenant_id)
    ingredients = list_ingredients(tenant_id)
    low_stock = [ing for ing in ingredients if _safe_float(ing.get("stock_actuel")) <= 3]

    current_month_charges = _safe_float(monthly[0]["total_ht"]) if monthly else 0.0
    avg_margin = (
        sum(max(0.0, _safe_float(plat.get("marge_pct"))) for plat in plats) / len(plats)
        if plats
        else 0.0
    )
    active_menu = sum(1 for plat in plats if plat.get("actif"))
    margin_alerts = sum(1 for plat in plats if _safe_float(plat.get("marge_pct")) < 30.0)

    return {
        "metrics": {
            "current_month_charges": round(current_month_charges, 2),
            "avg_margin_pct": round(avg_margin, 2),
            "active_menu_items": active_menu,
            "margin_alerts": margin_alerts,
        },
        "charges_monthly": monthly,
        "charges_by_center": by_center,
        "menu_costs": plats,
        "low_stock_ingredients": low_stock,
    }


ALLOWED_FORECAST_GRANULARITY = {"daily", "weekly", "monthly"}


def _build_forecast_timeline(total_units: float, total_value: float, horizon: int, granularity: str) -> List[dict[str, Any]]:
    """Projette la consommation attendue sur le scénario choisi (journalier/hebdo/mensuel)."""

    if total_units < 0:
        total_units = 0.0
    if total_value < 0:
        total_value = 0.0
    today = date.today()
    step = {"daily": 1, "weekly": 7, "monthly": 30}[granularity]
    remaining = horizon
    offset = 0
    timeline: List[dict[str, Any]] = []
    while remaining > 0:
        window = min(step, remaining)
        start = today + timedelta(days=offset)
        end = start + timedelta(days=window - 1)
        timeline.append(
            {
                "period_start": start,
                "period_end": end,
                "expected_units": round(total_units * window, 2),
                "expected_value": round(total_value * window, 2),
            }
        )
        offset += window
        remaining -= window
    return timeline


def build_forecast_overview(
    tenant_id: int,
    horizon_days: int = 30,
    granularity: str = "weekly",
    top_limit: int = 8,
) -> dict[str, Any]:
    """Construit la vue de prévisions (consommation quotidienne estimée, timeline, TOP articles)."""

    safe_horizon = max(1, min(int(horizon_days), 180))
    granularity_key = granularity if granularity in ALLOWED_FORECAST_GRANULARITY else "weekly"
    catalog_df = fetch_customer_catalog(tenant_id=tenant_id)
    forecast_map = forecast_daily_consumption(tenant_id=tenant_id, horizon=safe_horizon)
    generated_at = datetime.utcnow()
    if catalog_df.empty or not forecast_map:
        return {
            "horizon_days": safe_horizon,
            "granularity": granularity_key,
            "generated_at": generated_at,
            "metrics": {
                "total_daily_units": 0.0,
                "total_daily_value": 0.0,
                "at_risk_items": 0,
                "median_cover_days": None,
            },
            "timeline": _build_forecast_timeline(0.0, 0.0, safe_horizon, granularity_key),
            "top_products": [],
            "categories": [],
        }

    forecast_records = [
        {"product_id": int(pid), "forecast_daily": max(float(value or 0), 0.0)}
        for pid, value in forecast_map.items()
        if value and value > 0
    ]
    if not forecast_records:
        return {
            "horizon_days": safe_horizon,
            "granularity": granularity_key,
            "generated_at": generated_at,
            "metrics": {
                "total_daily_units": 0.0,
                "total_daily_value": 0.0,
                "at_risk_items": 0,
                "median_cover_days": None,
            },
            "timeline": _build_forecast_timeline(0.0, 0.0, safe_horizon, granularity_key),
            "top_products": [],
            "categories": [],
        }

    forecast_df = pd.DataFrame.from_records(forecast_records)
    merged = forecast_df.merge(catalog_df, left_on="product_id", right_on="id", how="left")
    if merged.empty:
        return {
            "horizon_days": safe_horizon,
            "granularity": granularity_key,
            "generated_at": generated_at,
            "metrics": {
                "total_daily_units": 0.0,
                "total_daily_value": 0.0,
                "at_risk_items": 0,
                "median_cover_days": None,
            },
            "timeline": _build_forecast_timeline(0.0, 0.0, safe_horizon, granularity_key),
            "top_products": [],
            "categories": [],
        }

    numeric_cols = ["prix_vente", "stock_actuel"]
    for col in numeric_cols:
        merged[col] = pd.to_numeric(merged.get(col), errors="coerce").fillna(0.0)

    merged["categorie"] = merged.get("categorie", "Autre").fillna("Autre")
    merged["nom"] = merged.get("nom", "Produit").fillna("Produit")
    merged["ean"] = merged.get("ean", "").fillna("")
    merged["forecast_value"] = merged["forecast_daily"] * merged["prix_vente"]
    merged["stock_cover_days"] = np.where(
        merged["forecast_daily"] > 0,
        merged["stock_actuel"] / merged["forecast_daily"],
        np.inf,
    )

    risk_threshold = max(3, min(14, safe_horizon))
    merged["risk_level"] = np.select(
        [
            merged["stock_cover_days"] <= 1,
            merged["stock_cover_days"] <= risk_threshold / 2,
            merged["stock_cover_days"] <= risk_threshold,
        ],
        ["critique", "alerte", "surveillance"],
        default="ok",
    )
    risk_priority = {"critique": 0, "alerte": 1, "surveillance": 2, "ok": 3}
    merged["risk_priority"] = merged["risk_level"].map(risk_priority)

    total_units = float(merged["forecast_daily"].sum())
    total_value = float(merged["forecast_value"].sum())
    at_risk = int((merged["risk_level"].isin(["critique", "alerte"])).sum())
    finite_cover = merged.loc[np.isfinite(merged["stock_cover_days"]), "stock_cover_days"]
    median_cover = float(finite_cover.median()) if not finite_cover.empty else None

    top_limit = max(1, int(top_limit))
    top_df = (
        merged.sort_values(by=["risk_priority", "stock_cover_days", "forecast_value"], ascending=[True, True, False])
        .head(top_limit)
        .copy()
    )

    categories_df = (
        merged.groupby("categorie", dropna=False)[["forecast_daily", "forecast_value"]]
        .sum()
        .reset_index()
        .sort_values(by="forecast_value", ascending=False)
    )

    return {
        "horizon_days": safe_horizon,
        "granularity": granularity_key,
        "generated_at": generated_at,
        "metrics": {
            "total_daily_units": round(total_units, 2),
            "total_daily_value": round(total_value, 2),
            "at_risk_items": at_risk,
            "median_cover_days": round(median_cover, 2) if median_cover is not None else None,
        },
        "timeline": _build_forecast_timeline(total_units, total_value, safe_horizon, granularity_key),
        "top_products": [
            {
                "product_id": int(row["product_id"]),
                "nom": row["nom"],
                "categorie": row["categorie"],
                "ean": row.get("ean"),
                "forecast_daily": round(float(row["forecast_daily"]), 2),
                "forecast_value": round(float(row["forecast_value"]), 2),
                "stock_actuel": round(float(row["stock_actuel"]), 2),
                "stock_cover_days": None
                if not np.isfinite(row["stock_cover_days"])
                else round(float(row["stock_cover_days"]), 2),
                "risk_level": row["risk_level"],
            }
            for row in top_df.to_dict("records")
        ],
        "categories": [
            {
                "categorie": row["categorie"] or "Autre",
                "forecast_daily": round(float(row["forecast_daily"]), 2),
                "forecast_value": round(float(row["forecast_value"]), 2),
            }
            for row in categories_df.to_dict("records")
        ],
    }
C9SUMUP_DATE_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")
C9SUMUP_TIME_RE = re.compile(r"^\d{2}:\d{2}$")
SUMUP_STATUS_PREFIXES = (
    "APPROUV",
    "ENTRANT",
    "REMBOURS",
    "ANNUL",
    "REFUS",
)


def _parse_lcl_bank_statement(reader: PdfReader) -> List[dict[str, Any]]:
    """Extraction spécifique aux relevés LCL (PDF texte) en s'appuyant sur les lignes datées."""

    entries: list[dict[str, Any]] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        page_lines = [ln.strip() for ln in page_text.splitlines() if ln.strip()]
        if not page_lines:
            continue
        first_tx_idx = next(
            (idx for idx, value in enumerate(page_lines) if TRANSACTION_LINE_RE.match(value)),
            len(page_lines),
        )
        header_lines = page_lines[:first_tx_idx]
        data_lines = page_lines[first_tx_idx:]
        descriptions = _extract_descriptions(header_lines)
        tx_lines = [ln for ln in data_lines if TRANSACTION_LINE_RE.match(ln) and not _should_skip_line(ln)]
        descriptions = _align_descriptions(descriptions, len(tx_lines))

        for idx, line in enumerate(tx_lines):
            match = TRANSACTION_LINE_RE.match(line)
            if not match:
                continue
            description = descriptions[idx] if idx < len(descriptions) else ""
            if not description:
                description = "Mouvement"

            val_date = datetime.strptime(match.group("val"), "%d.%m.%y").date()
            op_month = val_date.strftime("%Y-%m")

            body = match.group("body")
            amounts = AMOUNT_RE.findall(body)
            debit = credit = 0.0
            if len(amounts) >= 2:
                debit = _normalize_amount(amounts[0])
                credit = _normalize_amount(amounts[1])
            elif len(amounts) == 1:
                amt = _normalize_amount(amounts[0])
                if _looks_like_credit(description):
                    credit = amt
                else:
                    debit = amt
            else:
                continue

            if credit:
                amount = credit
                entry_type = "Entrée"
            else:
                amount = debit
                entry_type = "Sortie"

            entries.append(
                {
                    "date": val_date,
                    "libelle": description,
                    "categorie": _guess_category(description, entry_type),
                    "montant": amount,
                    "type": entry_type,
                    "mois": op_month,
                    "source": "pdf",
                }
            )

    return entries


def _parse_sumup_bank_statement(reader: PdfReader) -> List[dict[str, Any]]:
    """Parser dédié aux relevés SumUp : découpe en blocs par date puis délègue à `_parse_sumup_block`."""

    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        for raw_line in text.splitlines():
            stripped = raw_line.strip()
            if stripped:
                lines.append(stripped)

    blocks: list[list[str]] = []
    current_block: list[str] = []
    for line in lines:
        if C9SUMUP_DATE_RE.match(line):
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        else:
            if current_block:
                current_block.append(line)
    if current_block:
        blocks.append(current_block)

    entries: list[dict[str, Any]] = []
    for block in blocks:
        entry = _parse_sumup_block(block)
        if entry:
            entries.append(entry)
    return entries


def _parse_sumup_block(block: list[str]) -> dict[str, Any] | None:
    """Transforme un bloc de lignes SumUp en entrée normalisée (date, description, montant, type)."""

    if not block:
        return None
    try:
        val_date = datetime.strptime(block[0], "%d/%m/%Y").date()
    except ValueError:
        return None
    idx = 1
    if idx < len(block) and C9SUMUP_TIME_RE.match(block[idx]):
        idx += 1

    description_lines: list[str] = []
    status_line = None
    while idx < len(block):
        line = block[idx]
        upper = line.upper()
        if any(upper.startswith(prefix) for prefix in SUMUP_STATUS_PREFIXES):
            status_line = line
            break
        description_lines.append(line)
        idx += 1

    if not status_line:
        return None

    parts = status_line.replace(",", ".").split()
    if len(parts) < 5:
        return None
    status = parts[0]
    try:
        debit = _safe_float(parts[1])
        credit = _safe_float(parts[2])
        fees = _safe_float(parts[3])
    except ValueError:
        return None

    entry_type = "Entrée" if credit > 0 else "Sortie"
    amount = credit if entry_type == "Entrée" else debit
    if amount <= 0:
        return None

    description = " ".join(description_lines).strip()
    if not description:
        description = status

    op_month = val_date.strftime("%Y-%m")
    return {
        "date": val_date,
        "libelle": description,
        "categorie": _guess_category(description, entry_type),
        "montant": amount,
        "type": entry_type,
        "mois": op_month,
        "source": "sumup_pdf",
    }


def list_sales_consumptions(tenant_id: int) -> list[Dict[str, Any]]:
    """Retourne les consommations restaurant converties en quantités Épicerie."""

    sql = text(
        """
        SELECT *
        FROM restaurant_sales_consumptions
        WHERE tenant_id = :tenant
        ORDER BY epicerie_nom NULLS LAST, last_sale_at DESC NULLS LAST
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    return df.to_dict("records")


def sync_ingredients_from_mappings(tenant_id: int = 2) -> int:
    mapping_sql = """
        SELECT
            rp.id AS plat_id,
            rp.nom AS plat_nom,
            rp.categorie AS plat_categorie,
            map.ratio,
            p.id AS produit_epicerie_id,
            p.nom AS epicerie_nom,
            p.categorie AS epicerie_categorie,
            COALESCE(p.prix_achat, 0) AS prix_achat
        FROM restaurant_epicerie_sku_map map
        JOIN restaurant_plats rp ON rp.id = map.produit_restaurant_id AND rp.tenant_id = map.tenant_restaurant
        LEFT JOIN produits p ON p.id = map.produit_epicerie_id AND p.tenant_id = map.tenant_epicerie
        WHERE map.tenant_restaurant = :tenant
        ORDER BY rp.nom;
    """

    def guess_unit(category: str | None) -> str:
        normalized = (category or '').lower()
        if any(keyword in normalized for keyword in ('champagne', 'whisky', 'spiritueux', 'alcool', 'bouteille')):
            return 'bouteille'
        if any(keyword in normalized for keyword in ('bière', 'biere')):
            return 'bouteille'
        if any(keyword in normalized for keyword in ('softs', 'jus', 'boissons')):
            return 'bouteille'
        return 'unit'

    mappings = query_df(text(mapping_sql), {"tenant": tenant_id}).to_dict("records")
    inserted = 0
    for mapping in mappings:
        ingredient_name = mapping.get("epicerie_nom") or f"{mapping['plat_nom']} ingredient"
        unit = guess_unit(mapping.get("epicerie_categorie"))
        cost = float(mapping.get("prix_achat") or 0)
        existing = query_df(
            text(
                """
                SELECT id
                FROM restaurant_ingredients
                WHERE tenant_id = :tenant
                  AND LOWER(nom) = LOWER(:name)
                LIMIT 1;
                """
            ),
            {"tenant": tenant_id, "name": ingredient_name},
        )
        if not existing.empty:
            ingredient_id = int(existing.iloc[0]["id"])
        else:
            ingredient_id = exec_sql_return_id(
                text(
                    """
                    INSERT INTO restaurant_ingredients (tenant_id, nom, unite_base, cout_unitaire, stock_actuel)
                    VALUES (:tenant, :name, :unit, :cost, 0)
                    RETURNING id;
                    """
                ),
                {"tenant": tenant_id, "name": ingredient_name, "unit": unit, "cost": cost},
            )

        exec_sql(
            text(
                """
                INSERT INTO restaurant_plat_ingredients (tenant_id, plat_id, ingredient_id, quantite, unite)
                VALUES (:tenant, :plat_id, :ingredient_id, :quantite, :unit)
                ON CONFLICT (plat_id, ingredient_id)
                DO UPDATE SET quantite = EXCLUDED.quantite, unite = EXCLUDED.unite;
                """
            ),
            {
                "tenant": tenant_id,
                "plat_id": mapping["plat_id"],
                "ingredient_id": ingredient_id,
                "quantite": float(mapping.get("ratio") or 1),
                "unit": unit,
            },
        )
        inserted += 1
    return inserted


def list_combined_price_history(tenant_id: int) -> list[Dict[str, Any]]:
    """Retourne l'historique de prix restaurant avec les coûts Epicerie liés."""

    sql = text(
        """
        SELECT
            ph.plat_id,
            rp.nom AS plat_nom,
            ph.prix_vente_ttc,
            ph.changed_at AS plat_changed_at,
            p.id AS epicerie_id,
            p.nom AS epicerie_nom,
            eph.prix_achat,
            eph.changed_at AS epicerie_changed_at
        FROM restaurant_plat_price_history ph
        JOIN restaurant_plats rp ON rp.id = ph.plat_id AND rp.tenant_id = :tenant
        LEFT JOIN restaurant_epicerie_sku_map map
            ON map.produit_restaurant_id = ph.plat_id
            AND map.tenant_restaurant = rp.tenant_id
        LEFT JOIN produits p ON p.id = map.produit_epicerie_id AND p.tenant_id = map.tenant_epicerie
        LEFT JOIN LATERAL (
            SELECT prix_achat, changed_at
            FROM produits_price_history eph
            WHERE eph.produit_id = p.id
              AND eph.changed_at <= ph.changed_at
            ORDER BY eph.changed_at DESC
            LIMIT 1
        ) eph ON TRUE
        ORDER BY ph.changed_at DESC
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    return df.to_dict("records")


def list_plat_epicerie_links(tenant_id: int) -> list[Dict[str, Any]]:
    sql = text(
        """
        SELECT
            rp.id AS plat_id,
            rp.nom AS plat_nom,
            rp.categorie AS plat_categorie,
            map.produit_epicerie_id,
            p.nom AS epicerie_nom,
            p.categorie AS epicerie_categorie,
            p.prix_achat,
            p.prix_vente,
            map.ratio
        FROM restaurant_plats rp
        LEFT JOIN restaurant_epicerie_sku_map map
            ON map.produit_restaurant_id = rp.id
            AND map.tenant_restaurant = rp.tenant_id
        LEFT JOIN produits p
            ON p.id = map.produit_epicerie_id
            AND p.tenant_id = map.tenant_epicerie
        WHERE rp.tenant_id = :tenant
        ORDER BY rp.categorie NULLS LAST, rp.nom
        """
    )
    df = query_df(sql, {"tenant": tenant_id})
    if df.empty:
        return []
    return df.to_dict("records")
